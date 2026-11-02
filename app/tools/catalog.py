
from app.models.tool_definition import ToolDefinition
from app.tools.register import build_tool_registry


def get_available_tool_definitions() -> list[ToolDefinition]:
    """
    Return metadata for all enabled tools registered
    with the SIEM-INTEL agent.
    """
    registry = build_tool_registry()
    return registry.list_definitions()


def get_tool_catalog_for_llm() -> list[dict]:
    """
    Return a simplified tool catalog for the LLM.
    """
    catalog = []

    for tool in get_available_tool_definitions():
        catalog.append({
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "execution_type": tool.execution_type,
            "parameters": tool.parameters,
            "requires_approval": tool.requires_approval,
        })

    return catalog
