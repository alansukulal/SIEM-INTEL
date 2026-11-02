from unittest.mock import patch

from app.agent.nodes.tool_executor import tool_executor_node


def test_knowledge_tool_execution():
    state = {
        "tool_calls": [
            {
                "tool_name": "knowledge_search",
                "arguments": {
                    "query": "Sentinel log outage",
                    "source_type": "runbook",
                    "limit": 2,
                },
            }
        ],
        "knowledge": [],
        "investigation_history": [],
        "tool_results": [],
        "tool_errors": [],
    }

    with patch(
        "app.agent.nodes.tool_executor.registry.execute"
    ) as mock_execute:
        pass