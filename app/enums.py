from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    QUED_FOR_ANALYSIS = "queued_for_analysis"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    # "Standard industry practices, no significant concerns"
    STANDART_PRACTICE = "standard_practice"
    # "Minor concerns, generally acceptable"
    LOW = "low"
    # "Some user-unfriendly terms, review recommended"
    MEDIUM = "medium"
    # "Significant consumer risks, legal review advised"
    HIGH = "high"
    # "Extremely problematic, avoid if possible"
    CRITICAL = "critical"

    @classmethod
    def values(cls):
        return [level.value for level in cls]
