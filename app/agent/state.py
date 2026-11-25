
from typing import Any, TypedDict


class InvestigationState(TypedDict):
    # Request and tenant context
    tenant_id: str
    alert: str
    siem: str
    conversation_history: list[dict[str, str]]

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
    evidence_sufficient: bool
    evidence_assessment: str
    missing_evidence: list[str]

    # KQL validation and correction
    kql_valid: bool
    kql_validation_errors: list[str]
    kql_attempts: int
    kql_reason: str
    kql_correction_attempts: int

    # Investigation budget
    investigation_attempts: int
    max_investigation_steps: int

    # Dynamic tool execution budget
    tool_execution_attempts: int
    max_tool_execution_attempts: int

    # Investigation status
    investigation_status: str
    investigation_error: str
    investigation_history: list[dict[str, Any]]
    

    # Dynamic capabilities
    available_tools: list[str]
    selected_tools: list[str]
    pending_capabilities: list[str]
    current_action: str

    # Tool execution
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    tool_errors: list[dict[str, Any]]
    tool_call_history: list[dict[str, Any]]

    # Approval management
    pending_approval: bool
    approval_request: dict[str, Any] | None
    approved_actions: list[str]

    # Completion tracking
    execution_complete: bool
    tool_batch_complete: bool
    investigation_complete: bool

