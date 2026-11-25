
from typing import Any


def create_initial_state(
    alert: str,
    siem: str,
    tenant_id: str,
    conversation_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        # Request context
        "tenant_id": tenant_id,
        "alert": alert.strip(),
        "siem": siem.strip(),

        # Conversation context
        "conversation_history": conversation_history or [],

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
        "evidence_sufficient": False,
        "evidence_assessment": "",
        "missing_evidence": [],
        "investigation_complete": False,


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

def create_follow_up_input(
    alert: str,
    conversation_history: list[dict[str, str]],
) -> dict[str, Any]:

    return {
        # New user message and updated conversation context
        "alert": alert.strip(),
        "conversation_history": conversation_history,

        # Reset current investigation turn
        "plan": "",
        "query": "",
        "finding": "",
        "knowledge": [],

        # Evaluation
        "needs_more_investigation": False,
        "next_investigation_reason": "",
        "investigation_outcome": "pending",
        "evidence_sufficient": False,
        "evidence_assessment": "",
        "missing_evidence": [],
        "investigation_complete": False,

        # KQL validation
        "kql_valid": False,
        "kql_validation_errors": [],
        "kql_attempts": 0,
        "kql_reason": "",
        "kql_correction_attempts": 0,

        # Investigation budgets
        "investigation_attempts": 0,
        "max_investigation_steps": 5,
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,

        # Current investigation status
        "investigation_status": "pending",
        "investigation_error": "",

        # Preserve investigation_history from checkpoint.
        # Reset current tool execution data.
        "available_tools": [],
        "selected_tools": [],
        "pending_capabilities": [],
        "current_action": "",
        "tool_calls": [],
        "tool_results": [],
        "tool_errors": [],
        "tool_call_history": [],

        # Completion tracking
        "execution_complete": False,
        "tool_batch_complete": False,
    }