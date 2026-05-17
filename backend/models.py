"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PrepareRequest(BaseModel):
    """
    Request model for the /prepare endpoint.
    Validates the incoming JSON payload.
    """
    topic: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="The topic to prepare questions for (e.g., 'Binary Trees', 'OOP')"
    )
    level: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Difficulty level (e.g., 'beginner', 'intermediate', 'advanced')"
    )


class QuestionItem(BaseModel):
    """A single interview question with answer and source."""
    question: str
    answer: str
    source: str


class CodingProblem(BaseModel):
    """A single coding problem with title, difficulty, platform, and link."""
    title: str
    difficulty: str
    platform: str
    link: str


class PrepareResponse(BaseModel):
    """
    Structured response model for the /prepare endpoint.
    Returns organized interview preparation data.
    """
    topic: str = Field(..., description="The requested topic")
    level: str = Field(..., description="The requested level")
    questions: List[QuestionItem] = Field(default_factory=list, description="List of interview questions")
    coding_problems: List[CodingProblem] = Field(default_factory=list, description="List of coding problems")
    sources: List[str] = Field(default_factory=list, description="List of reference sources")


class HistoryItem(BaseModel):
    """A single search history entry (summary view)."""
    id: str = Field(..., alias="_id")
    topic: str
    level: str
    created_at: Optional[str] = None

    class Config:
        populate_by_name = True
