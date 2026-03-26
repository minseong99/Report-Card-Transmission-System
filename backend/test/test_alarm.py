import sys
import os
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
import random
import statistics

# パスの解決
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)
DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL)

def test_api_trigger_and_response_format():
    """
    特定のクラスの成績データのみがスキャン完了した際に、
    該当講師にのみ通知が送信され、DBが正しくロックされるかを検証するテスト。
    ※ 実際の試験フォーマット（必須4科目 + 探求2科目）を反映し、
    ※ リアルな点数、偏差値、順位を自動計算してDBに挿入する超実践的テスト。
    """
    today = datetime.date.today()

    with engine.begin() as conn:
        
        # テスト対象をrandomで決める
        target_class_id = random.randint(1, 20)
        # ========================================================
        #  0. テストデータのクリーンアップ（テストの冪等性を担保）
        # 同じ日に何度もテストを実行してデータが矛盾（重複）しないよう、
        # 新しくInsertする前に「本日の成績データ」を完全に削除してリセットします。
        # ========================================================
        # 成績詳細のデータを削除

        conn.execute(text("""
                DELETE d FROM 成績詳細 d
                JOIN 成績表 s ON d.成績表_id = s.id
                JOIN 学生 k ON s.学生_id = k.id
                WHERE s.実施日 = :today AND k.クラス_id = :class_id
            """), {"today": today, "class_id":target_class_id})
            
        #  次に成績表のデータを削除
        conn.execute(text("""
                DELETE s FROM 成績表 s
                JOIN 学生 k ON s.学生_id = k.id
                WHERE s.実施日 = :today AND k.クラス_id = :class_id
            """), {"today": today,"class_id":target_class_id})   
         
        
        
        # 対象のクラスに所属している学生情報
        students = conn.execute(text("""
            SELECT id, 選択科目1_id, 選択科目2_id 
            FROM 学生 
            WHERE クラス_id = :cid
        """), {"cid": target_class_id}).fetchall()
        
        student_count = len(students)
        assert student_count > 0, "クラスの学生データが存在しません。seed.pyを実行してください。"

        # 必須科目（国語・英語・数学・歴史）のIDリストを取得
        mandatory_subjects = conn.execute(text("""
            SELECT id FROM 科目 WHERE 科目名 IN ('国語', '英語', '数学', '歴史')
        """)).fetchall()
        mandatory_ids = [row.id for row in mandatory_subjects]
        
        print(f"\nスキャナーがクラスID {target_class_id}（計 {student_count}名）の成績データをInsertします...")
        print("受験フォーマット: 必須4科目 + 探求選択2科目 = 計6科目 / 学生")
        print("点数のランダム生成、および偏差値・順位のリアルタイム計算を開始します...")
        
        # --- 偏差値・順位計算のためのデータ一時保存用辞書 ---
        # 構造: { 科目ID: [ {'score_id': 成績表ID, 'score': 点数}, ... ] }
        subject_scores = {}

        # 1-1. まず全学生の「成績表（親データ）」を作成し、ランダムな点数を生成
        for student in students:
            # 成績表の作成
            result = conn.execute(text("""
                INSERT INTO 成績表 (学生_id, 受験者数, 実施日, 確認ステータス) 
                VALUES (:student_id, :total_students, :exam_date, '未確認')
            """), {
                "student_id": student.id, 
                "total_students": student_count, # クラス人数をセット
                "exam_date": today
            })
            score_id = result.lastrowid
            
            # 必須4科目 + この学生が選択した探求2科目のIDリストを作成
            student_sub_ids = mandatory_ids + [student.選択科目1_id, student.選択科目2_id]
            
            for sub_id in student_sub_ids:
                if sub_id not in subject_scores:
                    subject_scores[sub_id] = []
                
                # 30点〜100点の間でランダムな点数を生成
                subject_scores[sub_id].append({
                    'score_id': score_id,
                    'score': random.randint(30, 100) 
                })

        # 1-2. 科目ごとに平均・標準偏差・順位を計算し、DB(成績詳細)にInsertする
        for sub_id, records in subject_scores.items():
            # 順位をつけるため、点数が高い順（降順）に並び替え
            records.sort(key=lambda x: x['score'], reverse=True)
            
            # 統計計算用の点数リスト
            scores_list = [r['score'] for r in records]
            avg = statistics.mean(scores_list)
            # 母集団の標準偏差を計算（人数が1人の場合は0にするエラー回避）
            stdev = statistics.pstdev(scores_list) if len(scores_list) > 1 else 0
            
            # 各学生の順位と偏差値を計算してInsert
            for i, r in enumerate(records):
                # 順位計算（前の人と同じ点数なら同順位にするリアルな処理）
                if i > 0 and r['score'] == records[i-1]['score']:
                    rank = records[i-1]['rank']
                else:
                    rank = i + 1
                r['rank'] = rank # 同順位判定のために辞書に保存
                
                # 偏差値計算 (得点 - 平均) / 標準偏差 * 10 + 50
                if stdev == 0:
                    hensachi = 50.0 # 全員同じ点数などの例外時
                else:
                    hensachi = round((r['score'] - avg) / stdev * 10 + 50, 1)

                # 成績詳細のInsert
                conn.execute(text("""
                    INSERT INTO 成績詳細 (点数, 偏差値, 順位, 科目_id, 成績表_id)
                    VALUES (:score, :hensachi, :rank, :sub_id, :score_id)
                """), {
                    "score": r['score'],
                    "hensachi": hensachi,
                    "rank": rank,
                    "sub_id": sub_id,
                    "score_id": r['score_id']
                })

    # ========================================================
    # 2. バックエンドAPIの呼び出し
    # ========================================================
    response = client.post("/api/drafts/alam-and-start-generation")
    
    # 3. レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # 4. アラームの検証
    found_my_class = False
    for alert in data["alerts"]:
        if alert["class_id"] == target_class_id:
            found_my_class = True
            print(f"期待通り、クラスID:{target_class_id} 用のアラームデータを受信しました！")
            print(f"メッセージ内容: {alert['message']}")
            break
            
    assert found_my_class == True

    # 5. DBのロック確認
    with engine.connect() as conn:
        processing_count = conn.execute(text("""
            SELECT COUNT(*) FROM 成績表 
            JOIN 学生 ON 成績表.学生_id = 学生.id
            WHERE 学生.クラス_id = :cid AND 成績表.確認ステータス = '生成中'
        """), {"cid": target_class_id}).scalar()
        
        assert processing_count >= student_count
        print(f"DBのステータスも「生成中」に正しくロックされています。（ロック件数: {processing_count}）")
        print(" 単一クラスAPI統合テスト（超実践的・自動計算版）、完全成功です")


