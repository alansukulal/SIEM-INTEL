
from unittest.mock import patch

from app.agent.nodes.tool_executor import tool_executor_node


def run_test():
    state = {
        "knowledge": [],
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
        "tool_results": [],
        "tool_errors": [],
        "tool_calls": [
            {
                "tool_name": "knowledge_search",
                "arguments": {"query": "Sentinel runbook"},
                "reason": "Find internal guidance",
            },
            {
                "tool_name": "web_search",
                "arguments": {"query": "Microsoft Sentinel API failures"},
                "reason": "Find external documentation",
            },
            {
                "tool_name": "web_scrape",
                "arguments": {"url": "https://learn.microsoft.com/"},
                "reason": "Read Microsoft documentation",
            },
            {
                "tool_name": "sentinel_investigation",
                "arguments": {},
                "reason": "Investigate live Sentinel evidence",
            },
        ],
    }

    with patch(
        "app.agent.nodes.tool_executor.build_tool_registry"
    ) as mock_registry_builder:

        registry = mock_registry_builder.return_value

        def get_definition(name):
            from app.tools.register import build_tool_registry
            return build_tool_registry().get_definition(name)

        registry.get_definition.side_effect = get_definition

        registry.execute.side_effect = [
            [{"content": "Internal runbook"}],
            {"results": [{"title": "Microsoft documentation"}]},
            {"url": "https://learn.microsoft.com/", "content": "Documentation"},
        ]

        result = tool_executor_node(state)

    assert len(result["tool_results"]) == 3
    assert len(result["tool_errors"]) == 0
    assert result["tool_execution_attempts"] == 3

    assert result["pending_capabilities"] == [
        "sentinel_investigation"
    ]

    assert len(result["knowledge"]) == 1

    print("Knowledge search execution passed.")
    print("Web search execution passed.")
    print("Web scrape execution passed.")
    print("Sentinel graph routing passed.")
    print("All tool executor tests passed.")


if __name__ == "__main__":
    run_test()
