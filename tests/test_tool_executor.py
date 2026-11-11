from unittest.mock import MagicMock, patch

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
        "app.agent.nodes.tool_executor.build_tool_registry"
    ) as mock_factory:

        mock_registry = mock_factory.return_value

        mock_definition = MagicMock()
        mock_definition.enabled = True
        mock_definition.execution_type = "direct"
        mock_definition.requires_approval = False

        mock_definition.parameters = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "source_type": {
                    "type": ["string", "null"],
                    "enum": ["runbook", "table_schema", None],
                },
                "limit": {"type": "integer"},
            },
            "required": ["query"],
            "additionalProperties": False,
        }

        mock_registry.get_definition.return_value = mock_definition
        mock_registry.execute.return_value = [
            {"title": "Sentinel runbook"}
        ]

        result = tool_executor_node(state)

        mock_registry.execute.assert_called_once()
        assert len(result["knowledge"]) == 1