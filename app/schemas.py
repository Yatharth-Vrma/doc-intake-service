from datetime import datetime
from typing import Any, List, Optional, Dict

from pydantic import BaseModel, Field


class Question(BaseModel):
    question_number: int = Field(..., description="Question number, e.g., 1, 2, 3")
    question_text: str = Field(..., description="Full question text")
    marks: Optional[int] = Field(None, description="Marks for this question, if found")


class ParsedFields(BaseModel):
    name: Optional[str] = Field(None, description="Student or candidate name")
    exam_name: Optional[str] = None
    roll_number: Optional[str] = None
    total_marks: Optional[int] = None
    questions: List[Question] = Field(default_factory=list)


class DocumentInDB(BaseModel):
    id: str = Field(..., alias="_id")
    filename: str
    content_type: str
    created_at: datetime
    raw_text: str
    parsed: ParsedFields

    class Config:
        populate_by_name = True


class UploadResponse(BaseModel):
    doc_id: str


class ErrorResponse(BaseModel):
    detail: str
