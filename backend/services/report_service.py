import datetime
from fastapi import HTTPException, status
from core.database import engine
import crud.report_crud as crud
from services.pdf_service import generate_and_upload_pdf
from core.event_manager import event_manager

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

def proccess_bulk_report_generation(class_id: int, exam_date: str):
    """
    バックグラウンドでクラス全員分の成績表を自動生成するタスク。
    """
    print(f"\n[クラス: {class_id}] {exam_date}実施の成績表一括生成を開始します。。。", flush=True)

    with engine.begin() as conn:
        student_ids = crud.get_pendding_students_for_class(conn, class_id, exam_date)

    success_count = 0
    for sid in student_ids:
        try:
            generate_report_workflow(
                student_id=sid,
                exam_date=exam_date,
                comment="【システム自動生成】\n各科目において安定した成績を収めています。引き続き現在の学習ペースを維持し、弱点の克服に努めましょう。",
                university="システムによる自動判定のため省略",
                class_id=class_id
            )
            success_count += 1
        except Exception as e:
            print(f"生徒ID{sid} の生成に失敗: {e}",flush=True)
    
    # 全ての生成プロセスが終了した瞬間に、フロントエンドへ「更新せよ」と信号を送ります
    # 同期関数のため sync_broadcastを使用する
    event_manager.sync_broadcast(class_id, "REFRESH_DRAFTS")
    print(f"{success_count}名分の成績表一括生成が完了しました。",flush=True)