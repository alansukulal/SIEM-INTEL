
from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    tool_name: str = Field(
        description=(
            "The exact registered capability selected for this "
            "investigation step."
        )
    )

    arguments: dict = Field(
        default_factory=dict,
        description="Arguments required by the selected capability.",
    )

    reason: str = Field(
        description="Why this capability is needed."
    )


class ToolSelectionResult(BaseModel):
    reasoning: str = Field(
        description="Brief explanation of the selection strategy."
    )

    tool_calls: list[ToolCall] = Field(
        default_factory=list,
        description="Capabilities selected for the current step.",
    )

    investigation_complete: bool = Field(
        default=False,
        description="Whether the investigation has enough information to finish.",
    )

    completion_reason: str = Field(
        default="",
        description="Why the investigation can be considered complete.",
    )
