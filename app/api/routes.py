from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.graph import build_investigation_graph

router = APIRouter(prefix="/api/v1")

graph = build_investigation_graph()


class InvestigationRequest(BaseModel):
    alert: str
    siem: str


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SIEM-INTEL",
    }


@router.post("/investigations")
def create_investigation(request: InvestigationRequest):

    initial_state = {
        "alert": request.alert,
        "siem": request.siem,
        "plan": "",
        "query": "",
        "evidence": [],
        "finding": "",
        "needs_more_investigation": False,
        "investigation_attempts": 0,
    }

    result = graph.invoke(initial_state)

    return {
        "alert": result["alert"],
        "siem": result["siem"],
        "plan": result["plan"],
        "query": result["query"],
        "evidence": result["evidence"],
        "finding": result["finding"],
    }