import time 
from sqlalchemy import text
from database import engine 

def mock_send_email_and_sms(parent_name: str, student_name: str, exam_date: str, file_url: str):
    message = f"""
    =========================================

    {parent_name}様

    {exam_date}実施の模擬試験 ({student_name}様)の成績表結果が出ました。
    以下のURLにより、PDFの成績通知書をご確認ください。

    成績表: {file_url}

    from 〇〇学習塾
    =========================================
    """
    print(message)
    time.sleep(0.5)

def process_batch_notifications(student_ids: list[int], exam_date: str):
    """
    バックグラウンドで実行される一括送信サービス
    """
    print(f"{len(student_ids)}名分の成績表一括送信プロセスを開始します。。。")

    with engine.begin() as conn:
        for student_id in student_ids:
            row = conn.execute(text("""
                SELECT s.名前, s.苗字, t.s3_file_url, t.id as score_id
                FROM 学生 s
                JOIN 成績表 t ON s.id = t.学生_id
                WHERE s.id = :student_id AND t.実施日 = :exam_date
            """), {"student_id": student_id, "exam_date": exam_date}).fetchone()

            if row and row.s3_file_url:
                student_name = f"{row.苗字} {row.名前}"
                parent_name = f"{row.苗字} 保護者" 
                
                mock_send_email_and_sms(parent_name, student_name, exam_date, row.s3_file_url)

                conn.execute(text("""
                    UPDATE 成績表 SET 確認ステータス = '送信済' WHERE id = :score_id
                """), {"score_id": row.score_id})

    print("一括送信プロセスがすべて完了しました！")