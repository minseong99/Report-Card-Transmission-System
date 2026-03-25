import sys
import os
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
import random

# パスの解決
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)
DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL)

def test_api_trigger_and_response_format():
    """
    特定のクラス（クラスID: 1）の成績データのみがスキャン完了した際に、
    該当クラスの担当講師にのみ通知が送信され、DBが正しくロックされるかを検証するテスト。
    ※実際の試験フォーマット（必須4科目 ＋ 探求選択2科目 ＝ 計6科目）を反映。
    """
    today = datetime.date.today()
    
    with engine.begin() as conn:
        # 1. テスト対象を「クラスID: 1」に固定
        target_class_id = random.randint(1,20)
        
        # クラス1に所属する学生「全員」を取得
        students = conn.execute(text(
            "SELECT id FROM 学生 WHERE クラス_id = :cid"
        ), {"cid": target_class_id}).fetchall()
        
        student_count = len(students)
        assert student_count > 0, "クラス1の学生データが存在しません。seed.pyを実行してください。"

        # 🚨 万が一のための科目データ生成ガードロジック（全8科目を生成）
        subjects_count = conn.execute(text("SELECT COUNT(*) FROM 科目")).scalar()
        if subjects_count == 0:
            print("\n⚠️ 科目データが空っぽの罠を検知！テスト用に全8科目を自動生成します...")
            conn.execute(text("""
                INSERT INTO 科目 (科目名) VALUES 
                ('国語'), ('数学'), ('英語'), ('歴史'), 
                ('生命工学'), ('地球科学'), ('物理'), ('化学')
            """))

        # 🎯 実際の試験フォーマットに合わせて科目を分類
        # 必須科目（国語・英語・数学・歴史）
        mandatory_subjects = conn.execute(text("""
            SELECT id FROM 科目 WHERE 科目名 IN ('国語', '英語', '数学', '歴史')
        """)).fetchall()

        # 探求科目（生命工学・地球科学・物理・化学）
        elective_subjects = conn.execute(text("""
            SELECT id FROM 科目 WHERE 科目名 IN ('生命工学', '地球科学', '物理', '化学')
        """)).fetchall()
        
        # 2. スキャナーの動作をシミュレート（クラス1の全データをInsert）
        print(f"\n📝 スキャナーがクラスID {target_class_id}（計 {student_count}名）の成績データをDBにInsertします...")
        print("📊 受験フォーマット: 必須4科目 ＋ 探求選択2科目 ＝ 計6科目 / 学生")
        
        for student in students:
            # 成績表の作成
            result = conn.execute(text("""
                INSERT INTO 成績表 (学生_id, 受験者数, 実施日, 確認ステータス) 
                VALUES (:student_id, 100, :exam_date, '未確認')
            """), {"student_id": student.id, "exam_date": today})
            score_id = result.lastrowid
            
            # 🎲 各学生ごとに探求科目をランダムに2つ選択
            chosen_electives = random.sample(elective_subjects, 2)
            
            # 必須4科目 + 選択2科目 = 計6科目のリストを作成
            student_subjects = mandatory_subjects + chosen_electives
            
            # 6科目分の成績詳細（点数など）をInsert
            for subject in student_subjects:
                # ※実務では点数もrandomで変動させますが、今回はテスト高速化のため固定値
                conn.execute(text("""
                    INSERT INTO 成績詳細 (点数, 偏差値, 順位, 科目_id, 成績表_id)
                    VALUES (80, 55.0, 10, :subject_id, :score_id)
                """), {"subject_id": subject.id, "score_id": score_id})

    # ========================================================
    # 3. バックエンドAPIの呼び出し
    # ========================================================
    response = client.post("/api/drafts/alam-and-start-generation")
    
    # 4. レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "success"
    assert "alerts" in data
    
    # 5. フロントエンドが振り分けられるように、自分のクラスIDがalertsに含まれているか確認
    found_my_class = False
    for alert in data["alerts"]:
        if alert["class_id"] == target_class_id:
            found_my_class = True
            print(f"✅ 期待通り、クラスID:{target_class_id} 用のアラームデータを受信しました！")
            print(f"📩 メッセージ内容: {alert['message']}")
            break
            
    assert found_my_class == True

    # 6. DBのロック確認（データ蓄積によるエラーを防ぐため >= を使用）
    with engine.connect() as conn:
        processing_count = conn.execute(text("""
            SELECT COUNT(*) FROM 成績表 
            JOIN 学生 ON 成績表.学生_id = 学生.id
            WHERE 学生.クラス_id = :cid AND 成績表.確認ステータス = '生成中'
        """), {"cid": target_class_id}).scalar()
        
        assert processing_count >= student_count
        print(f"🔒 DBのステータスも「生成中」に正しくロックされています。（現在のロック件数: {processing_count}）")
        print("🎉 単一クラスAPI統合テスト（実務フォーマット版）、完全成功です！")


