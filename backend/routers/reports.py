from fastapi import APIRouter, Depends, BackgroundTasks

from dependencies.auth import get_current_teacher
from schemas.report import ConfirmReportRequest, BatchSendRequest
from services.report_service import generate_report_workflow
from services.notification_service import process_batch_notifications

"""
フロントエンドからのHTTPリクエストを受け取り、適切なサービスへ処理を委譲するルーター層(Controller)。
ここに複雑なロジックやSQLは記述せず、コードを極力薄く保ちます。
"""

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.post("/confirm")
def confirm_and_generate_report(request: ConfirmReportRequest, teacher: dict = Depends(get_current_teacher)):
    """
    成績表の最終確認を行い、PDFを生成してURLを返却します。
    """
    # 複雑な処理はすべてサービス層に丸投げします
    presigned_url = generate_report_workflow(
        student_id=request.student_id,
        exam_date=request.exam_date,
        comment=request.comment,
        university=request.university,
        class_id=teacher["class_id"]
    )
    
    return {
        "status": "success",
        "message": "成績表が正常に生成されました。",
        "file_url": presigned_url
    }


@router.post("/send-batch")
def send_batch_reports(request: BatchSendRequest, background_tasks: BackgroundTasks):
    """
    生成済みの成績表を保護者へ一括送信するバックグラウンドタスクを起動します。
    """
    # リクエストの検証はPydantic(BatchSendRequest)が自動で行うため、即座にタスクを登録できます
    background_tasks.add_task(
        process_batch_notifications, 
        student_ids=request.student_ids, 
        exam_date=request.exam_date
    )

    return {
        "status": "success",
        "message": f"{len(request.student_ids)}件の成績表を保護者へ送信開始しました。"
    }