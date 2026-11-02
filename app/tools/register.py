
from app.tools.registry import ToolRegistry
from app.models.tool_definition import ToolDefinition

from app.tools.knowledge_tools import knowledge_search


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # Knowledge retrieval
    registry.register(
        definition=ToolDefinition(
            name="knowledge_search",
            description=(
                "Search the internal knowledge base for runbooks, "
                "troubleshooting guides, and SIEM table schemas."
            ),
            category="knowledge",
            execution_type="direct",
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What information to search for."
                    },
                    "source_type": {
                        "type": ["string", "null"],
                        "enum": ["runbook", "table_schema", None],
                        "description": "Optional knowledge source filter."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        ),
        function=knowledge_search,
    )

    # Sentinel investigation is a graph capability.
    # It must go through KQL generation, validation and investigation.
    registry.register(
        definition=ToolDefinition(
            name="sentinel_investigation",
            description=(
                "Investigate an alert using Microsoft Sentinel. "
                "LangGraph will generate, validate and execute the "
                "required KQL queries."
            ),
            category="sentinel",
            execution_type="graph",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )
    )

    return registry
