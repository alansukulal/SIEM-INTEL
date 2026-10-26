
from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    finding: str = Field(
        description="Concise findings based only on the collected evidence."
    )
    needs_more_investigation: bool = Field(
        description=(
            "True if an important unanswered question requires "
            "additional investigation; otherwise False."
        )
    )
    next_investigation_reason: str = Field(
        default="",
        description="What question the next investigation should answer."
    )
