from pydantic import BaseModel
from typing import List

"""
成績表に関するAPIのリクエスト・レスポンスのデータ構造(Schema)を定義します。
Pydanticモデルを使用することで、自動的なデータバリデーション（型チェック）が行われます。
"""

class ConfirmReportRequest(BaseModel):
    student_id: int
    exam_date: str
    comment: str
    university: str

class BatchSendRequest(BaseModel):
    student_ids: List[int]
    exam_date: str