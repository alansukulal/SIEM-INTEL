
from unittest.mock import MagicMock, patch

from app.agent.nodes.evaluator import evaluator_node
from app.models.evaluation import EvaluationResult


def make_state(**overrides):
    state = {
        "tenant_id": "test-tenant",
        "alert": "Investigate a sudden increase in StorageBlobLogs ingestion.",
        "siem": "Microsoft Sentinel",
        "plan": '{"objective": "Identify the source of the ingestion spike."}',
        "query": "StorageBlobLogs | summarize count()",
        "evidence": [{"Source": "storage-account-01", "Count": 1000}],
        "finding": "",
        "knowledge": [],
        "investigation_history": [],
        "investigation_attempts": 1,
        "max_investigation_steps": 3,
        "tool_execution_attempts": 1,
        "max_tool_execution_attempts": 10,
        "investigation_status": "success",
        "investigation_error": "",
        "tool_results": [],
        "tool_errors": [],
        "tool_calls": [],
    }
    state.update(overrides)
    return state


def make_result(**overrides):
    result = {
        "finding": "Storage account activity was identified.",
        "evidence_sufficient": True,
        "evidence_assessment": "The collected telemetry identifies the source.",
        "missing_evidence": [],
        "investigation_complete": True,
        "needs_more_investigation": False,
        "next_investigation_reason": "",
    }
    result.update(overrides)
    return EvaluationResult(**result)


def run_evaluator(state, result):
    with patch(
        "app.agent.nodes.evaluator.LLMClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.invoke_structured.return_value = result
        mock_client_class.return_value = mock_client

        return evaluator_node(state)


def test_sufficient_evidence_allows_completion():
    state = make_state()

    result = make_result()

    output = run_evaluator(state, result)

    assert output["evidence_sufficient"] is True
    assert output["investigation_complete"] is True
    assert output["needs_more_investigation"] is False

    print("SUCCESS: Sufficient evidence allows completion.")


def test_insufficient_evidence_rejects_completion():
    state = make_state(
        evidence=[],
        knowledge=[{"content": "Generic Microsoft documentation"}],
    )

    result = make_result(
        evidence_sufficient=False,
        evidence_assessment="Customer-specific telemetry is missing.",
        missing_evidence=["Current customer ingestion telemetry"],
        investigation_complete=True,
        needs_more_investigation=False,
    )

    output = run_evaluator(state, result)

    assert output["evidence_sufficient"] is False
    assert output["investigation_complete"] is False
    assert output["missing_evidence"] == [
        "Current customer ingestion telemetry"
    ]

    print("SUCCESS: Insufficient evidence rejects completion.")


def test_missing_evidence_requests_further_investigation():
    state = make_state(
        evidence=[],
        knowledge=[],
        tool_results=[],
    )

    result = make_result(
        evidence_sufficient=False,
        evidence_assessment="Current ingestion telemetry is missing.",
        missing_evidence=["Current ingestion telemetry"],
        investigation_complete=False,
        needs_more_investigation=True,
        next_investigation_reason=(
            "Retrieve current ingestion metrics from Sentinel."
        ),
    )

    output = run_evaluator(state, result)

    assert output["investigation_complete"] is False
    assert output["needs_more_investigation"] is True
    assert output["next_investigation_reason"] != ""

    print("SUCCESS: Missing evidence requests further investigation.")


def test_conflicting_completion_and_continuation_is_rejected():
    state = make_state()

    result = make_result(
        evidence_sufficient=True,
        investigation_complete=True,
        needs_more_investigation=True,
        next_investigation_reason="Verify another data source.",
    )

    output = run_evaluator(state, result)

    assert output["investigation_complete"] is False
    assert output["needs_more_investigation"] is True

    print("SUCCESS: Conflicting completion decision is rejected.")


if __name__ == "__main__":
    test_sufficient_evidence_allows_completion()
    test_insufficient_evidence_rejects_completion()
    test_missing_evidence_requests_further_investigation()
    test_conflicting_completion_and_continuation_is_rejected()

    print("\nALL EVIDENCE SUFFICIENCY TESTS PASSED.")
