from unittest.mock import MagicMock, patch

from app.agent.nodes.tool_executor import tool_executor_node


def test_invalid_tool_rejected():
    state = {
        "tool_calls": [
            {
                "tool_name": "unknown_tool",
                "arguments": {},
            }
        ],
        "knowledge": [],
        "tool_results": [],
        "tool_errors": [],
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
    }

    with patch(
        "app.agent.nodes.tool_executor.build_tool_registry"
    ) as mock_factory:
        registry = mock_factory.return_value
        registry.get_definition.side_effect = ValueError(
            "Unknown tool"
        )

        result = tool_executor_node(state)

        assert len(result["tool_errors"]) == 1
        assert result["tool_errors"][0]["tool"] == "unknown_tool"
        registry.execute.assert_not_called()