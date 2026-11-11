
from unittest.mock import patch
from app.agent.nodes.evaluator import evaluator_node
from app.models.evaluation import EvaluationResult


def test_evaluator_receives_historical_successful_evidence():
    state = {
        "alert": "Investigate unusual StorageBlobLogs ingestion.",
        "siem": "Microsoft Sentinel",
        "plan": '{"objective": "Investigate ingestion activity"}',
        "query": "StorageBlobLogs | take 10",
        "evidence": [],
        "finding": "",
        "investigation_status": "failed",
        "investigation_error": "Latest query failed.",
        "investigation_attempts": 2,
        "max_investigation_steps": 3,
        "tool_execution_attempts": 1,
        "max_tool_execution_attempts": 10,
        "investigation_history": [
            {
                "query": "StorageBlobLogs | take 10",
                "status": "success",
                "evidence": [
                    {
                        "Account": "storage-account-1",
                        "Count": 5000,
                    }
                ],
                "error": "",
            },
            {
                "query": "StorageBlobLogs | where TimeGenerated > ago(1h)",
                "status": "failed",
                "evidence": [],
                "error": "Sentinel query failed.",
            },
        ],
        "tool_results": [],
        "tool_errors": [],
        "tool_calls": [],
    }

    captured_prompt = {}

    def mock_invoke_structured(prompt, model):
        captured_prompt["value"] = prompt

        return EvaluationResult(
            finding="Historical evidence exists, but the latest query failed.",
            investigation_complete=False,
            needs_more_investigation=True,
            next_investigation_reason="Verify the latest ingestion activity.",
        )

    with patch(
        "app.agent.nodes.evaluator.LLMClient.invoke_structured",
        side_effect=mock_invoke_structured,
    ):
        result = evaluator_node(state)

    prompt = captured_prompt["value"]

    assert "storage-account-1" in prompt
    assert "5000" in prompt
    assert "Sentinel query failed." in prompt

    assert result["investigation_complete"] is False
    assert result["needs_more_investigation"] is True

    print("SUCCESS: Historical successful evidence reached evaluator.")
    print("SUCCESS: Failed query was not treated as successful evidence.")
    print("SUCCESS: Evaluator requested further investigation.")


if __name__ == "__main__":
    test_evaluator_receives_historical_successful_evidence()
