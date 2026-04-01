import datetime
import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from core.database import engine
from core.config import settings # 🌟 中央管理の設定ファイル
import crud.auth_crud as crud

"""
認証のコアとなるビジネスロジックを担当するサービス層。
パスワードのハッシュ検証や、JWT(JSON Web Token)の発行を行います。
"""

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def authenticate_teacher(login_id: str, password: str) -> dict:
    with engine.connect() as conn:
        # 1. DBから講師情報を取得
        teacher = crud.get_teacher_by_login_id(conn, login_id)

        # 2. 存在確認およびパスワードの検証
        if not teacher or not pwd_context.verify(password, teacher["パスワード"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="IDまたはパスワードが間違っています。"
            )

        # 3. JWTトークンの生成 (設定は core/config.py から取得)
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=60)
        token_data = {
            "sub": login_id,
            "class_id": teacher["担当クラス_id"],
            "exp": expiration
        }
        access_token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # 4. コントローラーへ返すデータを整形
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "teacher": {
                "id": teacher["id"],
                "name": f"{teacher['苗字']} {teacher['名前']}",
                "class_id": teacher["担当クラス_id"]
            }
        }