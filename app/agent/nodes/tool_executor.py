
import logging
from typing import Any

from app.agent.state import InvestigationState
from app.tools.register import build_tool_registry

logger = logging.getLogger(__name__)

GRAPH_CAPABILITIES = {
    "sentinel_investigation",
}


def _validate_arguments(
    tool_name: str,
    arguments: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Validate direct tool arguments against the registered schema."""

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    if schema.get("additionalProperties") is False:
        unexpected = set(arguments) - set(properties)
        if unexpected:
            raise ValueError(
                f"Unexpected arguments for '{tool_name}': "
                f"{sorted(unexpected)}"
            )

    missing = [
        key for key in required if key not in arguments
    ]
    if missing:
        raise ValueError(
            f"Missing required arguments for '{tool_name}': {missing}"
        )

    for key, value in arguments.items():
        property_schema = properties.get(key, {})
        expected_type = property_schema.get("type")

        if isinstance(expected_type, list):
            valid_type = any(
                _matches_type(value, item)
                for item in expected_type
            )
        else:
            valid_type = _matches_type(value, expected_type)

        if not valid_type:
            raise ValueError(
                f"Invalid type for argument '{key}' "
                f"in tool '{tool_name}'."
            )

        if "enum" in property_schema and value not in property_schema["enum"]:
            raise ValueError(
                f"Invalid value for argument '{key}' in '{tool_name}'."
            )

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            minimum = property_schema.get("minimum")
            maximum = property_schema.get("maximum")

            if minimum is not None and value < minimum:
                raise ValueError(f"'{key}' must be at least {minimum}.")

            if maximum is not None and value > maximum:
                raise ValueError(f"'{key}' must not exceed {maximum}.")

        if isinstance(value, str):
            minimum_length = property_schema.get("minLength")
            maximum_length = property_schema.get("maxLength")

            if minimum_length is not None and len(value) < minimum_length:
                raise ValueError(f"'{key}' is too short.")

            if maximum_length is not None and len(value) > maximum_length:
                raise ValueError(f"'{key}' is too long.")

    return arguments


def _matches_type(value: Any, expected_type: str | None) -> bool:
    """Check common JSON schema primitive types."""

    if expected_type is None:
        return True

    if expected_type == "string":
        return isinstance(value, str)

    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)

    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    if expected_type == "boolean":
        return isinstance(value, bool)

    if expected_type == "object":
        return isinstance(value, dict)

    if expected_type == "array":
        return isinstance(value, list)

    if expected_type == "null":
        return value is None

    return False


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

        if (
            not isinstance(tool_name, str)
            or not isinstance(arguments, dict)
        ):
            errors.append({
                "tool": str(tool_name),
                "error": "Invalid tool name or arguments.",
            })
            continue

        try:
            definition = registry.get_definition(tool_name)

            if not definition.enabled:
                raise PermissionError(
                    f"Tool is disabled: {tool_name}"
                )

            # Graph capabilities are handled by LangGraph.
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

            # All registered direct tools can execute through the registry.
            if definition.execution_type != "direct":
                raise PermissionError(
                    f"Unsupported execution type: "
                    f"{definition.execution_type}"
                )

            if definition.requires_approval:
                raise PermissionError(
                    f"Tool requires approval: {tool_name}"
                )

            arguments = _validate_arguments(
                tool_name,
                arguments,
                definition.parameters,
            )

            # Count actual direct execution attempts.
            execution_attempts += 1

            result = registry.execute(tool_name, arguments)

            if tool_name == "knowledge_search":
                if not isinstance(result, list):
                    raise TypeError(
                        "Knowledge search must return a list."
                    )

                knowledge.extend(result)

            results.append({
                "tool": tool_name,
                "status": "success",
                "result": result,
            })

        except Exception as exc:
            logger.exception(
                "Tool execution failed: %s",
                tool_name,
            )

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
