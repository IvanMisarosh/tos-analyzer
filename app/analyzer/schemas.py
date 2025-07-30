from pydantic import BaseModel, Field
from app import enums
from typing import Optional, List


class DocumentCreate(BaseModel):
    user_context: Optional[str] = None
    file_url: str
    status: str

    class Config:
        from_attributes = True


class ClauseAnalysis(BaseModel):
    """Analysis result for a Terms & Conditions clause."""

    category: Optional[List[str]] = Field(
        description="Categories of the clause (as few as possible)")

    risk_level: enums.RiskLevel = Field(description="Risk level for consumers")

    reason: Optional[str] = Field(description="Reasoning for risk level (short)")

    key_points: List[str] = Field(description="Key points from the clause (short, and concise)")

    conclusion: str = Field(
        description="Conclusion about the clause so user understands how to proceed")
