
import json
import logging
from typing import Any

from app.agent.state import InvestigationState
from app.llm.client import LLMClient
from app.models.tool_selection import ToolSelectionResult
from app.tools.catalog import get_tool_catalog_for_llm

logger = logging.getLogger(__name__)


def _validate_tool_call(
    call: Any,
    catalog: list[dict],
) -> dict | None:
    """Validate a selected capability against the registered catalog."""

    tool_name = call.tool_name
    arguments = call.arguments

    if not isinstance(arguments, dict):
        logger.warning("Invalid arguments for tool '%s'.", tool_name)
        return None

    definition = next(
        (tool for tool in catalog if tool["name"] == tool_name),
        None,
    )

    if definition is None:
        logger.warning("Unregistered tool selected: %s", tool_name)
        return None

    if definition["execution_type"] == "graph" and arguments:
        logger.warning(
            "Graph capability '%s' does not accept arguments.",
            tool_name,
        )
        return None

    schema = definition.get("parameters", {})
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    if schema.get("additionalProperties") is False:
        if any(key not in properties for key in arguments):
            logger.warning("Unexpected arguments for '%s'.", tool_name)
            return None

    if any(key not in arguments for key in required):
        logger.warning("Missing required arguments for '%s'.", tool_name)
        return None

    if tool_name == "knowledge_search":
        query = arguments.get("query")

        if not isinstance(query, str) or not query.strip():
            return None

        source_type = arguments.get("source_type")
        if source_type not in (None, "runbook", "table_schema"):
            return None

        limit = arguments.get("limit", 5)
        if not isinstance(limit, int) or isinstance(limit, bool):
            return None

        if not 1 <= limit <= 10:
            return None

        clean_arguments = {
            "query": query.strip(),
            "source_type": source_type,
            "limit": limit,
        }
    else:
        clean_arguments = arguments

    return {
        "tool_name": tool_name,
        "arguments": clean_arguments,
        "reason": call.reason,
    }


def tool_selector_node(state: InvestigationState) -> dict:
    catalog = get_tool_catalog_for_llm()

    available_tool_names = [
        tool["name"] for tool in catalog
    ]

    prompt = f"""
You are the tool-selection component of SIEM-INTEL,
an agentic SIEM investigation platform.

Your task is to decide which registered capabilities
are required for the next investigation step.

ALERT:
{state.get("alert", "")}

SIEM:
{state.get("siem", "")}

INVESTIGATION PLAN:
{state.get("plan", "")}

CURRENT FINDING:
{state.get("finding", "")}

KNOWLEDGE:
{json.dumps(state.get("knowledge", []), default=str)[:5000]}

SENTINEL EVIDENCE:
{json.dumps(state.get("evidence", []), default=str)[:5000]}

PREVIOUS TOOL RESULTS:
{json.dumps(state.get("tool_results", [])[-5:], default=str)[:5000]}

PREVIOUS TOOL ERRORS:
{json.dumps(state.get("tool_errors", [])[-5:], default=str)[:3000]}

INVESTIGATION HISTORY:
{json.dumps(state.get("investigation_history", [])[-5:], default=str)[:3000]}

PREVIOUS ACTION REASON:
{state.get("next_investigation_reason", "")}

AVAILABLE TOOL CATALOG:
{json.dumps(catalog, indent=2, default=str)}

AVAILABLE TOOL NAMES:
{available_tool_names}

EXECUTION BUDGET:
{state.get("tool_execution_attempts", 0)}
/
{state.get("max_tool_execution_attempts", 10)}

RULES:
1. Select only tools present in the available tool catalog.
2. Use each tool only when it contributes useful evidence.
3. Do not repeat a previous action without a good reason.
4. Use knowledge_search for internal runbooks and table schemas.
5. Use sentinel_investigation when live Sentinel evidence is required.
6. sentinel_investigation accepts no arguments. LangGraph handles
   KQL generation, validation and execution.
7. Do not invent tool names or tool arguments.
8. Do not claim that an action succeeded before receiving its result.
9. If the investigation objective is already answered, finish.
10. If no useful action remains, finish and explain the limitation.
11. Do not select tools if the execution budget is exhausted.

Return a structured tool-selection result.
"""

    result: ToolSelectionResult = LLMClient().invoke_structured(
        prompt,
        ToolSelectionResult,
    )

    validated_calls = []

    if not result.investigation_complete:
        for call in result.tool_calls:
            validated = _validate_tool_call(call, catalog)

            if validated:
                validated_calls.append(validated)

    selected_tools = [
        call["tool_name"] for call in validated_calls
    ]

    # Do not silently treat an invalid or empty selection as success.
    execution_complete = result.investigation_complete
    selection_error = ""

    if not execution_complete and not validated_calls:
        selection_error = (
            "No valid tool calls were selected for the next step. "
            "The investigation cannot continue with the current selection."
        )

    return {
        "available_tools": available_tool_names,
        "selected_tools": selected_tools,
        "tool_calls": validated_calls,
        "execution_complete": execution_complete,
        "investigation_error": selection_error,
    }
