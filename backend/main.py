from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings # 設定をインポート
from routers import auth, drafts, notification, reports

"""
FastAPIアプリケーションのメインエントリーポイント（起動ファイル）。
ここではミドルウェアの設定と、各ルーター(APIエンドポイント)の登録のみを行います。
"""

app = FastAPI(title=settings.PROJECT_NAME)

# CORS (Cross-Origin Resource Sharing) の設定
# フロントエンド（Reactなど）からの別ポート・別ドメイン通信を許可する
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL], # 設定ファイルから読み込む
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 各機能ごとのルーター（APIグループ）をアプリケーションにマウントする
app.include_router(auth.router)
app.include_router(drafts.router)
app.include_router(notification.router)
app.include_router(reports.router)


