# Agent memmory section for the run
from typing import Any, TypedDict


class InvestigationState(TypedDict):
    alert: str
    siem: str
    plan: str
    query: str
    evidence: list[dict[str, Any]]
    finding: str
    needs_more_investigation: bool
    investigation_attempts:int
    kql_valid: bool
    kql_validation_errors: list[str]
    kql_attempts:int
    kql_reason:str
    knowledge: list[dict]
