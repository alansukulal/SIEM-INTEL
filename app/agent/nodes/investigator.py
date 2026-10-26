import logging

from app.agent.state import InvestigationState
from app.tools.sentinel import SentinelClient, SentinelQueryError

logger = logging.getLogger(__name__)


def investigator_node(state: InvestigationState) -> dict:
    try:
        sentinel = SentinelClient()
        results = sentinel.run_query(state["query"])

        return {
            "evidence": results,
            "investigation_attempts": (
                state.get("investigation_attempts", 0) + 1
            ),
            "investigation_status": "success",
            "investigation_error": "",
        }

    except SentinelQueryError:
        logger.exception("Sentinel query execution failed")

        return {
            "evidence": [],
            "investigation_attempts": (
                state.get("investigation_attempts", 0) + 1
            ),
            "investigation_status": "failed",
            "investigation_error": (
                "Sentinel query execution failed. "
                "Check server logs for diagnostic details."
            ),
        }