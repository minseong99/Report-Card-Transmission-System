from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import jwt 
import os

# environment value 
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_teacher(token: str = Depends(oauth2_scheme)):
    """
    JWT Tokenを解読して検証してlogin_id, class_idをreturnします。
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login_id: str = payload.get("sub")
        class_id: int = payload.get("class_id")

        if login_id is None or class_id is None:
            raise HTTPException(status_code=401, detail="無効なトークンです。")

        return {"login_id": login_id, "class_id":class_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="トークンの有効期限が切れています。")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="トークンが不正です。")