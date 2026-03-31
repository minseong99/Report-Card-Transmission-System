from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # フロントエンド通信許容
from dotenv import load_dotenv

# .envを読み込む
load_dotenv()

from routers import auth, drafts, notification, reports

app = FastAPI(title="成績表送信システム API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(drafts.router)
app.include_router(notification.router)
app.include_router(reports.router)


