from sqlalchemy import text
from sqlalchemy.engine import Connection

"""
データベース(DB)との直接的なやり取り(SQLクエリの実行)のみを担当するCRUDモジュール。
ビジネスロジックはここには含めず、純粋なデータの取得・更新に専念します。
"""

def get_student_info(conn: Connection, student_id: int, exam_date: str, class_id: int):
    row = conn.execute(text("""
        SELECT s.id, s.苗字, s.名前, t.統合順位, t.クラス順位, t.id as score_id
        FROM 学生 s
        JOIN 成績表 t ON s.id = t.学生_id
        WHERE s.id = :student_id AND t.実施日 = :exam_date AND s.クラス_id = :class_id
    """), {"student_id": student_id, "exam_date": exam_date, "class_id": class_id}).fetchone()
    return dict(row._mapping) if row else None

def get_current_scores(conn: Connection, score_id: int):
    rows = conn.execute(text("""
        SELECT m.科目名, d.点数, d.偏差値, d.順位 as overall_rank
        FROM 成績詳細 d 
        JOIN 科目 m ON d.科目_id = m.id
        WHERE d.成績表_id = :score_id
    """), {"score_id": score_id}).fetchall()
    return [{"subject": r.科目名, "score": r.点数, "hensachi": float(r.偏差値), "overall_rank": r.overall_rank} for r in rows]

def get_trend_scores(conn: Connection, student_id: int, jan_first: str):
    return conn.execute(text("""
        SELECT t.実施日, m.科目名, d.点数
        FROM 成績表 t
        JOIN 成績詳細 d ON t.id = d.成績表_id
        JOIN 科目 m ON d.科目_id = m.id
        WHERE t.学生_id = :student_id AND t.実施日 >= :jan_first
        ORDER BY t.実施日 ASC
    """), {"student_id": student_id, "jan_first": jan_first}).fetchall()

def update_report_file_url(conn: Connection, score_id: int, file_url: str):
    conn.execute(text("""
        UPDATE 成績表
        SET 確認ステータス = '完了', s3_file_url = :file_url
        WHERE id = :score_id
    """), {"file_url": file_url, "score_id": score_id})