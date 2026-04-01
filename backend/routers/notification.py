from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from dependencies.auth import get_current_teacher # 移動したパスに注意
from services.notification_service import generate_class_alerts
import asyncio
from core.event_manager import event_manager
from dependencies.auth import get_current_teacher_query

"""
フロントエンド（ダッシュボード）のアラート表示に必要な通知APIを処理するルーター層。
"""

router = APIRouter(prefix="/api/notification", tags=["Notification"])

@router.get("/")
def get_class_notifications(teacher: dict = Depends(get_current_teacher)):
    """
    フロントエンドが定期的に(ポーリングで)呼び出し、
    担当クラスの成績表処理ステータス（通知一覧）を取得するエンドポイントです。
    """
    class_id = teacher["class_id"]
    
    # 全てのデータ集計ロジックはサービス層に丸投げします
    alerts = generate_class_alerts(class_id)
    
    return {
        "status": "success", 
        "alerts": alerts
    }

@router.get("/stream")
async def sse_endpoint(request: Request, teahcer: dict = Depends(get_current_teacher_query)):
    """
    Eventsourceと常時接続し、
    サーバー側からリアルタイムにイベント(SSE)を送信するストリーミング・エンドポイントです。
    """
    class_id = teahcer["class_id"]

    async def event_generator():
        # １. 接続時にクライアント専用のキューを作成して登録する。
        queue = await event_manager.subscribe(class_id)

        try:
            while True:
                # 2. クライアントが切られていないか確認
                if await request.is_disconnected():
                    break

                # 3. キューにメッセージが入るのを待機する。
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    # SSEの厳密なformatで送信
                    yield f"data:{message}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            # 4. クライアントがタブを閉じるなどして切断されたら、キューを削除する
            event_manager.unsubscribe(class_id, queue)
    # media_type="text/event-stream"を指定することで、ブラウザがSSE通信だと確認する
    return StreamingResponse(event_generator(), media_type="text/event-stream")    