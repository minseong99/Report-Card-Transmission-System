from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
import datetime 

from database import engine
from services.jwtToken_authentication import get_current_teacher
from services.pdf_service import generate_and_upload_pdf

router = APIRouter(prefix="/api/reports", tags=["Reports"])

class ConfirmReportRequest(BaseModel):
    student_id: int
    exam_date: str
    comment: str
    university: str

@router.post("/confirm")
def confirm_and_generate_report(request: ConfirmReportRequest, teacher: dict = Depends(get_current_teacher)):
    class_id = teacher["class_id"]
    current_year = datetime.date.today().year
    jan_first = f"{current_year}-01-01"

    with engine.begin() as conn:
        # 1. 学生の基本情報と順位を取得
        student_info_row = conn.execute(text("""
            SELECT s.id, s.苗字, s.名前, t.統合順位, t.クラス順位, t.id as score_id
            FROM 学生 s
            JOIN 成績表 t ON s.id = t.学生_id
            WHERE s.id = :student_id AND t.実施日 = :exam_date AND s.クラス_id = :class_id
        """), {"student_id" : request.student_id, "exam_date": request.exam_date, "class_id": class_id}).fetchone()

        if not student_info_row:
            raise HTTPException(status_code=404, detail="成績データが見つかりません。")
        
        student_info = dict(student_info_row._mapping)

        # 2. 今回の成績詳細を取得
        current_scores_raw = conn.execute(text("""
            SELECT m.科目名, d.点数, d.偏差値, d.順位 as overall_rank
            FROM 成績詳細 d 
            JOIN 科目 m ON d.科目_id = m.id
            WHERE d.成績表_id = :score_id
        """), {"score_id": student_info["score_id"]}).fetchall()

        current_scores = [{"subject": r.科目名, "score": r.点数, "hensachi": float(r.偏差値), "overall_rank": r.overall_rank} for r in current_scores_raw]

        # 3. １月からの成績推移を取得
        trend_raw = conn.execute(text("""
            SELECT t.実施日, m.科目名, d.点数
            FROM 成績表 t
            JOIN 成績詳細 d ON t.id = d.成績表_id
            JOIN 科目 m ON d.科目_id = m.id
            WHERE t.学生_id = :student_id AND t.実施日 >= :jan_first
            ORDER BY t.実施日 ASC
        """), {"student_id": request.student_id, "jan_first": jan_first}).fetchall()

        trend_dict = {}
        for tr in trend_raw:
            month_str = f"{tr.実施日.month}月"
            if tr.実施日 == datetime.date.fromisoformat(request.exam_date):
                month_str += "(今回)"
            if month_str not in trend_dict:
                trend_dict[month_str] = {"month": month_str}
            trend_dict[month_str][tr.科目名] = tr.点数
        trend_data = list(trend_dict.values())

        # 4. pdf生成
        file_url = generate_and_upload_pdf(
            class_id=class_id,
            exam_date=request.exam_date,
            student_info=student_info,
            current_scores=current_scores,
            trend_data=trend_data,
            comment=request.comment,
            university=request.university
        )

        # DBの成績表に S3 bucket urlを　 update
        conn.execute(text("""
            UPDATE 成績表
            SET 確認ステータス = '完了', s3_file_url = :file_url
            WHERE id = :score_id
        """), {"file_url": file_url['db_url'], "score_id": student_info["score_id"]})
    
    return {
        "status" : "success",
        "message" : "成績表が正常に成績されました。",
        "file_url" : file_url['presigned_url']
    }