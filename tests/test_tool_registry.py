
from app.tools.register import build_tool_registry


def test_tool_registry():
    registry = build_tool_registry()

    available_tools = registry.list_tools()

    assert "knowledge_search" in available_tools
    assert "sentinel_query" in available_tools

    assert len(available_tools) == 2

    print("Registered tools:", available_tools)
    print("Tool registry test passed!")


if __name__ == "__main__":
    test_tool_registry()