def test_api_1000_students_bulk_process():
        """
        全校生徒（約1000名）の成績データが一気に投入された場合の負荷テスト。
        ※ 科目ごとの偏差値・順位だけでなく、
        ※ 【総点に基づく統合順位（全校順位）とクラス順位】も計算して成績表に反映する完全版。
        """
        today = datetime.date.today()
        from collections import defaultdict # クラスごとの順位計算に使用

        with engine.begin() as conn:
            # 0. クリーンアップ処理 (省略せずにそのまま使用)
            conn.execute(text("""
                DELETE d FROM 成績詳細 d
                JOIN 成績表 s ON d.成績表_id = s.id
                WHERE s.実施日 = :today
            """), {"today": today})
            
            conn.execute(text("""
                DELETE FROM 成績表 WHERE 実施日 = :today
            """), {"today": today})  

            # 1. 学生データの取得
            students = conn.execute(text("SELECT id, クラス_id, 選択科目1_id, 選択科目2_id FROM 学生")).fetchall()
            student_count = len(students)
            assert student_count > 0, "学生データが0件です！"

            mandatory_subjects = conn.execute(text("""
                SELECT id FROM 科目 WHERE 科目名 IN ('国語', '英語', '数学', '歴史')
            """)).fetchall()
            mandatory_ids = [row.id for row in mandatory_subjects]

            print(f"\n【負荷テスト】全校生徒 {student_count}名分の成績データをInsertします...")
            print("1000名規模の科目別偏差値・順位、および【総点ベースの全校・クラス順位】を計算します...")

            subject_scores = {}
            # 追加: 総点による順位計算のためのリスト
            student_totals = [] 

            # 2-1. 成績表の作成とランダム点数生成
            for student in students:
                result = conn.execute(text("""
                    INSERT INTO 成績表 (学生_id, 受験者数, 実施日, 確認ステータス) 
                    VALUES (:student_id, :total_students, :exam_date, '未確認')
                """), {
                    "student_id": student.id, 
                    "total_students": student_count,
                    "exam_date": today
                })
                score_id = result.lastrowid

                student_sub_ids = mandatory_ids + [student.選択科目1_id, student.選択科目2_id]
                
                total_score = 0 # 学生1人あたりの総点（6科目合計）
                
                for sub_id in student_sub_ids:
                    if sub_id not in subject_scores:
                        subject_scores[sub_id] = []
                    
                    score = random.randint(20, 100)
                    total_score += score # 総点に加算
                    
                    subject_scores[sub_id].append({
                        'score_id': score_id,
                        'score': score 
                    })
                
                # 学生ごとの総点データを保存（後で順位計算に使うため）
                student_totals.append({
                    'score_id': score_id,
                    'class_id': student.クラス_id,
                    'total_score': total_score
                })

            # 2-2. 科目ごとの偏差値・順位計算 (成績詳細へのInsert)
            for sub_id, records in subject_scores.items():
                records.sort(key=lambda x: x['score'], reverse=True)
                scores_list = [r['score'] for r in records]
                avg = statistics.mean(scores_list)
                stdev = statistics.pstdev(scores_list) if len(scores_list) > 1 else 0
                
                for i, r in enumerate(records):
                    rank = records[i-1]['rank'] if i > 0 and r['score'] == records[i-1]['score'] else i + 1
                    r['rank'] = rank 
                    hensachi = 50.0 if stdev == 0 else round((r['score'] - avg) / stdev * 10 + 50, 1)

                    conn.execute(text("""
                        INSERT INTO 成績詳細 (点数, 偏差値, 順位, 科目_id, 成績表_id)
                        VALUES (:score, :hensachi, :rank, :sub_id, :score_id)
                    """), {
                        "score": r['score'], "hensachi": hensachi,
                        "rank": rank, "sub_id": sub_id, "score_id": r['score_id']
                    })

            # ========================================================
            # 2-3. 【総点ベース】統合順位（全校順位）とクラス順位の計算＆UPDATE
            # ========================================================
            # ① 統合順位（全校順位）の計算
            student_totals.sort(key=lambda x: x['total_score'], reverse=True)
            for i, st in enumerate(student_totals):
                # 同点の場合は同じ順位にする
                if i > 0 and st['total_score'] == student_totals[i-1]['total_score']:
                    st['overall_rank'] = student_totals[i-1]['overall_rank']
                else:
                    st['overall_rank'] = i + 1

            # ② クラス順位の計算（クラスごとにグループ化して順位付け）
            class_groups = defaultdict(list)
            for st in student_totals:
                class_groups[st['class_id']].append(st)
                
            for cid, group in class_groups.items():
                group.sort(key=lambda x: x['total_score'], reverse=True)
                for i, st in enumerate(group):
                    if i > 0 and st['total_score'] == group[i-1]['total_score']:
                        st['class_rank'] = group[i-1]['class_rank']
                    else:
                        st['class_rank'] = i + 1

            # ③ 成績表(親テーブル)に計算結果をUPDATE
            for st in student_totals:
                conn.execute(text("""
                    UPDATE 成績表 
                    SET 統合順位 = :overall_rank, クラス順位 = :class_rank 
                    WHERE id = :score_id
                """), {
                    "overall_rank": st['overall_rank'],
                    "class_rank": st['class_rank'],
                    "score_id": st['score_id']
                })
            print("全校順位およびクラス順位の計算・DB反映が完了しました！")

        print(f"データ書き込み完了！ APIを呼び出します...")

        # 3. API実行 と 4. 検証 (以降は既存のコードと同じ)
        response = client.post("/api/drafts/alam-and-start-generation")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        alerts = data["alerts"]
        assert len(alerts) > 0

        with engine.connect() as conn:
            processing_count = conn.execute(text("""
                SELECT COUNT(*) FROM 成績表 WHERE 実施日 = :today AND 確認ステータス = '生成中'
            """), {"today": today}).scalar()
            assert processing_count >= student_count
            
        print("🎉 1000名規模の負荷・結合テスト（統合順位＆クラス順位対応・完全版）、大成功です！")