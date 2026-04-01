import datetime
import boto3
from botocore.client import Config
from core.database import engine
from core.config import settings # 🌟 環境変数を中央管理から取得
import crud.draft_crud as crud

# ==========================================
# S3クライアント設定 (保護者用URL生成のため)
# 設定はすべて core/config.py から安全に読み込みます。
# ==========================================
s3_client_external = boto3.client(
    's3',
    endpoint_url=settings.MINIO_EXTERNAL_ENDPOINT,
    aws_access_key_id=settings.ACCESS_KEY_ID,
    aws_secret_access_key=settings.SECRET_ACCESS_KEY,
    region_name='us-east-1',
    config=Config(signature_version='s3v4', s3={'addressing_style': 'path'})
)
BUCKET_NAME = "report-cards"

def get_preview_data(class_id: int):
    """
    CRUDからデータを取得・加工し、プレビュー用のリストを構築するサービス。
    成績表が完成している場合はS3の署名付きURLを生成して返します。
    """
    current_year = datetime.date.today().year
    feb_first = f"{current_year}-01-01"
    result_data = []

    with engine.connect() as conn:
        # 1. 最新の試験日を取得
        latest_date = crud.get_latest_exam_date(conn, class_id)
        if not latest_date:
            return {"status": "success", "exam_date": None, "data": []}

        # 2. 学生一覧を取得
        students = crud.get_class_students_with_scores(conn, class_id, str(latest_date))

        # 3. 各学生のデータを加工
        for st in students:
            # a. 今回の成績集計
            current_scores_raw = crud.get_student_current_scores(conn, st.score_id)
            current_scores = []
            total_score = 0
            for cs in current_scores_raw:
                current_scores.append({
                    "subject": cs.科目名, "score": cs.点数, 
                    "hensachi": float(cs.偏差値), "overall_rank": cs.overall_rank
                })
                total_score += cs.点数
            
            # b. 推移データの加工
            trend_raw = crud.get_student_trend_scores(conn, st.id, feb_first)
            trend_dict = {}
            for tr in trend_raw:
                month_str = f"{tr.実施日.month}月"
                if tr.実施日 == latest_date:
                    month_str += "(今回)"
                if month_str not in trend_dict:
                    trend_dict[month_str] = {"month": month_str}
                trend_dict[month_str][tr.科目名] = tr.点数
            trend_data = list(trend_dict.values())

            # c. S3 Presigned URL生成
            file_url = None
            if st.確認ステータス == '完了' and st.s3_file_url:
                try:
                    s3_key = st.s3_file_url.split(f"{BUCKET_NAME}/")[-1]
                    file_url = s3_client_external.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
                        ExpiresIn=604800
                    )
                except Exception as e:
                    print(f"URL parsing error: {e}")
                    file_url = st.s3_file_url

            # 加工したデータを結果リストに追加
            result_data.append({
                "studentId": st.id,
                "studentName": f"{st.苗字} {st.名前}",
                "class_id": class_id,
                "overallRank": st.統合順位,
                "classRank": st.クラス順位,
                "totalScore": total_score,
                "currentScores": current_scores,
                "trendData": trend_data,
                "status": st.確認ステータス,
                "fileUrl": file_url
            })
        
        return {"status": "success", "exam_date": str(latest_date), "data": result_data}