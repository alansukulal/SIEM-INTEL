
from app.agent.state import InvestigationState


def route_after_tool_execution(state: InvestigationState) -> str:
    """
    Route the workflow based on the selected capability.
    """

    selected_tools = state.get("selected_tools", [])

    # Sentinel must use the existing KQL investigation pipeline.
    if "sentinel_investigation" in selected_tools:
        return "sentinel_investigation"

    # If knowledge was retrieved, allow the selector to decide
    # whether another capability is required.
    if state.get("tool_errors"):
        return "tool_error"

    return "select_again"
