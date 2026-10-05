from pydantic import BaseModel

from app.agent.graph import build_investigation_graph


class InvestigationInput(BaseModel):
    alert: str
    siem: str


def run_investigation(request: InvestigationInput) -> dict:
    graph = build_investigation_graph()

    initial_state = {
        "alert": request.alert,
        "siem": request.siem,
        "plan": "",
        "evidence": [],
        "finding": "",
    }

    result = graph.invoke(initial_state)

    return {
        "alert": result["alert"],
        "siem": result["siem"],
        "plan": result["plan"],
        "evidence": result["evidence"],
        "finding": result["finding"],
    }