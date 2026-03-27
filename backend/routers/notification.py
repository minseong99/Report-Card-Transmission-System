from fastapi import APIRouter
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/api/notification", tags=["Notification"])

@router.get("/{class_id}")
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