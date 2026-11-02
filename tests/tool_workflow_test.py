
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from app.agent.nodes.tool_executor import tool_executor_node


def test_knowledge_search_workflow():
    """Test knowledge search execution through the tool executor."""

    mock_registry = MagicMock()

    mock_registry.list_tools.return_value = [
        "knowledge_search",
        "sentinel_investigation",
    ]

    mock_registry.get_definition.return_value = SimpleNamespace(
        name="knowledge_search",
        enabled=True,
        execution_type="direct",
        requires_approval=False,
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "source_type": {
                    "type": ["string", "null"],
                    "enum": ["runbook", "table_schema", None],
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    )

    mock_registry.execute.return_value = [
        {
            "content": "Log outage troubleshooting runbook",
            "source": "runbook",
        }
    ]

    state = {
        "alert": "Logs stopped arriving in Sentinel",
        "siem": "Microsoft Sentinel",
        "knowledge": [],
        "tool_calls": [
            {
                "tool_name": "knowledge_search",
                "arguments": {
                    "query": "log outage checks",
                    "source_type": "runbook",
                    "limit": 5,
                },
                "reason": "Retrieve the log outage troubleshooting runbook.",
            }
        ],
        "tool_results": [],
        "tool_errors": [],
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
        "pending_capabilities": [],
    }

    with patch(
        "app.agent.nodes.tool_executor.build_tool_registry",
        return_value=mock_registry,
    ):
        result = tool_executor_node(state)

    assert len(result["knowledge"]) == 1
    assert result["knowledge"][0]["source"] == "runbook"

    assert len(result["tool_results"]) == 1
    assert result["tool_results"][0]["status"] == "success"

    assert result["tool_errors"] == []
    assert result["tool_execution_attempts"] == 1
    assert result["tool_batch_complete"] is True

    # The executor must not mark the entire investigation complete.
    assert "execution_complete" not in result

    mock_registry.execute.assert_called_once_with(
        "knowledge_search",
        {
            "query": "log outage checks",
            "source_type": "runbook",
            "limit": 5,
        },
    )

    print("Knowledge search workflow passed.")


if __name__ == "__main__":
    test_knowledge_search_workflow()
    print("All workflow tests passed.")
