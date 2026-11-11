
from unittest.mock import patch

from app.agent.nodes.tool_selector import (
    tool_selector_node,
    _get_available_catalog,
)
from app.models.tool_selection import (
    ToolCall,
    ToolSelectionResult,
)


MOCK_CATALOG = [
    {
        "name": "knowledge_search",
        "description": "Search internal knowledge.",
        "category": "knowledge",
        "execution_type": "direct",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "web_search",
        "description": "Search the web.",
        "category": "web",
        "execution_type": "direct",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "sentinel_investigation",
        "description": "Investigate Sentinel.",
        "category": "sentinel",
        "execution_type": "graph",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]


def test_sentinel_removed_when_budget_exhausted():
    state = {
        "investigation_attempts": 3,
        "max_investigation_steps": 3,
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
    }

    available, budget = _get_available_catalog(
        state,
        MOCK_CATALOG,
    )

    names = [tool["name"] for tool in available]

    assert "sentinel_investigation" not in names
    assert "knowledge_search" in names
    assert "web_search" in names
    assert budget["sentinel_budget_available"] is False

    print("Sentinel budget filtering passed.")


def test_sentinel_available_within_budget():
    state = {
        "investigation_attempts": 1,
        "max_investigation_steps": 3,
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
    }

    available, budget = _get_available_catalog(
        state,
        MOCK_CATALOG,
    )

    names = [tool["name"] for tool in available]

    assert "sentinel_investigation" in names
    assert budget["sentinel_budget_available"] is True

    print("Sentinel available within budget passed.")


@patch(
    "app.agent.nodes.tool_selector.get_tool_catalog_for_llm",
    return_value=MOCK_CATALOG,
)
@patch(
    "app.agent.nodes.tool_selector.LLMClient.invoke_structured"
)
def test_selector_chooses_alternative_after_sentinel_budget(
    mock_invoke,
    mock_catalog,
):
    mock_invoke.return_value = ToolSelectionResult(
        reasoning="Sentinel budget exhausted. Use internal knowledge.",
        tool_calls=[
            ToolCall(
                tool_name="knowledge_search",
                arguments={"query": "Sentinel ingestion troubleshooting"},
                reason="Retrieve relevant troubleshooting documentation.",
            )
        ],
        investigation_complete=False,
        completion_reason="",
    )

    state = {
        "alert": "Sentinel ingestion failure",
        "siem": "Microsoft Sentinel",
        "plan": "Investigate ingestion failure.",
        "finding": "",
        "knowledge": [],
        "evidence": [],
        "tool_results": [],
        "tool_errors": [],
        "investigation_history": [],
        "next_investigation_reason": "Find alternative evidence.",
        "investigation_status": "failed",
        "investigation_error": "Sentinel investigation budget exhausted.",
        "investigation_attempts": 3,
        "max_investigation_steps": 3,
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
    }

    result = tool_selector_node(state)

    assert result["selected_tools"] == ["knowledge_search"]
    assert result["tool_calls"][0]["arguments"]["query"]
    assert "sentinel_investigation" not in result["available_tools"]
    assert result["execution_complete"] is False

    # Verify that the LLM received the filtered catalog.
    prompt = mock_invoke.call_args.args[0]
    assert "SENTINEL BUDGET AVAILABLE:\nFalse" in prompt

    print("Alternative tool selection passed.")


if __name__ == "__main__":
    test_sentinel_removed_when_budget_exhausted()
    test_sentinel_available_within_budget()
    test_selector_chooses_alternative_after_sentinel_budget()

    print("All tool selector tests passed.")
