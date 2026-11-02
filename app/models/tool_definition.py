
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str = Field(
        description="Unique name of the tool."
    )

    description: str = Field(
        description="What the tool does and when the agent should use it."
    )

    category: Literal[
        "knowledge",
        "sentinel",
        "web",
        "jira",
    ]

    execution_type: Literal[
        "direct",
        "graph",
    ] = Field(
        description="Whether execution happens directly or through LangGraph."
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema describing the accepted arguments."
    )

    requires_approval: bool = Field(
        default=False,
        description="Whether user approval is required before execution."
    )

    enabled: bool = Field(
        default=True,
        description="Whether this tool is currently available to the agent."
    )
