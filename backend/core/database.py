from sqlalchemy import create_engine
from core.config import settings # 中央集権化された設定をインポート

"""
データベース接続を管理するモジュール。
エンジン(engine)をここで一度だけ初期化し、アプリケーション全体で使い回します。
"""

# pool_pre_ping=True: コネクションプールから接続を取得する前に、
# その接続がまだ有効か（DB側で切断されていないか）をチェックする実務必須のオプション。
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)