# Agent memmory section for the run
from typing import Any, TypedDict


class InvestigationState(TypedDict):
    alert: str
    siem: str
    plan: str
    query:str
    evidence: list[dict[str, Any]]
    finding: str