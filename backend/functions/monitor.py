import os 
import httpx 
from sqlalchemy import create_engine, text 

DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL)

def check_new_scores():
    triggered_bathces = []

    with engine.begin() as conn:
        # 新規データの検知
        # 未確認かつコメントが空の成績データ、クラスごとに集計
        query = text("""
            SELECT 学生.クラス_id, 成績表.実施日, COUNT(DISTINCT 成績表.id) as record_count
            FROM 成績表
            JOIN 学生 ON 成績表.学生_id = 学生.id
            JOIN 成績詳細 ON 成績詳細.成績表_id = 成績表.id
            WHERE 成績表.確認ステータス = '未確認' AND 成績表.コメント IS NULL
            GROUP BY 学生.クラス_id, 成績表.実施日
            HAVING record_count > 0                          
        """)
        new_batches = conn.execute(query).fetchall()

        for row in new_batches:
            class_id = row.クラス_id
            exam_date = row.実施日
            
            # ロック処理（二重検知防ぐため、ステータスを「生成中」に変更）
            conn.execute(text("""
                UPDATE 成績表
                JOIN 学生 ON 成績表.学生_id = 学生.id
                SET 成績表.確認ステータス = '生成中'
                WHERE 学生.クラス_id = :class_id
                AND 成績表.実施日 = :exam_date
                AND 成績表.確認ステータス = '未確認'
            """), {"class_id":class_id, "exam_date": exam_date})

            triggered_bathces.append({
                "class_id": class_id,
                "exam_date": str(exam_date),
                "count": row.record_count
            })
            
    return triggered_bathces
