"""
Database Schemas for Survey Builder

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
- Survey -> "survey"
- Response -> "response"
- User -> "user"

Questions are embedded within Survey documents.
"""

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


QuestionType = Literal[
    "multiple_choice", "checkbox", "short_text", "long_text", "rating", "nps"
]


class Question(BaseModel):
    id: str = Field(..., description="Client-generated stable id for the question")
    type: QuestionType
    title: str
    description: Optional[str] = None
    required: bool = False
    options: Optional[List[str]] = Field(
        default=None, description="Options for choice-based questions"
    )
    scale_max: Optional[int] = Field(
        default=5, description="For rating questions (number of stars/points)"
    )


class SurveyTheme(BaseModel):
    accent: str = "#D4AF37"  # default luxury gold
    background: str = "#0b0b0f"
    surface: str = "#13131a"
    text: str = "#e7e7ea"


class Survey(BaseModel):
    title: str
    description: Optional[str] = None
    status: Literal["draft", "published", "closed"] = "draft"
    owner_id: Optional[str] = None
    theme: SurveyTheme = SurveyTheme()
    questions: List[Question] = []
    share_slug: Optional[str] = Field(None, description="Public share code for published surveys")


class Response(BaseModel):
    survey_id: str
    answers: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of {questionId, value}"
    )
    meta: Dict[str, Any] = Field(default_factory=dict)


class User(BaseModel):
    name: str
    email: str
    role: Literal["admin", "editor", "viewer"] = "admin"
    avatar_url: Optional[str] = None
