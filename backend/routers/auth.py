from fastapi import APIRouter
from schemas.auth import LoginRequest
from services.auth_service import authenticate_teacher

"""
認証(ログイン)関連のHTTPリクエストを処理するルーター層(Controller)。
ビジネスロジックは auth_service に委譲し、コードを薄く保ちます。
"""

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/login")
def login(request: LoginRequest):
    """
    講師のログイン認証APIエンドポイント。
    成功した場合はJWTトークンと講師の基本情報を返却します。
    """
    auth_data = authenticate_teacher(request.login_id, request.password)
    
    return {
        "status": "success",
        **auth_data # auth_service から返されたトークンと講師情報を展開してマージ
    }
