from sqlalchemy import text
from sqlalchemy.engine import Connection

"""
講師の認証に関するデータベース操作(CRUD)を担当します。
"""

def get_teacher_by_login_id(conn: Connection, login_id: str):
    query = text("""
        SELECT id, 苗字, 名前, 担当クラス_id, パスワード
        FROM 講師
        WHERE ログイン_id = :login_id
    """)
    row = conn.execute(query, {"login_id": login_id}).fetchone()
    return dict(row._mapping) if row else None