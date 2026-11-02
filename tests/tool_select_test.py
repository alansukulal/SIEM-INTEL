
from app.models.tool_selection import (
    ToolCall,
    ToolSelectionResult,
)


def test_knowledge_selection():
    result = ToolSelectionResult(
        reasoning="Need relevant runbook information.",
        tool_calls=[
            ToolCall(
                tool_name="knowledge_search",
                arguments={
                    "query": "Sentinel log outage",
                    "source_type": "runbook",
                    "limit": 3,
                },
                reason="Retrieve outage investigation guidance.",
            )
        ],
    )

    assert result.tool_calls[0].tool_name == "knowledge_search"


def test_sentinel_selection():
    result = ToolSelectionResult(
        reasoning="A live SIEM investigation is required.",
        tool_calls=[
            ToolCall(
                tool_name="sentinel_investigation",
                arguments={},
                reason="Investigate log ingestion.",
            )
        ],
    )

    assert result.tool_calls[0].tool_name == "sentinel_investigation"


def test_invalid_tool_rejected():
    try:
        ToolCall(
            tool_name="unknown_tool",
            arguments={},
            reason="Invalid tool",
        )
    except Exception:
        return

    raise AssertionError("Invalid tool should have been rejected.")


if __name__ == "__main__":
    test_knowledge_selection()
    test_sentinel_selection()
    test_invalid_tool_rejected()

    print("All tool selection model tests passed.")
