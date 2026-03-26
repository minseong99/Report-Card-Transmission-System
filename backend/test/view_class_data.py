import os
import sys
from sqlalchemy import create_engine, text

# DB接続設定
DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL)

def get_class_full_data(class_id: int):
    """
    指定されたクラスIDに所属する学生の全データ
    （基本情報、保護者情報、最新の成績情報、科目別の詳細成績、クラス・全校順位）を取得して表示する関数
    """
    with engine.connect() as conn:
        # 1. クラス名の取得（存在確認も兼ねる）
        class_info = conn.execute(text("SELECT クラス名 FROM クラス WHERE id = :cid"),
                                   {"cid": class_id}).fetchone()
        if not class_info:
            print(f"エラー: クラスID {class_id} は存在しません。")
            return

        class_name = class_info.クラス名
        print(f"\n==================================================")
        print(f" 【{class_name}】 (クラスID: {class_id}) 総合データレポート ")
        print(f"==================================================")

        # 2. 5つのテーブルをJOINして、全データを一括取得する強力なクエリ
        # 追加: 成績表の「統合順位」と「クラス順位」をSELECTに追加！
        query = text("""
            SELECT 
                学生.id AS 学生_id, 
                学生.苗字 AS 学生_苗字, 学生.名前 AS 学生_名前, 学生.電話番号 AS 学生_電話番号,
                保護者.苗字 AS 保護者_苗字, 保護者.名前 AS 保護者_名前, 保護者.電話番号 AS 保護者_電話番号, 保護者.メール AS 保護者_メール,
                成績表.実施日, 成績表.確認ステータス, 成績表.統合順位, 成績表.クラス順位,
                科目.科目名, 成績詳細.点数, 成績詳細.偏差値, 成績詳細.順位
            FROM 学生
            JOIN 保護者 ON 学生.保護者_id = 保護者.id
            LEFT JOIN 成績表 ON 学生.id = 成績表.学生_id
            LEFT JOIN 成績詳細 ON 成績表.id = 成績詳細.成績表_id
            LEFT JOIN 科目 ON 成績詳細.科目_id = 科目.id
            WHERE 学生.クラス_id = :class_id
            ORDER BY 学生.id, 科目.id
        """)
        
        results = conn.execute(query, {"class_id": class_id}).fetchall()

        if not results:
            print("このクラスにはまだ学生が登録されていません。")
            return

        # 3. 取得したデータを学生ごとに整理（グルーピング）するロジック
        students_data = {}
        for row in results:
            s_id = row.学生_id
            
            # 初めて登場する学生なら、基本情報を辞書に登録
            if s_id not in students_data:
                students_data[s_id] = {
                    "student_name": f"{row.学生_苗字} {row.学生_名前}",
                    "student_phone": row.学生_電話番号,
                    "parent_name": f"{row.保護者_苗字} {row.保護者_名前}",
                    "parent_phone": row.保護者_電話番号,
                    "parent_mail": row.保護者_メール,
                    "exam_date": row.実施日,
                    "status": row.確認ステータス,
                    "overall_rank": row.統合順位, 
                    "class_rank": row.クラス順位,   
                    "scores": []
                }
            
            # 科目の成績データがあればリストに追加
            if row.科目名 is not None:
                students_data[s_id]["scores"].append(
                    f"{row.科目名}: {row.点数}点 (偏差値: {row.偏差値}, {row.科目名}順位: {row.順位}位)"
                )

        # 4. ターミナルに美しく出力
        for s_id, data in students_data.items():
            print(f"\n学生ID: {s_id} | {data['student_name']} (TEL: {data['student_phone']})")
            print(f"   保護者: {data['parent_name']} (TEL: {data['parent_phone']}, メール: {data['parent_mail']})")
            
            if data['exam_date']:
                print(f"   最新試験日: {data['exam_date']} | ステータス: [{data['status']}]")
                
                # 🌟 追加: 総合順位・クラス順位の表示（まだ計算されていなければハイフン表示）
                overall = data['overall_rank'] if data['overall_rank'] else '-'
                class_rk = data['class_rank'] if data['class_rank'] else '-'
                print(f"   総合評価: 全校 {overall}位 / クラス {class_rk}位")
                
                print("   【成績詳細】:")
                for score in data['scores']:
                    print(f"      - {score}")
            else:
                print("   まだ成績データが登録されていません。")

if __name__ == "__main__":
    # コマンドライン引数からクラスIDを受け取る（デフォルトはクラスID: 1）
    target_class = 1
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        target_class = int(sys.argv[1])
        
    get_class_full_data(target_class)