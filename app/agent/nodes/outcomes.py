
from app.agent.state import InvestigationState


def mark_completed_node(state: InvestigationState) -> dict:
    return {
        "investigation_outcome": "completed",
    }


def mark_incomplete_node(state: InvestigationState) -> dict:
    return {
        "investigation_outcome": "incomplete",
    }


def mark_failed_node(state: InvestigationState) -> dict:
    return {
        "investigation_outcome": "failed",
    }



def mark_kql_exhausted_node(state: InvestigationState) -> dict:
    reason = state.get("kql_reason", "").strip()

    if not reason:
        reason = (
            "The agent could not generate a safe, usable KQL query."
        )

    return {
        "investigation_outcome": "kql_exhausted",
        "finding": (
            "Investigation stopped before the next query could execute. "
            f"Reason: {reason}"
        ),
    }
