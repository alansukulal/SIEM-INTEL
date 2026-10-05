from app.agent.state import InvestigationState
from app.tools.sentinel import SentinelClient


def investigator_node(state: InvestigationState) -> dict:
    plan = state["plan"]

    sentinel = SentinelClient()

    kql = """
    Heartbeat
    | take 10
    """

    results = sentinel.run_query(kql)


    return {
        "query":kql.strip(),
        "evidence": results,
    }