from fastapi import APIRouter, BackgroundTasks, Depends
from services.monitor import check_new_scores
import datetime
from sqlalchemy import text
from database import engine
from services.jwtToken_authentication import get_current_teacher

router = APIRouter(prefix="/api/drafts", tags=["Drafts"])

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
@router.post("/alam-and-start-generation")
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

# ========================================
# 成績に入る情報を見せるためのAPI（持続的にモニタリング)
# ========================================
@router.get("/preview")
def get_class_draft_previews(teacher: dict = Depends(get_current_teacher)):
    """
    担当クラスの「直近25日以内」の試験データを取得し、
    今年1月からの成績推移を含めた完全なプレービューデータを返す。
    """

    class_id = teacher["class_id"]
    current_year = datetime.date.today().year
    feb_first = f"{current_year}-01-01"

    with engine.connect() as conn:
        # 1. 最近25日以内の「最近の試験日」を特定する
        exam_record = conn.execute(text("""
            SELECT DISTINCT 実施日 FROM 成績表
            JOIN 学生 ON 成績表.学生_id = 学生.id
            WHERE 学生.クラス_id = :class_id
                AND 実施日 >= CURRENT_DATE - INTERVAL 25 DAY
            ORDER BY 実施日 DESC LIMIT 1
        """), {"class_id":class_id}).fetchone()

        if not exam_record:
            return {"status": "success", "exam_date": None, "data": []}
        
        latest_date = exam_record.実施日

        # 2. 試験を受けた「担当クラスの学生一覧」を取得
        students = conn.execute(text("""
            SELECT s.id, s.苗字, s.名前, t.統合順位, t.クラス順位, t.id as score_id, t.確認ステータス
            FROM 学生 s
            JOIN 成績表 t ON s.id = t.学生_id
            WHERE s.クラス_id = :class_id AND t.実施日 = :latest_date
        """), {"class_id":class_id, "latest_date": latest_date}).fetchall()

        result_data = []

        # 3. 各学生の「今回の成績詳細」と「１月からの推移」を組み立てる
        for st in students:
            student_id = st.id 
            student_name = f"{st.苗字} {st.名前}"

            # a. 今回の成績詳細(科目、　点数、　偏差値、　全校順位)
            current_scores_rw = conn.execute(text("""
                SELECT m.科目名, d.点数, d.偏差値, d.順位 as overall_rank
                FROM 成績詳細 d
                JOIN 科目 m ON d.科目_id = m.id
                WHERE d.成績表_id = :score_id                                 
            """), {"score_id": st.score_id}).fetchall()

            current_scores = []
            total_score = 0
            for cs in current_scores_rw:
                current_scores.append({
                    "subject": cs.科目名,
                    "score": cs.点数,
                    "hensachi": float(cs.偏差値),
                    "overall_rank" : cs.overall_rank
                })
                total_score += cs.点数
            
            # b. １月以降の全成績推移を取得
            trend_raw = conn.execute(text("""
                SELECT t.実施日, m.科目名, d.点数
                FROM 成績表 t
                JOIN 成績詳細 d ON t.id = d.成績表_id
                JOIN 科目 m ON d.科目_id = m.id
                WHERE t.学生_id = :student_id AND t.実施日 >= :feb_first
                ORDER BY t.実施日 ASC
            """), {"student_id": student_id, "feb_first": feb_first}).fetchall()

            # {"4月": {"国語": 80 ,"英語": 90...}, ...}
            trend_dict = {}
            for tr in trend_raw:
                month_str = f"{tr.実施日.month}月"
                if tr.実施日 == latest_date:
                    month_str += "(今回)"
                
                if month_str not in trend_dict:
                    trend_dict[month_str] = {"month": month_str}
                
                trend_dict[month_str][tr.科目名] = tr.点数

            trend_data = list(trend_dict.values())

            # 4. 最終データをリストに追加
            result_data.append({
                "studentId" : student_id,
                "studentName": student_name,
                "class_id": class_id,
                "overallRank": st.統合順位,
                "classRank": st.クラス順位,
                "totalScore": total_score,
                "currentScores": current_scores,
                "trendData": trend_data,
                "status": st.確認ステータス
            })
        
        return {"status": "success", "exam_date": str(latest_date), "data": result_data}
