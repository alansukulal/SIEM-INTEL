
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent.graph import build_investigation_graph

router = APIRouter(prefix="/api/v1")

graph = build_investigation_graph()


class InvestigationRequest(BaseModel):
    alert: str = Field(min_length=1, max_length=5000)
    siem: str = Field(min_length=1, max_length=100)


@router.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SIEM-INTEL",
    }


@router.post("/investigations")
def create_investigation(request: InvestigationRequest):
    initial_state = {
        "alert": request.alert.strip(),
        "siem": request.siem.strip(),
        "plan": "",
        "query": "",
        "evidence": [],
        "finding": "",
        "needs_more_investigation": False,
        "next_investigation_reason": "",
        "investigation_attempts": 0,
        "investigation_status": "pending",
        "investigation_error": "",
        "kql_valid": False,
        "kql_validation_errors": [],
        "kql_attempts": 0,
        "kql_reason": "",
        "knowledge": [],
    }

    result = graph.invoke(initial_state)

    return {
        "alert": result.get("alert", request.alert),
        "siem": result.get("siem", request.siem),
        "plan": result.get("plan", ""),
        "query": result.get("query", ""),
        "kql_reason": result.get("kql_reason", ""),
        "kql_valid": result.get("kql_valid", False),
        "kql_validation_errors": result.get(
            "kql_validation_errors", []
        ),
        "evidence": result.get("evidence", []),
        "finding": result.get("finding", ""),
        "investigation_status": result.get(
            "investigation_status", "unknown"
        ),
        "investigation_error": result.get("investigation_error", ""),
        "investigation_attempts": result.get(
            "investigation_attempts", 0
        ),
        "kql_attempts": result.get("kql_attempts", 0),
        "needs_more_investigation": result.get(
            "needs_more_investigation", False
        ),
        "next_investigation_reason": result.get(
            "next_investigation_reason", ""
        ),
    }
