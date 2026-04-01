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

def update_subject_score(conn: Connection, score_id: int, subject_name: str, new_score: int):
    """特定の科目の点数を更新します"""
    conn.execute(text("""
        UPDATE 成績詳細 d
        JOIN 科目 m ON d.科目_id = m.id
        SET d.点数 = :new_score
        WHERE d.成績表_id = :score_id AND m.科目名 = :subject_name
    """), {"new_score": new_score, "score_id": score_id, "subject_name": subject_name})

def recaculate_all_ranks(conn: Connection, exam_date: str):
    """
    点数変更によるバタフライ効果(順位変動)を処理するため、
    Window関数(RANK() OVER)を使用して、全生徒の順位を一括で再計算します。
    """
    # 1. 科目別の順位を再計算して一括更新
    conn.execute(text("""
        WITH RankedSubjects AS (
            SELECT d.成績表_id, d.科目_id,
                      RANK() OVER(PARTITION BY d.科目_id ORDER BY d.点数 DESC) as new_rank
            FROM 成績詳細 d
            JOIN 成績表 t ON d.成績表_id = t.id
            WHERE t.実施日 = :exam_date
        )
        UPDATE 成績詳細 d 
        JOIN RankedSubjects r ON d.成績表_id = r.成績表_id AND d.科目_id = r.科目_id
        SET d.順位 = r.new_rank
    """), {"exam_date":exam_date})

    # 2. 統合順位とクラス順位を再計算して一括更新
    conn.execute(text("""
        WITH TotalScores AS (
            SELECT t.id as score_id, s.クラス_id, SUM(d.点数) as total_score
            FROM 成績表 t
            JOIN 学生 s ON t.学生_id = s.id
            JOIN 成績詳細 d ON t.id = d.成績表_id
            WHERE t.実施日 = :exam_date
            GROUP BY t.id, s.クラス_id              
        ),
        RankedTotals AS (
            SELECT score_id,
                      RANK() OVER(ORDER BY total_score DESC) as new_overall_rank,
                      RANK() OVER(PARTITION BY クラス_id ORDER BY total_score DESC) as new_class_rank
            FROM TotalScores
        )
        UPDATE 成績表 t
        JOIN RankedTotals r ON t.id = r.score_id
        SET t.統合順位 = r.new_overall_rank,
                t.クラス順位 = r.new_class_rank
        WHERE t.実施日 = :exam_date
    """), {"exam_date": exam_date})

def recalculate_hensachi(conn: Connection, exam_date: str):
    """
    点数更新に伴う、該当試験日の全生徒の「偏差値」を再計算して一括更新します。
    """
    conn.execute(text("""
        WITH SubjectStatus AS (
                SELECT
                      d.科目_id,
                      AVG(d.点数) as avg_score,
                      STDDEV(d.点数) as std_dev
                FROM 成績詳細 d
                JOIN 成績表 t ON d.成績表_id = t.id
                WHERE t.実施日 = :exam_date
                GROUP BY d.科目_id
        )
        UPDATE 成績詳細 d
        JOIN 成績表 t ON d.成績表_id = t.id
        JOIN SubjectStatus s ON d.科目_id = s.科目_id
        SET d.偏差値 = CASE
                    WHEN s.std_dev = 0 THEN 50.0  -- 全員が同じ点数の場合のエラー回避
                    ELSE ROUND (((d.点数 - s.avg_score) / s.std_dev) * 10 + 50, 1)
        END
        WHERE t.実施日 = :exam_date
    """), {"exam_date": exam_date})