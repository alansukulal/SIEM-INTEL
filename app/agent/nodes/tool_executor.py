
import logging
from typing import Any

from app.agent.state import InvestigationState
from app.tools.register import build_tool_registry

logger = logging.getLogger(__name__)

DIRECT_EXECUTABLE_TOOLS = {
    "knowledge_search",
}

GRAPH_CAPABILITIES = {
    "sentinel_investigation",
}


def tool_executor_node(state: InvestigationState) -> dict[str, Any]:
    """Execute registered direct tools and queue graph capabilities."""

    registry = build_tool_registry()

    tool_calls = state.get("tool_calls", [])
    knowledge = list(state.get("knowledge", []))

    results = []
    errors = []
    pending_capabilities = []

    execution_attempts = state.get("tool_execution_attempts", 0)
    max_attempts = state.get("max_tool_execution_attempts", 10)

    if execution_attempts >= max_attempts:
        return {
            "pending_capabilities": [],
            "current_action": "",
            "tool_batch_complete": True,
            "investigation_error": (
                "Tool execution budget exhausted. "
                "No additional tools can be executed."
            ),
        }

    for call in tool_calls:

        if execution_attempts >= max_attempts:
            errors.append({
                "tool": "unknown",
                "error": "Tool execution budget exhausted.",
            })
            break

        if not isinstance(call, dict):
            errors.append({
                "tool": "unknown",
                "error": "Tool call must be a dictionary.",
            })
            continue

        tool_name = call.get("tool_name")
        arguments = call.get("arguments", {})

        if not isinstance(tool_name, str) or not isinstance(arguments, dict):
            errors.append({
                "tool": str(tool_name),
                "error": "Invalid tool name or arguments.",
            })
            continue

        try:
            definition = registry.get_definition(tool_name)

            if not definition.enabled:
                raise PermissionError(f"Tool is disabled: {tool_name}")

            # Graph capabilities are routed through LangGraph.
            if definition.execution_type == "graph":
                if tool_name not in GRAPH_CAPABILITIES:
                    raise PermissionError(
                        f"Graph capability is not approved: {tool_name}"
                    )

                if arguments:
                    raise ValueError(
                        "Graph capability does not accept direct arguments."
                    )

                if tool_name not in pending_capabilities:
                    pending_capabilities.append(tool_name)

                continue

            # Direct execution must be explicitly allowlisted.
            if tool_name not in DIRECT_EXECUTABLE_TOOLS:
                raise PermissionError(
                    f"Direct execution is not allowed: {tool_name}"
                )

            if definition.requires_approval:
                raise PermissionError(
                    f"Tool requires approval: {tool_name}"
                )

            # Check arguments against the registered JSON schema.
            schema = definition.parameters
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            if schema.get("additionalProperties") is False:
                unexpected = set(arguments) - set(properties)
                if unexpected:
                    raise ValueError(
                        f"Unexpected arguments: {sorted(unexpected)}"
                    )

            missing = [
                key for key in required if key not in arguments
            ]
            if missing:
                raise ValueError(
                    f"Missing required arguments: {missing}"
                )

            if tool_name == "knowledge_search":
                query = arguments.get("query")
                source_type = arguments.get("source_type")
                limit = arguments.get("limit", 5)

                if not isinstance(query, str) or not query.strip():
                    raise ValueError("A non-empty query is required.")

                if source_type not in (None, "runbook", "table_schema"):
                    raise ValueError("Invalid knowledge source_type.")

                if (
                    not isinstance(limit, int)
                    or isinstance(limit, bool)
                    or not 1 <= limit <= 10
                ):
                    raise ValueError("Knowledge search limit must be 1-10.")

                arguments = {
                    "query": query.strip(),
                    "source_type": source_type,
                    "limit": limit,
                }

            # Count only actual direct execution attempts.
            execution_attempts += 1

            result = registry.execute(tool_name, arguments)

            if tool_name == "knowledge_search":
                if isinstance(result, list):
                    knowledge.extend(result)
                else:
                    raise TypeError(
                        "Knowledge search must return a list."
                    )

            results.append({
                "tool": tool_name,
                "status": "success",
                "result": result,
            })

        except Exception as exc:
            logger.exception("Tool execution failed: %s", tool_name)

            errors.append({
                "tool": tool_name,
                "error": str(exc),
            })

    return {
        "knowledge": knowledge,
        "tool_execution_attempts": execution_attempts,
        "tool_results": state.get("tool_results", []) + results,
        "tool_errors": state.get("tool_errors", []) + errors,
        "pending_capabilities": pending_capabilities,
        "current_action": (
            pending_capabilities[0] if pending_capabilities else ""
        ),
        "tool_batch_complete": True,
    }
