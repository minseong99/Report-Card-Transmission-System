# create dummy data 

from sqlalchemy import create_engine, text
from faker import Faker
import random
import os

# DB接続設定
DB_URL = os.environ.get("DATABASE_URL")  # docker-compose.ymlから環境変数を読み込む
engine = create_engine(DB_URL)
fake = Faker('ja_JP') # 日本語のダミーデータ生成

def seed_data():
    with engine.begin() as conn:
        # ==================================================
        #データベース初期化(INCREMENT問題解決)
        # ==================================================
        print("既存のデータを初期化しています。。。")

        # 外部キー制約を無効化
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))

        #テーブルを空にして、IDを 1に初期化
        tables_to_truncate = [
            "学生", "講師", "保護者", "クラス"
        ]
        for table in tables_to_truncate:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table};"))
                print(f" -> {table} テーブルをリセットしました。")
            except Exception as e:
                print(f" -> {table} テーブルはスキップ")

        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        print("初期化完了しました。")      

        # ==================================================
        # ダミーデータ生成
        # ==================================================

        print("ダミーデータの生成を開始します。。。")

        # クラスデータ生成（２０クラス）
        for i in range (1, 21):
            conn.execute(text(f"INSERT INTO クラス (クラス名) VALUES ('理系クラス_{i}')"))
        print("20名クラス生成完了")

        # 講師データ生成（各クラスに一人）
        for i in range (1, 21):
            conn.execute(text("""
                INSERT INTO 講師 (苗字, 名前, ログイン_id, パスワード, 電話番号, メール, 生年月日, 担当クラス_id)
                VALUES (:last_name, :first_name, :login_id, '1234', :phone, :email, :birth, :class_id)              
            """), {
                "last_name": fake.last_name(), "first_name": fake.first_name(),
                "login_id": f"teacher_{i}", "phone":fake.phone_number(),
                "email": fake.unique.email(), "birth": fake.date_of_birth(minimum_age=24, maximum_age=50),
                "class_id": i
            })
        print("20名の講師データ生成完了")

        # 保護者と学生の生成(1000名)
        for i in range (1, 1000):
            # 保護者
            parent_id = conn.execute(text("""
                INSERT INTO 保護者 (苗字, 名前, 電話番号, メール, 生年月日)
                VALUES (:last_name, :first_name, :phone, :email, :birth)
            """), {
                "last_name": fake.last_name(), "first_name": fake.first_name(),
                "phone": fake.phone_number(), "email": fake.unique.email(),
                "birth": fake.date_of_birth(minimum_age=25, maximum_age=70)
            }).lastrowid

            # 学生
            class_id = random.randint(1, 20)
            conn.execute(text("""
                INSERT INTO 学生 (苗字, 名前, 電話番号, メール, 生年月日, クラス_id, 保護者_id)
                VALUES (:last_name, :first_name, :phone, :email, :birth, :class_id, :parent_id)
            """), {
                "last_name": fake.last_name(), "first_name": fake.first_name(),
                "phone": fake.phone_number(), "email": fake.unique.email(),
                "birth": fake.date_of_birth(minimum_age=19, maximum_age=23),
                "class_id": class_id, "parent_id": parent_id
            })
        print("1000名の保護者と学生データが生成されました")
        print("全てのダミーデータ生成が完了しました。")

if __name__ == "__main__":
    seed_data()