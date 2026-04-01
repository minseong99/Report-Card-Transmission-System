from sqlalchemy import text
from sqlalchemy.engine import Connection

"""
成績表草案（プレビュー）画面に必要なデータを取得するCRUDモジュール。
ビジネスロジックを含めず、純粋なDBからのデータ抽出に専念します。
"""

def get_latest_exam_date(conn: Connection, class_id: int):
    row = conn.execute(text("""
        SELECT DISTINCT 実施日 FROM 成績表
        JOIN 学生 ON 成績表.学生_id = 学生.id
        WHERE 学生.クラス_id = :class_id
            AND 実施日 >= CURRENT_DATE - INTERVAL 25 DAY
        ORDER BY 実施日 DESC LIMIT 1
    """), {"class_id": class_id}).fetchone()
    return row.実施日 if row else None

def get_class_students_with_scores(conn: Connection, class_id: int, latest_date: str):
    return conn.execute(text("""
        SELECT s.id, s.苗字, s.名前, t.統合順位, t.クラス順位, t.id as score_id, t.確認ステータス, t.s3_file_url
        FROM 学生 s
        JOIN 成績表 t ON s.id = t.学生_id
        WHERE s.クラス_id = :class_id AND t.実施日 = :latest_date
    """), {"class_id": class_id, "latest_date": latest_date}).fetchall()

def get_student_current_scores(conn: Connection, score_id: int):
    return conn.execute(text("""
        SELECT m.科目名, d.点数, d.偏差値, d.順位 as overall_rank
        FROM 成績詳細 d
        JOIN 科目 m ON d.科目_id = m.id
        WHERE d.成績表_id = :score_id                                 
    """), {"score_id": score_id}).fetchall()

def get_student_trend_scores(conn: Connection, student_id: int, start_date: str):
    return conn.execute(text("""
        SELECT t.実施日, m.科目名, d.点数
        FROM 成績表 t
        JOIN 成績詳細 d ON t.id = d.成績表_id
        JOIN 科目 m ON d.科目_id = m.id
        WHERE t.学生_id = :student_id AND t.実施日 >= :start_date
        ORDER BY t.実施日 ASC
    """), {"student_id": student_id, "start_date": start_date}).fetchall()