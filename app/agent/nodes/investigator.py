
import logging
from typing import Any

from app.agent.state import InvestigationState
from app.tools.sentinel import SentinelClient, SentinelQueryError

logger = logging.getLogger(__name__)


def investigator_node(state: InvestigationState) -> dict:
    """
    Execute a validated KQL query against Microsoft Sentinel.

    Preserves previous evidence and investigation history when
    an execution fails.
    """

    history = list(state.get("investigation_history") or [])
    previous_evidence = list(state.get("evidence") or [])

    query = (state.get("query") or "").strip()
    attempts = state.get("investigation_attempts", 0)

    # A missing query is recorded but does not count as an
    # actual Sentinel execution attempt.
    if not query:
        error_message = "No KQL query was provided for execution."

        history.append({
            "query": "",
            "evidence": [],
            "status": "failed",
            "error": error_message,
        })

        logger.warning(error_message)

        return {
            "evidence": previous_evidence,
            "investigation_history": history,
            "investigation_status": "failed",
            "investigation_error": error_message,
        }

    try:
        sentinel = SentinelClient()
        results = sentinel.run_query(query)

        history.append({
            "query": query,
            "evidence": results,
            "status": "success",
            "error": "",
            "attempt": attempts + 1,
        })

        logger.info(
            "Sentinel investigation succeeded. Attempt=%s, Evidence=%s",
            attempts + 1,
            len(results) if results is not None else 0,
        )

        return {
            "evidence": results,
            "investigation_history": history,
            "investigation_attempts": attempts + 1,
            "investigation_status": "success",
            "investigation_error": "",
        }

    except SentinelQueryError:
        logger.exception(
            "Sentinel query execution failed. Attempt=%s",
            attempts + 1,
        )

        error_message = (
            "Sentinel query execution failed. "
            "Check server logs for diagnostic details."
        )

    except Exception:
        logger.exception(
            "Unexpected error during Sentinel investigation. Attempt=%s",
            attempts + 1,
        )

        error_message = (
            "An unexpected error occurred during Sentinel investigation. "
            "Check server logs for diagnostic details."
        )

    # Both failure paths preserve previous successful evidence.
    history.append({
        "query": query,
        "evidence": [],
        "status": "failed",
        "error": error_message,
        "attempt": attempts + 1,
    })

    return {
        "evidence": previous_evidence,
        "investigation_history": history,
        "investigation_attempts": attempts + 1,
        "investigation_status": "failed",
        "investigation_error": error_message,
    }
