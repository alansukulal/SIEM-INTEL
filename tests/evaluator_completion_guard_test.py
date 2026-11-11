
from unittest.mock import patch

from app.agent.nodes.evaluator import evaluator_node
from app.models.evaluation import EvaluationResult


def base_state():
    return {
        "alert": "Investigate unusual storage ingestion.",
        "siem": "Microsoft Sentinel",
        "plan": '{"objective": "Investigate storage ingestion"}',
        "query": "",
        "evidence": [],
        "finding": "",
        "knowledge": [],
        "investigation_status": "failed",
        "investigation_error": "Sentinel unavailable.",
        "investigation_attempts": 1,
        "max_investigation_steps": 3,
        "tool_execution_attempts": 1,
        "max_tool_execution_attempts": 10,
        "investigation_history": [],
        "tool_results": [],
        "tool_errors": [],
        "tool_calls": [],
    }


def mock_completed_evaluation(prompt, model):
    return EvaluationResult(
        finding="Historical Sentinel evidence supports the finding.",
        investigation_complete=True,
        needs_more_investigation=False,
        next_investigation_reason="",
        evidence_sufficient=True,
        evidence_assessment=(
            "Successful historical Sentinel evidence supports the finding."
        ),
        missing_evidence=[],
    )

def test_completion_rejected_without_evidence():
    state = base_state()

    with patch(
        "app.agent.nodes.evaluator.LLMClient.invoke_structured",
        side_effect=mock_completed_evaluation,
    ):
        result = evaluator_node(state)

    assert result["investigation_complete"] is False

    print("SUCCESS: Unsupported completion was rejected.")


def test_completion_allowed_with_historical_evidence():
    state = base_state()

    state["investigation_history"] = [
        {
            "query": "StorageBlobLogs | take 10",
            "status": "success",
            "evidence": [
                {"Account": "storage-account-1", "Count": 5000}
            ],
            "error": "",
        },
        {
            "query": "StorageBlobLogs | where TimeGenerated > ago(1h)",
            "status": "failed",
            "evidence": [],
            "error": "Sentinel query failed.",
        },
    ]

    with patch(
        "app.agent.nodes.evaluator.LLMClient.invoke_structured",
        side_effect=mock_completed_evaluation,
    ):
        result = evaluator_node(state)

    assert result["investigation_complete"] is True

    print("SUCCESS: Historical successful evidence was recognized.")


if __name__ == "__main__":
    test_completion_rejected_without_evidence()
    test_completion_allowed_with_historical_evidence()
