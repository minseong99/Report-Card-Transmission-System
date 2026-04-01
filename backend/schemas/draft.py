from pydantic import BaseModel
from typing import Dict

# score update schemas
class ScoreUpdateRequest(BaseModel):
    score_id: int 
    exam_date: str
    class_id: int
    updated_scores: Dict[str, int] # "{"score": 39 ...}"