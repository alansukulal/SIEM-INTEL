
import logging

from app.agent.state import InvestigationState
from app.tools.sentinel import SentinelClient, SentinelQueryError

logger = logging.getLogger(__name__)


def investigator_node(state: InvestigationState) -> dict:
    history = list(state.get("investigation_history", []))
    query = state.get("query", "").strip()

    if not query:
        return {
            "investigation_status": "failed",
            "investigation_error": "No KQL query was provided for execution.",
        }

    attempts = state.get("investigation_attempts", 0)

    try:
        sentinel = SentinelClient()
        results = sentinel.run_query(query)

        history.append(
            {
                "query": query,
                "evidence": results,
                "status": "success",
            }
        )

        return {
            "evidence": results,
            "investigation_history": history,
            "investigation_attempts": attempts + 1,
            "investigation_status": "success",
            "investigation_error": "",
        }

    except SentinelQueryError:
        logger.exception("Sentinel query execution failed")

        history.append(
            {
                "query": query,
                "evidence": [],
                "status": "failed",
            }
        )

        return {
            # Preserve evidence from the last successful query.
            "evidence": state.get("evidence", []),
            "investigation_history": history,
            "investigation_attempts": attempts + 1,
            "investigation_status": "failed",
            "investigation_error": (
                "Sentinel query execution failed. "
                "Check server logs for diagnostic details."
            ),
        }
