
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    finding: str = Field(
        description=(
            "Concise findings based only on the collected evidence. "
            "Clearly identify missing or unverified evidence."
        )
    )

    evidence_sufficient: bool = Field(
        default=False,
        description=(
            "True only when the collected evidence is relevant, "
            "reliable, and sufficient to answer the original "
            "investigation objective. The mere presence of evidence "
            "does not make it sufficient."
        ),
    )

    evidence_assessment: str = Field(
        default="",
        description=(
            "Explain why the available evidence is or is not "
            "sufficient to answer the original objective."
        ),
    )

    missing_evidence: list[str] = Field(
        default_factory=list,
        description=(
            "List important evidence that is still missing or "
            "unverified. Return an empty list when no important "
            "evidence is missing."
        ),
    )

    investigation_complete: bool = Field(
        default=False,
        description=(
            "True only when sufficient evidence answers the original "
            "investigation objective. False when the objective remains "
            "unresolved or evidence is insufficient."
        ),
    )

    needs_more_investigation: bool = Field(
        default=False,
        description=(
            "True when another useful investigation action is available "
            "that could resolve an important unanswered question. "
            "False when no useful action remains."
        ),
    )

    next_investigation_reason: str = Field(
        default="",
        description=(
            "The specific unresolved question or reason for the next "
            "investigation action. Empty when no further action is needed."
        ),
    )
