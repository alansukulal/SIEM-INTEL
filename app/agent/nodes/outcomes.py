
import logging

from app.agent.state import InvestigationState

logger = logging.getLogger(__name__)


def _get_text(value: object) -> str:
    """Safely normalize optional state values to strings."""
    return value.strip() if isinstance(value, str) else ""


def mark_completed_node(state: InvestigationState) -> dict:
    """Mark an evidence-supported investigation as completed."""

    logger.info("Investigation completed successfully.")

    return {
        "investigation_outcome": "completed",
        "investigation_error": "",
    }


def mark_incomplete_node(state: InvestigationState) -> dict:
    """
    Mark an unresolved investigation incomplete without
    discarding its finding, evidence, or history.
    """

    reason = (
        _get_text(state.get("investigation_error"))
        or _get_text(state.get("next_investigation_reason"))
        or (
            "The investigation stopped without sufficient "
            "evidence to answer the original objective."
        )
    )

    logger.warning(
        "Investigation marked incomplete: %s",
        reason,
    )

    return {
        "investigation_outcome": "incomplete",
        "investigation_error": reason,
        "investigation_complete": False,
        "needs_more_investigation": False,
    }


def mark_failed_node(state: InvestigationState) -> dict:
    """Mark an investigation that encountered an unrecoverable error."""

    reason = (
        _get_text(state.get("investigation_error"))
        or "The investigation encountered an unrecoverable error."
    )

    logger.error(
        "Investigation marked failed: %s",
        reason,
    )

    return {
        "investigation_outcome": "failed",
        "investigation_error": reason,
        "investigation_complete": False,
        "needs_more_investigation": False,
    }


def mark_kql_exhausted_node(state: InvestigationState) -> dict:
    """
    Record KQL generation/validation exhaustion.

    This node preserves existing evidence and history.
    The evaluator can still decide whether the overall
    investigation objective was answered by other evidence.
    """

    history = list(
        state.get("investigation_history") or []
    )
    previous_evidence = list(
        state.get("evidence") or []
    )

    reason = (
        _get_text(state.get("kql_reason"))
        or "The agent could not generate a safe, usable KQL query."
    )

    query = _get_text(state.get("query"))
    previous_finding = _get_text(state.get("finding"))

    history.append({
        "query": query,
        "evidence": [],
        "status": "kql_exhausted",
        "error": reason,
        "attempt": state.get("investigation_attempts", 0),
    })

    if previous_finding:
        finding = (
            f"{previous_finding}\n\n"
            "The next Sentinel investigation step could not proceed. "
            f"KQL generation or validation was exhausted. Reason: {reason}"
        )
    else:
        finding = (
            "The Sentinel investigation could not proceed because "
            "KQL generation or validation was exhausted. "
            f"Reason: {reason}"
        )

    logger.warning(
        "KQL investigation exhausted. Reason: %s",
        reason,
    )

    return {
        "investigation_outcome": "kql_exhausted",
        "investigation_status": "kql_exhausted",
        "investigation_error": reason,
        "finding": finding,
        "evidence": previous_evidence,
        "investigation_history": history,
    }
