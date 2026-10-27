
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
        "kql_correction_attempts": 0,
        "knowledge": [],
        "tenant_id": "local-dev",
        "max_investigation_steps": 3,
        "investigation_outcome": "pending",
        "investigation_history": [],
    }

    result = graph.invoke(initial_state)

    
    finding = result.get("finding", "")
    outcome = result.get("investigation_outcome", "unknown")
    history = result.get("investigation_history", [])
    evidence = result.get("evidence", [])

    # Build explicit limitations from the actual investigation outcome.
    limitations = []

    if outcome == "incomplete":
        limitations.append(
            "The maximum investigation step limit was reached."
        )
    elif outcome == "failed":
        limitations.append(
            result.get("investigation_error")
            or "Sentinel query execution failed."
        )
    elif outcome == "kql_exhausted":
        limitations.append(
            result.get("kql_reason")
            or "The agent could not generate a usable KQL query."
        )

    return {
        "alert": result.get("alert", request.alert),
        "siem": result.get("siem", request.siem),
        "plan": result.get("plan", ""),
        "investigation_outcome": outcome,
        "finding": finding,
        "investigation_status": result.get(
            "investigation_status", "unknown"
        ),
        "investigation_error": result.get("investigation_error", ""),
        "investigation_attempts": result.get(
            "investigation_attempts", 0
        ),
        "max_investigation_steps": result.get(
            "max_investigation_steps", 10
        ),
        "kql_attempts": result.get("kql_attempts", 0),
        "kql_correction_attempts": result.get(
            "kql_correction_attempts", 0
        ),
        "query": result.get("query", ""),
        "kql_reason": result.get("kql_reason", ""),
        "kql_valid": result.get("kql_valid", False),
        "kql_validation_errors": result.get(
            "kql_validation_errors", []
        ),
        "evidence": evidence,
        "investigation_history": history,
        "needs_more_investigation": result.get(
            "needs_more_investigation", False
        ),
        "next_investigation_reason": result.get(
            "next_investigation_reason", ""
        ),
        "report": {
            "outcome": outcome,
            "summary": finding,
            "queries_executed": [
                {
                    "query": item.get("query", ""),
                    "status": item.get("status", "unknown"),
                    "evidence_count": len(
                        item.get("evidence", [])
                    ),
                }
                for item in history
            ],
            "evidence_from_latest_query": evidence,
            "limitations": limitations,
        },
    }
