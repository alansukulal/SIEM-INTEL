
from typing import Any, TypedDict


class InvestigationState(TypedDict):
    # Request and tenant context
    tenant_id: str
    alert: str
    siem: str

    # Investigation planning and evidence
    plan: str
    query: str
    evidence: list[dict[str, Any]]
    finding: str
    knowledge: list[dict[str, Any]]

    # Evaluation and follow-up
    needs_more_investigation: bool
    next_investigation_reason: str
    investigation_outcome: str

    # Query validation and correction tracking
    kql_valid: bool
    kql_validation_errors: list[str]
    kql_attempts: int
    kql_reason: str
    kql_correction_attempts: int

    # Investigation budget and progress
    investigation_attempts: int
    max_investigation_steps: int

    # Execution status and error information
    investigation_status: str
    investigation_error: str
    investigation_history: list[dict[str, Any]]
