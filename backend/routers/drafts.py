from fastapi import APIRouter, BackgroundTasks, Depends
from services.monitor import check_new_scores
from dependencies.auth import get_current_teacher # 🌟 core/dependencies に移動したauthをインポート
from services.draft_service import get_preview_data, update_score_and_recalculate
from schemas.draft import ScoreUpdateRequest
from core.event_manager import event_manager

router = APIRouter(prefix="/api/drafts", tags=["Drafts"])

def generate_drafts_background(class_id: int, exam_date: str):
    print(f"[クラス:{class_id}]の成績情報・コメント・推薦大学生成開始...")
    print(f"[クラス:{class_id}]の成績表草案の生成が完了しました。DBを更新します。")

@router.post("/alam-and-start-generation")
def trigger_draft_generation(background_tasks: BackgroundTasks):
    """
    新しい採点データを監視し、存在する場合は草案生成のバックグラウンドタスクをトリガーします。
    """
    batches = check_new_scores()
    if not batches:
        return {"status": "success", "message": "新しい成績データはありません。", "alerts":[]}
    
    alerts = []
    for batch in batches:
        class_id = batch["class_id"]
        exam_date = batch["exam_date"]
        background_tasks.add_task(generate_drafts_background, class_id, exam_date)
        alerts.append({
            "class_id": class_id,
            "message": f"[通知]{exam_date}実施の模擬試験（クラスID：{class_id}）の採点が完了しました。"
        })
        event_manager.sync_broadcast(class_id, "REFRESH_DRAFTS")
    return {"status": "success", "alerts": alerts}

@router.get("/preview")
def get_class_draft_previews(teacher: dict = Depends(get_current_teacher)):
    """
    担当クラスのプレビューデータを取得 (URL生成含む)
    全ての複雑なロジックは draft_service に委譲しています。
    """
    return get_preview_data(teacher["class_id"])

@router.put("/update-score")
def update_student_score(request: ScoreUpdateRequest, teacher: dict = Depends(get_current_teacher)):
    """
    成績表プレビュ-画面からの「点数修正」リクエストを処理する。
    修正後、影響を受ける全生徒の順位・偏差値を再計算します。
    """
    result = update_score_and_recalculate(request)

    # 再計算が終わったらUIを更新するために最新のプレービューデータを返してあげる
    fresh_data = get_preview_data(teacher["class_id"])

    event_manager.sync_broadcast(teacher["class_id"], "REFRESH_DRAFTS")
    return {
        "status": "success",
        "message": result["message"],
        "fresh_data": fresh_data["data"]
    }