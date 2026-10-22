from app.agent.state import InvestigationState
from app.tools.sentinel import SentinelClient


def investigator_node(state: InvestigationState) -> dict:
    kql = state["query"]

    sentinel = SentinelClient()

    results = sentinel.run_query(kql)

    return {
        "evidence": results,
        "investigation_attempts": state["investigation_attempts"] + 1,
    }