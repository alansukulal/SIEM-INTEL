
from pydantic import BaseModel, Field


class InvestigationPlan(BaseModel):
    objective: str = Field(
        description="The specific question the investigation must answer."
    )

    candidate_tables: list[str] = Field(
        default_factory=list,
        description=(
            "Candidate SIEM tables that may contain the evidence needed "
            "for this investigation. Use table names supported by retrieved "
            "knowledge or conversation context. Return an empty list when "
            "no SIEM table is required. These tables must be schema-verified "
            "before KQL generation."
        )
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