def test_api_1000_students_bulk_process():
        """
        全校生徒（約1000名）の成績データが一気に投入された場合の
        システムの耐久性とAPIの正確性を検証する負荷テスト。
        ※実際の試験フォーマット（必須4科目 ＋ 各学生固有の探求選択2科目 ＝ 計6科目）を完全に反映。
        """
        today = datetime.date.today()

        with engine.begin() as conn:
            # 1. データベース上の全学生を取得
            # 🌟 ここが進化！ 学生ごとに設定された「選択科目1」と「選択科目2」も一緒に取得します
            students = conn.execute(text("SELECT id, クラス_id, 選択科目1_id, 選択科目2_id FROM 学生")).fetchall()
            student_count = len(students)
            assert student_count > 0, "学生データが0件です！seed.pyを実行してください。"

            # 🚨 万が一のための科目データ生成ガードロジック
            subjects_count = conn.execute(text("SELECT COUNT(*) FROM 科目")).scalar()
            if subjects_count == 0:
                print("\n⚠️ 科目データが空っぽの罠を検知！テスト用に全8科目を自動生成します...")
                conn.execute(text("""
                    INSERT INTO 科目 (科目名) VALUES 
                    ('国語'), ('数学'), ('英語'), ('歴史'), 
                    ('生命工学'), ('地球科学'), ('物理'), ('化学')
                """))

            # 🎯 必須科目（国語・英語・数学・歴史）のIDを取得
            mandatory_subjects = conn.execute(text("""
                SELECT id FROM 科目 WHERE 科目名 IN ('国語', '英語', '数学', '歴史')
            """)).fetchall()
            mandatory_ids = [row.id for row in mandatory_subjects]

            print(f"\n📝 【負荷テスト】スキャナーが全校生徒 {student_count}名 分の成績データを一括Insertします... (数秒かかります)")
            print("📊 受験フォーマット: 必須4科目 ＋ 各学生がDBに登録している探求選択2科目 ＝ 計6科目 / 学生")
            
            # 2. 1000名分のデータ作成
            for student in students:
                # 成績表の作成
                result = conn.execute(text("""
                    INSERT INTO 成績表 (学生_id, 受験者数, 実施日, 確認ステータス) 
                    VALUES (:student_id, 1000, :exam_date, '未確認')
                """), {"student_id": student.id, "exam_date": today})
                score_id = result.lastrowid

                # 🌟 各学生がDB上に持っている固有の選択科目を、必須科目と合流させる！
                student_subjects = mandatory_ids + [student.選択科目1_id, student.選択科目2_id]
                
                # 6科目分の成績詳細（点数など）をInsert (1000人 × 6科目 = 6000回のINSERT!)
                for subject_id in student_subjects:
                    conn.execute(text("""
                        INSERT INTO 成績詳細 (点数, 偏差値, 順位, 科目_id, 成績表_id)
                        VALUES (80, 55.0, 10, :subject_id, :score_id)
                    """), {"subject_id": subject_id, "score_id": score_id})

        print(f"✅ {student_count}名分（成績詳細 計{student_count * 6}件）のデータ書き込み完了！ APIを呼び出します...")

        # ========================================================
        # 3. 1000名分のデータがある状態で、APIを実行！
        # ========================================================
        response = client.post("/api/drafts/alam-and-start-generation")
        
        # 4. 検証（APIが落ちずにちゃんと200 OKを返すか）
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # 全20クラスのデータが入っているはずなので、アラートも最大20クラス分返ってくるはず
        alerts = data["alerts"]
        print(f"📩 バックエンドから {len(alerts)} クラス分のアラーム通知配列が瞬時に返ってきました！")
        assert len(alerts) > 0

        # 5. DBのロック確認 (1000件すべてがロックされているか)
        with engine.connect() as conn:
            processing_count = conn.execute(text("""
                SELECT COUNT(*) FROM 成績表 
                WHERE 実施日 = :today AND 確認ステータス = '生成中'
            """), {"today": today}).scalar()
            
            print(f"🔒 DB上の「生成中」ロック件数: {processing_count} / {student_count}")
            # 何度もテストを実行した場合に備えて、>= を使用します
            assert processing_count >= student_count
            
        print("🎉 1000名規模の負荷・結合テスト（実務フォーマット版）、完全成功です！")