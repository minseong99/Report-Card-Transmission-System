import datetime
import boto3
import os
from sqlalchemy import text
from botocore.client import Config
from database import engine

# ==========================================
# S3クライアント設定 (保護者用URL生成のため)
# ==========================================
access_key_id = os.getenv('MINIO_ROOT_USER', 'user')
secret_access_key = os.getenv('MINIO_ROOT_PASSWORD', 'pasword1234')

s3_client_external = boto3.client(
    's3',
    endpoint_url=os.getenv('MINIO_EXTERNAL_ENDPOINT', 'http://localhost:9000'),
    aws_access_key_id=access_key_id,
    aws_secret_access_key=secret_access_key,
    region_name='us-east-1',
    config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
)
BUCKET_NAME = "report-cards"

def get_preview_data(class_id: int):
    """
    DBからプレビュー用のデータを取得し、
    成績表が完成している場合はS3の署名付きURLを生成して返すサービス関数
    """
    current_year = datetime.date.today().year
    feb_first = f"{current_year}-01-01"

    with engine.connect() as conn:
        # 1. 最近25日以内の「最近の試験日」を特定
        exam_record = conn.execute(text("""
            SELECT DISTINCT 実施日 FROM 成績表
            JOIN 学生 ON 成績表.学生_id = 学生.id
            WHERE 学生.クラス_id = :class_id
                AND 実施日 >= CURRENT_DATE - INTERVAL 25 DAY
            ORDER BY 実施日 DESC LIMIT 1
        """), {"class_id": class_id}).fetchone()

        if not exam_record:
            return {"status": "success", "exam_date": None, "data": []}
        
        latest_date = exam_record.実施日

        # 2. 試験を受けた「担当クラスの学生一覧」を取得 
        students = conn.execute(text("""
            SELECT s.id, s.苗字, s.名前, t.統合順位, t.クラス順位, t.id as score_id, t.確認ステータス, t.s3_file_url
            FROM 学生 s
            JOIN 成績表 t ON s.id = t.学生_id
            WHERE s.クラス_id = :class_id AND t.実施日 = :latest_date
        """), {"class_id": class_id, "latest_date": latest_date}).fetchall()

        result_data = []

        # 3. 各学生の「今回の成績詳細」と「１月からの推移」を組み立てる
        for st in students:
            student_id = st.id 
            student_name = f"{st.苗字} {st.名前}"

            # a. 今回の成績詳細
            current_scores_rw = conn.execute(text("""
                SELECT m.科目名, d.点数, d.偏差値, d.順位 as overall_rank
                FROM 成績詳細 d
                JOIN 科目 m ON d.科目_id = m.id
                WHERE d.成績表_id = :score_id                                 
            """), {"score_id": st.score_id}).fetchall()

            current_scores = []
            total_score = 0
            for cs in current_scores_rw:
                current_scores.append({
                    "subject": cs.科目名,
                    "score": cs.点数,
                    "hensachi": float(cs.偏差値),
                    "overall_rank" : cs.overall_rank
                })
                total_score += cs.点数
            
            # b. １月以降の全成績推移を取得
            trend_raw = conn.execute(text("""
                SELECT t.実施日, m.科目名, d.点数
                FROM 成績表 t
                JOIN 成績詳細 d ON t.id = d.成績表_id
                JOIN 科目 m ON d.科目_id = m.id
                WHERE t.学生_id = :student_id AND t.実施日 >= :feb_first
                ORDER BY t.実施日 ASC
            """), {"student_id": student_id, "feb_first": feb_first}).fetchall()

            trend_dict = {}
            for tr in trend_raw:
                month_str = f"{tr.実施日.month}月"
                if tr.実施日 == latest_date:
                    month_str += "(今回)"
                if month_str not in trend_dict:
                    trend_dict[month_str] = {"month": month_str}
                trend_dict[month_str][tr.科目名] = tr.点数
            trend_data = list(trend_dict.values())

            # ==========================================
            # 4. URL変換ロジック (完了ステータスの場合のみ)
            # ==========================================
            file_url = None
            if st.確認ステータス == '完了' and st.s3_file_url:
                try:
                    # DBの短いURLからKey部分を抽出して、7日間の有効なURLを発行
                    s3_key = st.s3_file_url.split(f"{BUCKET_NAME}/")[-1]
                    file_url = s3_client_external.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                        ExpiresIn=604800
                    )
                except Exception as e:
                    print(f"URL parsing error: {e}")
                    file_url = st.s3_file_url # 失敗時は元のURLを入れておく

            # 5. 最終データをリストに追加
            result_data.append({
                "studentId" : student_id,
                "studentName": student_name,
                "class_id": class_id,
                "overallRank": st.統合順位,
                "classRank": st.クラス順位,
                "totalScore": total_score,
                "currentScores": current_scores,
                "trendData": trend_data,
                "status": st.確認ステータス,
                "fileUrl": file_url # 🌟 生成したURLを追加
            })
        
        return {"status": "success", "exam_date": str(latest_date), "data": result_data}