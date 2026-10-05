# Investigation Planner

from app.agent.state import InvestigationState


def planner_node(state: InvestigationState) -> dict:
    alert = state["alert"]
    siem = state["siem"]

    plan = (
        f"Investigate the alert '{alert}' "
        f"using the {siem} SIEM."
    )

    return {
        "plan": plan,
    }