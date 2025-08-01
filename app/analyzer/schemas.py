from pydantic import BaseModel, Field
from app import enums
from typing import Optional, List


class DocumentCreate(BaseModel):
    user_context: Optional[str] = None
    file_url: str
    status: str

    class Config:
        from_attributes = True


class DocumentChapter(BaseModel):
    chapter_name: str
    chapter_text: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None


class ClauseAnalysis(BaseModel):
    """Analysis result for a Terms & Conditions clause."""

    category: Optional[List[str]] = Field(
        description="Categories of the clause")

    risk_level: enums.RiskLevel = Field(description="Risk level for consumers")

    reason: Optional[str] = Field(description="Reasoning for risk level")

    key_points: List[str] = Field(description="Key points from the clause")

    conclusion: str = Field(
        description="Conclusion about the clause so user understands how to proceed")
    
    is_valid: bool = Field(
        description=(
            "Set to **false** if the clause appears to be broken, malformed, or incomplete. "
            "For example, clauses that contain random or merged headings, unrelated topics, or "
            "gibberish text. The clause should be readable, coherent, and contain complete ideas. "
            "If it looks like multiple sections got mashed together or lacks logical structure, mark it as false."
        )
    )
    

class ChapterAnalysis(ClauseAnalysis):
    """Analysis result for a chapter in the Terms & Conditions document."""

    chapter_name: Optional[str] = Field(description="Name of the chapter being analyzed")
    page_start: Optional[int] = Field(
        default=None, description="Starting page of the chapter")
    page_end: Optional[int] = Field(
        default=None, description="Ending page of the chapter")


class ClauseAnalysisResponse(ChapterAnalysis):
    """Response model for clause analysis with additional metadata."""

    document_id: int = Field(description="ID of the document this clause belongs to")
    id: str = Field(description="Unique identifier for the clause in the database")
