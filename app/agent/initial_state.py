
from typing import Any


def create_initial_state(
    alert: str,
    siem: str,
    tenant_id: str = "local-dev",
) -> dict[str, Any]:
    return {
        # Request context
        "tenant_id": tenant_id,
        "alert": alert.strip(),
        "siem": siem.strip(),

        # Planning and evidence
        "plan": "",
        "query": "",
        "evidence": [],
        "finding": "",
        "knowledge": [],

        # Evaluation
        "needs_more_investigation": False,
        "next_investigation_reason": "",
        "investigation_outcome": "pending",

        # KQL validation
        "kql_valid": False,
        "kql_validation_errors": [],
        "kql_attempts": 0,
        "kql_reason": "",
        "kql_correction_attempts": 0,

        # Investigation budget
        "investigation_attempts": 0,
        "max_investigation_steps": 5,

        # Tool execution budget
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,

        # Investigation status
        "investigation_status": "pending",
        "investigation_error": "",
        "investigation_history": [],

        # Dynamic capabilities
        "available_tools": [],
        "selected_tools": [],
        "pending_capabilities": [],
        "current_action": "",

        # Tool execution
        "tool_calls": [],
        "tool_results": [],
        "tool_errors": [],
        "tool_call_history": [],

        # Approval management
        "pending_approval": False,
        "approval_request": None,
        "approved_actions": [],

        # Completion tracking
        "execution_complete": False,
        "tool_batch_complete": False,
    }
