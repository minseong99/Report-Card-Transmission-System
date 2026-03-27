from fastapi import FastAPI, BackgroundTasks, HTTPException
import time
from monitor import check_new_scores
from pydantic import BaseModel
from sqlalchemy import text, create_engine
from fastapi.middleware.cors import CORSMiddleware # フロントエンド通信許容
import os

app = FastAPI(title="成績表送信システム API")

# ========================================
# 成績表草案生成
# ========================================
def generate_drafts_background(class_id: int, exam_date: str):
    """
    バックグラウンドで実行される重い処理: Comment, 推薦大学, 成績表生成
    """
    print(f"[クラス:{class_id}]の成績情報・コメント・推薦大学生成開始...")

    #time.sleep(5)

    print(f"[クラス:{class_id}]の成績表草案の生成が完了しました。DBを更新します。")

# ========================================
# システム内部のスケジューラから呼ばれるエンドポイント
# ========================================
@app.post("/api/drafts/alam-and-start-generation")
def trigger_draft_generation(background_tasks: BackgroundTasks):
    """
    講師への（フロントエンド）アラート通知を発生し、
    FastAPI BackgroundTasksを利用して、
    時間がかかる成績表草案生成の処理を非同期化するAPIエンドポイント
    """
    batches = check_new_scores()

    if not batches:
        return {
            "status": "success",
            "message": "新しい成績データはありません。",
            "alerts":[]
        }
    alerts = []

    #　成績表草案生成をバックグラウンドに投げる
    for batch in batches:
        class_id = batch["class_id"]
        exam_date = batch["exam_date"]
        background_tasks.add_task(generate_drafts_background, class_id, exam_date)
        
        alerts.append({
            "class_id": class_id,
            "message": f"[通知]{exam_date}実施の模擬試験（クラスID：{class_id}）の採点が完了しました。"
        })
        
    return {
        "status": "success",
        "alerts": alerts,
    }


import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import datetime

# .envを読み込む
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24時間

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ========================================
# ログインAPIエンドポイント
# ========================================
class LoginRequest(BaseModel):
    login_id: str
    password: str

DB_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DB_URL)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@app.post("/api/auth/login")
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
    
@app.get("/api/notification/{class_id}")
def get_class_notifications(class_id: int):
    """
    フルンとエンドが定期的にAPIを呼び出して、
    自分の担当クラスの成績表ステータスを確認する。
    """
    with engine.connect() as conn:
        query = text("""
                    SELECT 実施日, 確認ステータス, COUNT(成績表.id) as student_count
                    FROM 成績表
                    JOIN 学生 ON 成績表.学生_id = 学生.id
                    WHERE 学生.クラス_id = :class_id AND 実施日 >= CURRENT_DATE - INTERVAL 20 DAY
                    GROUP BY 実施日, 確認ステータス
                    ORDER BY 実施日 DESC    
                """)
        records = conn.execute(query, {"class_id": class_id}).fetchall()
        
        alerts = []
        exam_status_map = {}
        for r in records:
            exam_date = str(r.実施日)
            if exam_date not in exam_status_map:
                exam_status_map[exam_date] = []
            exam_status_map[exam_date].append({
                "status": r.確認ステータス,
                "count": r.student_count
            })
        
        for exam_date, statuses in exam_status_map.items():
            total_students = sum(s["count"] for s in statuses)

            processing_count = sum(s["count"] for s in statuses if s["status"] in ('未確認', '生成中'))

            if processing_count > 0:
                alerts.append({
                    "id" : f"{exam_date}-registered",
                    "message" : f"[{exam_date}実施分]{class_id}組の{total_students}名成績データが登録されました。",
                    "type": "processing",
                    "date": exam_date
                })
            done_count = sum(s["count"] for s in statuses if s["status"] == '完了')
            if done_count > 0 and done_count == total_students:
                alerts.append({
                    "id" : f"{exam_date}-done",
                    "message" : f"[{exam_date}実施分]{total_students}名の成績表生成が完了しました。",
                    "type": "success",
                    "date": exam_date
                })
            


        
        return {"status": "success", "alerts": alerts}
