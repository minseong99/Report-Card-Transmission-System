import time 
from core.database import engine 
import crud.notification_crud as crud

"""
保護者への通知（メール・SMSモック）と、DBのステータス更新をオーケストレーションするサービス層。
"""

def mock_send_email_and_sms(parent_name: str, student_name: str, exam_date: str, file_url: str):
    message = f"""
    =========================================
    {parent_name}様

    {exam_date}実施の模擬試験 ({student_name}様)の成績表結果が出ました。
    以下のURLより、PDFの成績通知書をご確認ください。

    成績表: {file_url}
    from 〇〇学習塾
    =========================================
    """
    print(message, flush=True) # ターミナルに即時出力

def process_batch_notifications(student_ids: list[int], exam_date: str):
    print(f"\n{len(student_ids)}名分の成績表一括送信プロセスを開始します...", flush=True)

    with engine.begin() as conn:
        for student_id in student_ids:
            # CRUDを使用してDBから送信に必要なデータを取得
            target_data = crud.get_notification_target(conn, student_id, exam_date)

            if target_data and target_data["s3_file_url"]:
                student_name = f"{target_data['苗字']} {target_data['名前']}"
                parent_name = f"{target_data['苗字']} 保護者" 
                
                # モック送信処理
                mock_send_email_and_sms(parent_name, student_name, exam_date, target_data["s3_file_url"])

                # CRUDを使用してステータスを更新
                crud.update_status_to_sent(conn, target_data["score_id"])

    print("一括送信プロセスがすべて完了しました！", flush=True)

def generate_class_alerts(class_id: int) -> list:
    """
    担当クラスの成績処理ステータスをDBから取得し、
    フロントエンドに表示する通知(アラート)メッセージのリストを生成します。
    """
    with engine.connect() as conn:
        records = crud.get_recent_exam_status_summary(conn, class_id)
        
        alerts = []
        exam_status_map = {}
        
        # 1. 実施日ごとにステータスと人数をグループ化
        for r in records:
            exam_date = str(r.実施日)
            if exam_date not in exam_status_map:
                exam_status_map[exam_date] = []
            exam_status_map[exam_date].append({
                "status": r.確認ステータス,
                "count": r.student_count
            })
        
        # 2. グループ化されたデータを解析し、アラートメッセージを構築
        for exam_date, statuses in exam_status_map.items():
            total_students = sum(s["count"] for s in statuses)
            processing_count = sum(s["count"] for s in statuses if s["status"] in ('未確認', '生成中'))
            done_count = sum(s["count"] for s in statuses if s["status"] == '完了')

            # まだ処理待ち（未確認・生成中）の学生がいる場合
            if processing_count > 0:
                alerts.append({
                    "id": f"{exam_date}-registered",
                    "message": f"[{exam_date}実施分]{class_id}組の{total_students}名成績データが登録されました。",
                    "type": "processing",
                    "date": exam_date
                })
            
            # 全員の成績表が完了している場合
            if done_count > 0 and done_count == total_students:
                alerts.append({
                    "id": f"{exam_date}-done",
                    "message": f"[{exam_date}実施分]{total_students}名の成績表生成が完了しました。",
                    "type": "success",
                    "date": exam_date
                })
            
        return alerts