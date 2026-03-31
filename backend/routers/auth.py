import os
import jwt 
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from passlib.context import CryptContext
from database import engine

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 24時間

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    login_id: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    """
    講師のログイン認証のAPIエンドポイント
    入力されたIDとパスワードをDBと比して、当たったらJWTを発行します。
    """
    with engine.connect() as conn:
        query = text("""
            SELECT id, 苗字, 名前, 担当クラス_id, パスワード
            FROM 講師
            WHERE ログイン_id = :login_id
        """)

        teacher = conn.execute(query, {
            "login_id": request.login_id
        }).fetchone()

        # ユーザの存在確認およびパスワードのハッシュの一致検証
        if not teacher or not pwd_context.verify(request.password, teacher.パスワード):
            raise HTTPException(status_code=401, detail="IDまたはパスワードが間違っています。")

        # JWT 生成
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": request.login_id,
            "class_id": teacher.担当クラス_id,
            "exp": expiration
        }
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        # token + 講師情報
        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer",
            "teacher": {
                "id": teacher.id,
                "name": f"{teacher.苗字} {teacher.名前}",
                "class_id": teacher.担当クラス_id
            }
        }
    
