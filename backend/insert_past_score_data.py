import argparse
import datetime
import random
from sqlalchemy import text
from database import engine

def insert_past_exam(month: int):
    year = datetime.date.today().year
    exam_date = datetime.date(year, month, 15)

    with engine.begin() as conn:
        existing = conn.execute(text("SELECT id FROM 成績表 WHERE 実施日 = :exam_date LIMIT 1"), {"exam_date": exam_date}).fetchone()
        if existing:
            print(f"⚠️ すでに {exam_date} のデータが存在します。削除してから再実行するか、別の月を指定してください。")
            return

        mandatory_subjects = conn.execute(text("""
            SELECT id FROM 科目 WHERE 科目名 IN ('国語', '英語', '数学', '歴史')
        """)).fetchall()
        mandatory_ids = [row.id for row in mandatory_subjects]

        students = conn.execute(text("SELECT id, クラス_id, 選択科目1_id, 選択科目2_id FROM 学生")).fetchall()
        student_count = len(students)

        print(f"[{exam_date}] {student_count}名分の過去成績データを生成しています...")

        for student in students:

            result = conn.execute(text("""
                INSERT INTO 成績表 (学生_id, 受験者数, 実施日, 確認ステータス, 統合順位, クラス順位) 
                VALUES (:student_id, :total_students, :exam_date, '完了', :rand_rank, :rand_rank)
            """), {
                "student_id": student.id, 
                "total_students": student_count,
                "exam_date": exam_date,
                "rand_rank": random.randint(1, student_count) # 과거 등수는 대충 랜덤으로
            })
            score_id = result.lastrowid

            student_sub_ids = mandatory_ids + [student.選択科目1_id, student.選択科目2_id]
            
            for sub_id in student_sub_ids:
                score = random.randint(50, 100)
                hensachi = round(random.uniform(45.0, 75.0), 1)
                
                conn.execute(text("""
                    INSERT INTO 成績詳細 (点数, 偏差値, 順位, 科目_id, 成績表_id)
                    VALUES (:score, :hensachi, :rank, :sub_id, :score_id)
                """), {
                    "score": score, 
                    "hensachi": hensachi,
                    "rank": random.randint(1, student_count), 
                    "sub_id": sub_id, 
                    "score_id": score_id
                })

    print(f"{month}月 ({exam_date}) の過去データ作成が完了しました！グラフを確認してください。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="過去の模擬試験データを生成します。")
    parser.add_argument("month", type=int, help="生成する月 (例: 2)")
    args = parser.parse_args()
    
    if 1 <= args.month <= 12:
        insert_past_exam(args.month)
    else:
        print("月は 1 から 12 の間で指定してください。")