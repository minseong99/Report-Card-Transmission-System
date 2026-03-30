import io
import boto3
import os 
import urllib.request
import matplotlib
matplotlib.use('Agg') # サーバーバックグラウンドでUIなしにグラフを描画する設定
import matplotlib.pyplot as plt
import japanize_matplotlib # グラフの日本語文字化け防止

from botocore.client import Config
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
# --- Paragraph関連のインポートを追加 ---
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
# ----------------------------------------

# ==========================================
# 日本語フォント(BIZ UDゴシック)の自動ダウンロードと登録
# ==========================================
FONT_FILE = "BIZUDGothic-Regular.ttf"
FONT_URL = "https://github.com/googlefonts/morisawa-biz-ud-gothic/raw/main/fonts/ttf/BIZUDGothic-Regular.ttf"

if not os.path.exists(FONT_FILE):
    print("日本語フォントをダウンロードしています...")
    try:
        urllib.request.urlretrieve(FONT_URL, FONT_FILE)
        print("フォントのダウンロードが完了しました！")
    except Exception as e:
        print(f"❌ ダウンロードに失敗しました: {e}")

# ReportLabに日本語フォントを登録
# (※登録名(エイリアス)は 'NotoSansJP' のままにしておきます)
pdfmetrics.registerFont(TTFont('NotoSansJP', FONT_FILE))

# --- 🌟 日本語対応のParagraphスタイルを定義 ---
styles = getSampleStyleSheet()
# 通常テキスト用
styles.add(ParagraphStyle(
    name='Japanese',
    fontName='NotoSansJP',
    fontSize=11,
    leading=15, # 行間
    splitLongWords=True, # 長い単語を分割するか
    # textColor=HexColor("#333333") # 必要に応じて色を変更
))
# ----------------------------------------------

# MinIOクライアント設定
access_key_id = os.getenv('MINIO_ROOT_USER', 'user')
secret_access_key = os.getenv('MINIO_ROOT_PASSWORD', 'pasword1234')

s3_client = boto3.client(
    's3',
    endpoint_url='http://minio:9000', 
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name='us-east-1',
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
)
s3_client_external = boto3.client( # 保護者用
    's3',
    endpoint_url='http://localhost:9000', 
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name='us-east-1',
    config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
)

BUCKET_NAME = "report-cards"

