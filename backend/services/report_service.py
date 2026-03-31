import datetime
from fastapi import HTTPException, status
from core.database import engine
import crud.report_crud as crud
from services.pdf_service import generate_and_upload_pdf

"""
成績表生成のコアとなるビジネスロジックを担当するサービス層。
CRUD(データベース)やPDF生成サービスをオーケストレーション(指揮)します。
"""

def generate_report_workflow(student_id: int, exam_date: str, comment: str, university: str, class_id: int) -> str:
    current_year = datetime.date.today().year
    jan_first = f"{current_year}-01-01"

    # トランザクションの開始
    with engine.begin() as conn:
        # 1. DBから学生情報を取得
        student_info = crud.get_student_info(conn, student_id, exam_date, class_id)
        if not student_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="成績データが見つかりません。")

        # 2. 今回の成績と推移データを取得
        current_scores = crud.get_current_scores(conn, student_info["score_id"])
        trend_raw = crud.get_trend_scores(conn, student_id, jan_first)

        # 3. グラフ用のデータ加工（ビジネスロジック）
        trend_dict = {}
        for tr in trend_raw:
            month_str = f"{tr.実施日.month}月"
            if tr.実施日 == datetime.date.fromisoformat(exam_date):
                month_str += "(今回)"
            if month_str not in trend_dict:
                trend_dict[month_str] = {"month": month_str}
            trend_dict[month_str][tr.科目名] = tr.点数
        trend_data = list(trend_dict.values())

        # 4. PDF生成とMinIOアップロード (外部サービスの呼び出し)
        file_urls = generate_and_upload_pdf(
            class_id=class_id,
            exam_date=exam_date,
            student_info=student_info,
            current_scores=current_scores,
            trend_data=trend_data,
            comment=comment,
            university=university
        )

        # 5. DBのステータスとURLを更新
        crud.update_report_file_url(conn, student_info["score_id"], file_urls['db_url'])

    # フロントエンドに渡すPresigned URLを返す
    return file_urls['presigned_url']