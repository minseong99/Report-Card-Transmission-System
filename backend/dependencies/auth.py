from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt 
from core.config import settings # 設定をインポート

"""
APIエンドポイントの保護（認証・認可）を担当する依存性(Dependency)モジュール。
"""

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_teacher(token: str = Depends(oauth2_scheme)) -> dict:
    """
    送られてきたJWTトークンをデコード・検証し、現在ログイン中の講師情報を返す依存関数。
    APIの引数に `teacher: dict = Depends(get_current_teacher)` と記述するだけで認証が完了する。
    """
    try:
        # settings経由でシークレットキーとアルゴリズムを取得
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        login_id: str = payload.get("sub")
        class_id: int = payload.get("class_id")

        if login_id is None or class_id is None:
            # 401 Unauthorized エラーを明示的に指定
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="無効なトークンです。必要な情報が含まれていません。"
            )

        return {"login_id": login_id, "class_id": class_id}
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="トークンの有効期限が切れています。再度ログインしてください。"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="トークンが不正です。"
        )