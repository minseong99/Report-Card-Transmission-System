import os
from dotenv import load_dotenv

# .envファイルを読み込む (アプリ起動時に一度だけ実行される)
load_dotenv()

class Settings:
    """
    アプリケーション全体の環境変数・設定を管理するクラス。
    各ファイルで個別に os.getenv() を呼ぶのではなく、このクラスを経由して設定値にアクセスします。
    これにより、タイポを防ぎ、デフォルト値の管理が一元化されます。
    """
    PROJECT_NAME: str = "成績表送信システム API"
    
    # データベース設定
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/dbname")
    
    # JWT 認証設定
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback_secret_key")
    ALGORITHM: str = "HS256"
    
    # CORS 設定 (フロントエンドのURL)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # MinIOクライアント設定
    ACCESS_KEY_ID: str = os.getenv('MINIO_ROOT_USER', 'user')
    SECRET_ACCESS_KEY: str = os.getenv('MINIO_ROOT_PASSWORD', 'pasword1234')

    MINIO_INTERNAL_ENDPOINT: str = os.getenv("MINIO_INTERNAL_ENDPOINT", "http://minio:9000")
    MINIO_EXTERNAL_ENDPOINT: str = os.getenv("MINIO_EXTERNAL_ENDPOINT", "http://localhost:9000")

# インスタンスを作成し、他のファイルから `settings.DATABASE_URL` のように呼び出せるようにする
settings = Settings()