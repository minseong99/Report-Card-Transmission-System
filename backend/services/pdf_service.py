import io
import boto3
import os 
import matplotlib
matplotlib.use('AGG') # sever backgroundでUIなしにグラフを作れる設定
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

access_key_id = os.environ('MINIO_ROOT_USER')
secret_access_key = os.environ('MINIO_ROOT_PASSWORD')

# MinIo client 
s3_client = boto3.client(
    's3',
    endpoint_url='http://minio:9000', 
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name='us-east-1'
)
BUCKET_NAME="report-cards"

def generate_and_upload_pdf(class_id: int, exam_date:str, student_info: dict, 
                            current_scores:list, trend_data: list, comment: str, university: str) -> str:
    """
    データを受け取り、グラフ付きの成績表PDFをメモリ上で生成して
    MinIOにアップロードする
    """
    student_id = student_info["id"]
    student_name = f"{student_info['苗字']} {student_info['名前']}"
    file_name = f"{exam_date}_{student_id}_{student_info['名前']}_成績表.pdf"

    # ====================================
    # 1. Matplotlibで「成績表推移グラフ」を作って、画像メモリとして保存
    # ====================================
    plt.figure(figsize=(6, 3))

    # trend_data {{"month": "2月", "国語": 80, "数学":75 ...}...}
    months = [d["month"] for d in trend_data]
    
    if trend_data:
        subjects = [k for k in trend_data[-1].keys() if k != "month"]
        for sub in subjects:
            scores = [d.get(sub, None) for d in trend_data]
            plt.plot(months, scores, maker='o', label=sub)
    plt.ylim(0, 100)
    plt.title("Score Trend")
    plt.legend(loc='lower right', fontsize='small')
    plt.grid(True, linestyle='--', alpha=0.6)

    # graph(png) -> memory
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)
    plt.close()


    # ====================================
    # 2. Matplotlibで「成績表推移グラフ」を作って、画像メモリとして保存
    # ====================================
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # ※実務注意: 日本語を表示するにはIPAフォントなどのTTFファイルを登録する必要があります。
    # 例: pdfmetrics.registerFont(TTFont('IPAexGothic', 'ipaexg.ttf'))
    # ここでは便宜上、標準フォントを使用します。(日本語は文字化けする可能性があります)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Official Score Report")

    # 基本情報と順位
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 80, f"Name: {student_name}   |    Date: {exam_date}")
    c.drawString(50, height - 100, f"Overall Rank: {student_info['統合順位']}   |   Class Rank: {student_info['クラス順位']}")

    # 今回の成績詳細
    c.drawString(50, height - 140, "[ Current Exam Scores ]")
    y_pos = height - 160
    c.drawString(50, y_pos, "Subject | Score | Hensachi | Overall Rank")
    c.line(50, y_pos - 5, 400, y_pos - 5)
    y_pos -= 20
    for score in current_scores:
        c.drawString(50, y_pos, f"{score['subject']} | {score['score']} | {score['hensachi']} | {score['overall_rank']}")
        y_pos -= 20
    
    # graph -> pdf
    c.drawString(50, y_pos - 20, "[ Score Trend Graph ]")
    c.drawImage(ImageReader(img_buffer), 50, y_pos - 220, width=400, height=180)

    # 推薦大学とコメント
    text_y = y_pos - 250
    c.drawString(50, text_y, "[ University Recommendation ]")
    text_y -= 20
    for line in university.split('\n'):
        c.drawString(50, text_y, line)
        text_y -= 15
    
    text_y -= 15
    c.drawString(50, text_y, "[ Teacher's Comment ]")
    text_y -= 20
    for line in comment.split('\n'):
        c.drawString(50, text_y, line)
        text_y -= 15
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

    return f"http://localhost:9000/{BUCKET_NAME}/{s3_key}"