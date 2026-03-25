from fastapi import FastAPI, BackgroundTasks
import time
from monitor import check_new_scores

app = FastAPI(title="成績表送信システム API")

# ========================================
# 成績表草案生成
# ========================================
def generate_drafts_background(class_id: int, exam_date: str):
    """
    バックグラウンドで実行される重い処理: Comment, 推薦大学, 成績表生成
    """
    print(f"[{class_id}]の成績情報・コメント・推薦大学生成開始...")

    #time.sleep(5)

    print(f"[{class_id}]の成績表草案の生成が完了しました。DBを更新します。")

# ========================================
# システム内部のスケジューラから呼ばれるエンドポイント
# ========================================
@app.post("/api/drafts/alam-and-start-generation")
def trigger_draft_generation(background_tasks: BackgroundTasks):
    """
    講師への（フロントエンド）アラート通知を発生し、
    FastAPI BackgroundTasksを利用して、
    時間がかかる成績表草案生成の処理を非同期化するAPIエンドポイント
    """
    batches = check_new_scores()

    if not batches:
        return {
            "status": "success",
            "message": "新しい成績データはありません。",
            "alerts":[]
        }
    alerts = []

    #　成績表草案生成をバックグラウンドに投げる
    for batch in batches:
        class_id = batch["class_id"]
        exam_date = batch["exam_date"]
        background_tasks.add_task(generate_drafts_background, class_id, exam_date)
        
        alerts.append({
            "class_id": class_id,
            "message": f"[通知]{exam_date}実施の模擬試験（クラスID：{class_id}）の採点が完了しました。"
        })
        
    return {
        "status": "success",
        "alerts": alerts,
    }