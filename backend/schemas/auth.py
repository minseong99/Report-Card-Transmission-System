from pydantic import BaseModel

"""
認証(Auth)関連のAPIリクエストデータ構造(Schema)を定義します。
"""

class LoginRequest(BaseModel):
    login_id: str
    password: str