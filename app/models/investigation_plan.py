
from pydantic import BaseModel, Field


class InvestigationPlan(BaseModel):
    objective: str = Field(
        description="The specific question the investigation must answer."
    )

    evidence_needed: list[str] = Field(
        description=(
            "The minimum evidence needed to answer the objective. "
            "Keep this focused and avoid unnecessary checks."
        )
    )

    success_criteria: list[str] = Field(
        description=(
            "Conditions under which the objective can be considered "
            "answered based on the available evidence."
        )
    )

    investigation_scope: str = Field(
        description=(
            "A concise description of the investigation boundaries "
            "and any important limitations."
        )
    )