def generate_and_upload_pdf(class_id: int, exam_date: str, student_info: dict, 
                            current_scores: list, trend_data: list, comment: str, university: str) -> str:
    """
    データを受け取り、修能(スヌン)スタイルの公式成績表PDFを生成してMinIOにアップロードする
    """
    student_id = student_info["id"]
    student_name = f"{student_info['苗字']} {student_info['名前']}"
    file_name = f"{exam_date}_{student_id}_{student_info['名前']}_成績表.pdf"

    # ====================================
    # 1. Matplotlibで「成績推移グラフ」を描画
    # ====================================
    plt.figure(figsize=(7, 2.5)) 
    months = [d["month"] for d in trend_data]
    
    if trend_data:
        subjects = [k for k in trend_data[-1].keys() if k != "month"]
        for sub in subjects:
            scores = [d.get(sub, None) for d in trend_data]
            plt.plot(months, scores, marker='o', linewidth=2, label=sub)
            
    plt.ylim(0, 100)
    plt.legend(loc='lower right', fontsize='small', ncol=3) 
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300) 
    img_buffer.seek(0)
    plt.close()

    # ====================================
    # 2. ReportLabで「修能(スヌン)スタイル」のPDFを描画
    # ====================================
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4
    margin = 40

    # フォント設定ヘルパー関数
    def set_font(size):
        c.setFont('NotoSansJP', size)

    # --- ヘッダー領域 (タイトル) ---
    c.setLineWidth(2)
    c.setFillColor(HexColor("#f8fafc"))
    c.rect(margin, height - margin - 50, width - 2*margin, 50, fill=1, stroke=1) # 枠と塗りつぶしを同時に
    
    c.setFillColorRGB(0, 0, 0)
    set_font(22)
    c.drawCentredString(width / 2, height - margin - 35, "模擬試験 成績通知書")

    # --- 基本情報領域 (テーブル形式) ---
    info_y = height - 140
    c.setLineWidth(1)
    c.rect(margin, info_y, width - 2*margin, 30)
    c.line(margin + 100, info_y, margin + 100, info_y + 30)
    c.line(margin + 300, info_y, margin + 300, info_y + 30)
    
    set_font(11)
    c.drawString(margin + 15, info_y + 10, "受験番号 / 氏名")
    set_font(12)
    c.drawString(margin + 115, info_y + 10, f"{student_id}  /  {student_name}")
    
    set_font(11)
    c.drawString(margin + 315, info_y + 10, "実施日")
    set_font(12)
    c.drawString(margin + 380, info_y + 10, exam_date)

    # --- 成績詳細領域 (修能スタイルのグリッド) ---
    table_y = info_y - 30
    row_height = 25
    header_y = table_y - row_height
    
    # データ行数に基づいて全体の高さを計算
    num_rows = len(current_scores)
    
    # ヘッダー背景
    c.setFillColor(HexColor("#e2e8f0"))
    c.rect(margin, header_y, width - 2*margin, row_height, fill=1, stroke=0)
    c.setFillColorRGB(0, 0, 0)
    
    # 外枠
    c.setLineWidth(1.5)
    c.rect(margin, header_y - (num_rows * row_height), width - 2*margin, row_height * (num_rows + 1), stroke=1, fill=0)

    # カラムのX座標 (5等分)
    col_w = (width - 2*margin) / 5
    x_cols = [margin + col_w * i for i in range(6)]
    
    # 縦線を描画
    c.setLineWidth(0.5)
    for x in x_cols[1:5]:
        c.line(x, header_y + row_height, x, header_y - (num_rows * row_height))

    # ヘッダーテキスト
    set_font(11)
    headers = ["科目", "標準点数", "偏差値", "クラス順位", "全校順位"]
    for i, text in enumerate(headers):
        c.drawCentredString(x_cols[i] + col_w/2, header_y + 8, text)

    # データ行テキストと横線
    set_font(11)
    current_y = header_y
    for score in current_scores:
        current_y -= row_height
        c.line(margin, current_y + row_height, width - margin, current_y + row_height) # 横線
        c.drawCentredString(x_cols[0] + col_w/2, current_y + 8, score['subject'])
        c.drawCentredString(x_cols[1] + col_w/2, current_y + 8, str(score['score']))
        c.drawCentredString(x_cols[2] + col_w/2, current_y + 8, str(score['hensachi']))
        c.drawCentredString(x_cols[3] + col_w/2, current_y + 8, f"{student_info['クラス順位']} 位")
        c.drawCentredString(x_cols[4] + col_w/2, current_y + 8, f"{student_info['統合順位']} 位")

    # --- 成績推移グラフ領域 ---
    graph_h = 190
    graph_y = current_y - graph_h - 10 # 余白を少し追加
    c.setLineWidth(1)
    c.setFillColor(HexColor("#f8fafc"))
    c.rect(margin, graph_y + 170, width - 2*margin, 20, fill=1, stroke=1)
    
    c.rect(margin, graph_y, width - 2*margin, 170, fill=0, stroke=1) # グラフ部分の枠線

    c.setFillColorRGB(0, 0, 0)
    set_font(10)
    c.drawString(margin + 10, graph_y + 175, "■ 成績推移グラフ (今年度)")
    
    # グラフ画像を挿入
    c.drawImage(ImageReader(img_buffer), margin + 10, graph_y + 5, width=width - 2*margin - 20, height=160)

    # ==========================================
    # --- 🌟 Paragraphによるテキスト折り返し実装 ---
    # ==========================================
    
    # --- 推薦大学リスト ---
    # 改行コードをHTMLタグに変換
    uni_text = university.replace('\n', '<br/>')
    p_uni = Paragraph(uni_text, styles['Japanese'])
    # 描画可能な最大幅を指定して、テキストの高さを計算
    # 左右の余白10pxを考慮: width - 2*margin - 20
    aw, ah = p_uni.wrap(width - 2*margin - 20, height) # 高さは十分大きく設定

    # タイトル部分の描画
    title_h = 20
    c.setLineWidth(1)
    c.setFillColor(HexColor("#f8fafc"))
    c.rect(margin, graph_y - title_h - 10, width - 2*margin, title_h, fill=1, stroke=1)
    
    c.setFillColorRGB(0, 0, 0)
    set_font(10)
    c.drawString(margin + 10, graph_y - title_h - 5, "■ AI 推薦大学リスト")

    # テキスト部分の枠線（Paragraphの高さに合わせて動的に変更）
    text_box_y = graph_y - title_h - ah - 20 # 10pxの余白を追加
    c.rect(margin, text_box_y, width - 2*margin, ah + 10, fill=0, stroke=1)
    
    # Paragraphを描画
    p_uni.drawOn(c, margin + 10, text_box_y + 5)

    # --- 講師コメント ---
    # 改行コードをHTMLタグに変換
    comment_text = comment.replace('\n', '<br/>')
    p_comment = Paragraph(comment_text, styles['Japanese'])
    # テキストの高さを計算
    aw_c, ah_c = p_comment.wrap(width - 2*margin - 20, height)

    # タイトル部分の描画
    c.setFillColor(HexColor("#f8fafc"))
    c.rect(margin, text_box_y - title_h - 10, width - 2*margin, title_h, fill=1, stroke=1)
    
    c.setFillColorRGB(0, 0, 0)
    set_font(10)
    c.drawString(margin + 10, text_box_y - title_h - 5, "■ 担当講師からのコメント")

    # テキスト部分の枠線（Paragraphの高さに合わせて動的に変更）
    msg_box_y = text_box_y - title_h - ah_c - 20 # 10pxの余白を追加
    c.rect(margin, msg_box_y, width - 2*margin, ah_c + 10, fill=0, stroke=1)
    
    # Paragraphを描画
    p_comment.drawOn(c, margin + 10, msg_box_y + 5)
    
    # ==========================================

    # 保存してメモリの先頭に戻す
    c.showPage()
    c.save()
    pdf_buffer.seek(0)

    # ====================================
    # 3. MinIOにアップロード
    # ====================================
    s3_key = f"{class_id}/{file_name}"
    s3_client.upload_fileobj(
        pdf_buffer,
        BUCKET_NAME,
        s3_key,
        ExtraArgs={'ContentType' : 'application/pdf'}
    )

    db_url = f"http://localhost:9000/{BUCKET_NAME}/{s3_key}"
    presigned_url = s3_client_external.generate_presigned_url(
        'get_object',
        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
        ExpiresIn=604800
    )
    

    return {
        "db_url": db_url,
        "presigned_url": presigned_url
    }