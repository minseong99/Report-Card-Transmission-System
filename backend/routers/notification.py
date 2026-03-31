from fastapi import APIRouter, Depends
from dependencies.auth import get_current_teacher # 移動したパスに注意
from services.notification_service import generate_class_alerts

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