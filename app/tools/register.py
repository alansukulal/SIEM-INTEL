
from app.tools.registry import ToolRegistry
from app.models.tool_definition import ToolDefinition

from app.tools.knowledge_tools import knowledge_search
from app.tools.web import web_search, web_scrape


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # ------------------------------------------
    # Internal Knowledge Search
    # ------------------------------------------

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

    # ------------------------------------------
    # External Web Search
    # ------------------------------------------

    registry.register(
        definition=ToolDefinition(
            name="web_search",
            description=(
                "Search the external internet for Microsoft Sentinel "
                "documentation, security advisories, vendor integration "
                "guides, and technical troubleshooting information. "
                "Use when internal knowledge is insufficient or external "
                "information is required."
            ),
            category="web",
            execution_type="direct",
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The external information to search for."
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                        "default": 5
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "default": "basic"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        ),
        function=web_search,
    )

    # ------------------------------------------
    # Webpage Scraping
    # ------------------------------------------

    registry.register(
        definition=ToolDefinition(
            name="web_scrape",
            description=(
                "Extract readable content from a specific public webpage. "
                "Use after web search when detailed documentation or "
                "additional webpage context is required."
            ),
            category="web",
            execution_type="direct",
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The public webpage URL to extract."
                    }
                },
                "required": ["url"],
                "additionalProperties": False
            }
        ),
        function=web_scrape,
    )

    # ------------------------------------------
    # Sentinel Investigation
    # ------------------------------------------

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
