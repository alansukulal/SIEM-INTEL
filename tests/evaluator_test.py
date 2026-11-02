
from unittest.mock import patch

from app.agent.nodes.evaluator import evaluator_node
from app.models.evaluation import EvaluationResult


def test_evaluator_requests_more_investigation():

    mock_result = EvaluationResult(
        finding="SigninLogs ingestion has stopped.",
        needs_more_investigation=True,
        next_investigation_reason="Check connector authentication status.",
    )

    state = {
        "alert": "SigninLogs ingestion stopped",
        "siem": "Microsoft Sentinel",
        "plan": '{"objective": "Investigate ingestion outage"}',
        "query": "SigninLogs | take 10",
        "evidence": [],
        "investigation_status": "success",
        "investigation_history": [],
        "tool_results": [],
        "tool_errors": [],
        "tool_calls": [],
        "investigation_attempts": 1,
        "max_investigation_steps": 5,
    }

    with patch(
        "app.agent.nodes.evaluator.LLMClient"
    ) as mock_llm:

        mock_llm.return_value.invoke_structured.return_value = mock_result

        result = evaluator_node(state)

        assert result["needs_more_investigation"] is True
        assert result["next_investigation_reason"] == (
            "Check connector authentication status."
        )

        print("Evaluator follow-up test passed.")


def test_evaluator_completes_investigation():

    mock_result = EvaluationResult(
        finding="The ingestion issue has been resolved.",
        needs_more_investigation=False,
        next_investigation_reason="",
    )

    state = {
        "alert": "SigninLogs ingestion stopped",
        "siem": "Microsoft Sentinel",
        "plan": '{"objective": "Investigate ingestion outage"}',
        "query": "SigninLogs | take 10",
        "evidence": [],
        "investigation_status": "success",
        "investigation_history": [],
        "tool_results": [],
        "tool_errors": [],
        "tool_calls": [],
        "investigation_attempts": 1,
        "max_investigation_steps": 5,
    }

    with patch(
        "app.agent.nodes.evaluator.LLMClient"
    ) as mock_llm:

        mock_llm.return_value.invoke_structured.return_value = mock_result

        result = evaluator_node(state)

        assert result["needs_more_investigation"] is False
        assert result["next_investigation_reason"] == ""

        print("Evaluator completion test passed.")


if __name__ == "__main__":
    test_evaluator_requests_more_investigation()
    test_evaluator_completes_investigation()
    print("\nAll evaluator tests passed.")
