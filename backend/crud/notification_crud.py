from sqlalchemy import text
from sqlalchemy.engine import Connection

"""
保護者への成績表一括送信に関するデータベース操作を担当するCRUDモジュール。
"""

def get_notification_target(conn: Connection, student_id: int, exam_date: str):
    row = conn.execute(text("""
        SELECT s.名前, s.苗字, t.s3_file_url, t.id as score_id
        FROM 学生 s
        JOIN 成績表 t ON s.id = t.学生_id
        WHERE s.id = :student_id AND t.実施日 = :exam_date
    """), {"student_id": student_id, "exam_date": exam_date}).fetchone()
    return dict(row._mapping) if row else None

def update_status_to_sent(conn: Connection, score_id: int):
    conn.execute(text("""
        UPDATE 成績表 SET 確認ステータス = '送信済' WHERE id = :score_id
    """), {"score_id": score_id})

"""
ダッシュボードの通知（アラート）表示に必要な成績表ステータスを集計するCRUDです。
"""

def get_recent_exam_status_summary(conn: Connection, class_id: int):
    query = text("""
        SELECT 実施日, 確認ステータス, COUNT(成績表.id) as student_count
        FROM 成績表
        JOIN 学生 ON 成績表.学生_id = 学生.id
        WHERE 学生.クラス_id = :class_id AND 実施日 >= CURRENT_DATE - INTERVAL 20 DAY
        GROUP BY 実施日, 確認ステータス
        ORDER BY 実施日 DESC    
    """)
    return conn.execute(query, {"class_id": class_id}).fetchall()