import json
from unittest.mock import MagicMock, patch

from app.models.tool_definition import ToolDefinition
from app.agent.graph import investigation_graph
from app.models.evaluation import EvaluationResult
from app.models.tool_selection import ToolCall, ToolSelectionResult
from app.models.kql import KQLGenerationResult


def mock_kql_generation(prompt, schema):
    return KQLGenerationResult(
        kql=(
            "Heartbeat "
            "| where TimeGenerated > ago(24h) "
            "| summarize LastLogTime = max(TimeGenerated)"
        ),
        reason="Check the latest Heartbeat event timestamp.",
    )


def mock_get_table_schema(table_name):
    return [
        {"name": "TimeGenerated", "type": "datetime"},
        {"name": "Computer", "type": "string"},
        {"name": "Category", "type": "string"},
        {"name": "Version", "type": "string"},
    ]


def mock_selector_invoke(prompt, schema):
    mock_selector_invoke.call_count += 1

    if mock_selector_invoke.call_count == 1:
        return ToolSelectionResult(
            reasoning="Start by checking Sentinel ingestion health.",
            tool_calls=[
                ToolCall(
                    tool_name="sentinel_investigation",
                    arguments={},
                    reason="Investigate Sentinel ingestion health.",
                )
            ],
            investigation_complete=False,
        )

    if mock_selector_invoke.call_count == 2:
        return ToolSelectionResult(
            reasoning=(
                "Sentinel failed, so try an alternative knowledge lookup."
            ),
            tool_calls=[
                ToolCall(
                    tool_name="knowledge_search",
                    arguments={
                        "query": "Sentinel ingestion health troubleshooting"
                    },
                    reason="Retrieve alternative troubleshooting guidance.",
                )
            ],
            investigation_complete=False,
        )

    return ToolSelectionResult(
        reasoning="No further useful tools are available.",
        tool_calls=[],
        investigation_complete=False,
    )


def mock_evaluator_invoke(prompt, schema):
    mock_evaluator_invoke.call_count += 1

    if mock_evaluator_invoke.call_count == 1:
        return EvaluationResult(
            finding=(
                "Sentinel investigation failed. "
                "An alternative knowledge lookup is required."
            ),
            investigation_complete=False,
            needs_more_investigation=True,
            next_investigation_reason=(
                "Retrieve alternative troubleshooting guidance."
            ),
        )

    return EvaluationResult(
        finding=(
            "Sentinel connection failed. The alternative knowledge "
            "search successfully retrieved the Heartbeat ingestion "
            "troubleshooting runbook. However, the documentation does "
            "not establish the customer's live ingestion status. "
            "Live verification remains necessary."
        ),
        investigation_complete=False,
        needs_more_investigation=False,
        next_investigation_reason="",
    )


def mock_sentinel_run_query(*args, **kwargs):
    raise RuntimeError("Simulated Sentinel connection failure")


def mock_get_definition(tool_name):
    definitions = {
        "knowledge_search": ToolDefinition(
            name="knowledge_search",
            description="Search internal troubleshooting knowledge.",
            category="knowledge",
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
        ),
        "sentinel_investigation": ToolDefinition(
            name="sentinel_investigation",
            description="Investigate using Microsoft Sentinel.",
            category="sentinel",
            execution_type="graph",
            requires_approval=False,
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
    }

    return definitions.get(tool_name)


def mock_registry_execute(tool_name, arguments):
    if tool_name == "knowledge_search":
        return [
            {
                "content": (
                    "Heartbeat ingestion troubleshooting guide. "
                    "Check TimeGenerated, ingestion latency, "
                    "connector health, and latest heartbeat records."
                ),
                "source": "Heartbeat_Ingestion_Runbook",
                "source_type": "runbook",
            }
        ]

    raise ValueError(f"Unexpected tool: {tool_name}")


def run_test():
    # Reset mock counters for repeatable execution.
    mock_selector_invoke.call_count = 0
    mock_evaluator_invoke.call_count = 0

    mock_registry = MagicMock()
    mock_registry.get_definition.side_effect = mock_get_definition
    mock_registry.execute.side_effect = mock_registry_execute

    selector_client = MagicMock()
    selector_client.invoke_structured.side_effect = mock_selector_invoke

    evaluator_client = MagicMock()
    evaluator_client.invoke_structured.side_effect = mock_evaluator_invoke

    kql_client = MagicMock()
    kql_client.invoke_structured.side_effect = mock_kql_generation

    initial_state = {
        "tenant_id": "test-tenant",
        "alert": (
            "Investigate whether the Heartbeat table has stopped receiving "
            "logs during the last 24 hours. Identify the latest log timestamp "
            "and determine whether ingestion is continuing."
        ),
        "siem": "sentinel",
        "plan": "",
        "query": "",
        "evidence": [],
        "finding": "",
        "knowledge": [],
        "needs_more_investigation": False,
        "investigation_complete": False,
        "investigation_status": "pending",
        "investigation_outcome": "",
        "investigation_history": [],
        "tool_results": [],
        "tool_errors": [],
        "selected_tools": [],
        "tool_calls": [],
        "execution_complete": False,
        "tool_execution_attempts": 0,
        "max_tool_execution_attempts": 10,
        "investigation_steps": 0,
        "max_investigation_steps": 3,
        "kql_correction_attempts": 0,
        "max_kql_correction_attempts": 1,
        "kql_exhausted": False,
        "pending_sentinel_investigation": False,
        "next_investigation_reason": "",
        "error": "",
    }

    with (
        patch(
            "app.agent.nodes.investigator.SentinelClient.run_query",
            side_effect=mock_sentinel_run_query,
        ),
        patch(
            "app.agent.nodes.tool_executor.build_tool_registry",
            return_value=mock_registry,
        ),
        patch(
            "app.agent.nodes.tool_selector.LLMClient",
            return_value=selector_client,
        ),
        patch(
            "app.agent.nodes.evaluator.LLMClient",
            return_value=evaluator_client,
        ),
        patch(
            "app.agent.nodes.kql_generator.LLMClient",
            return_value=kql_client,
        ),
        patch(
            "app.agent.nodes.kql_generator.SentinelClient.get_table_schema",
            side_effect=mock_get_table_schema,
        ),
    ):
        result = investigation_graph.invoke(initial_state)

    assert kql_client.invoke_structured.called, (
        "KQL generator was not called."
    )

    assert result["investigation_history"], (
        "No Sentinel investigation history was recorded."
    )

    assert result["investigation_history"][0]["status"] == "failed", (
        "Sentinel runtime failure was not recorded."
    )

    print("\n========== RECOVERY SUCCESS TEST ==========")
    print(json.dumps(result, indent=2, default=str))

    # Sentinel investigation must fail.
    assert result["investigation_status"] == "failed"

    # Sentinel must only be attempted once.
    assert result["investigation_attempts"] == 1

    # Sentinel failure must be recorded.
    assert any(
        "failed" in str(item).lower()
        or "sentinel" in str(item).lower()
        for item in result.get("investigation_history", [])
    ), "Sentinel failure was not recorded."

    # Alternative knowledge lookup must succeed.
    assert any(
        item.get("tool") == "knowledge_search"
        and item.get("status") == "success"
        for item in result.get("tool_results", [])
    ), "Knowledge lookup did not succeed."

    # Retrieved runbook must be present in knowledge.
    assert any(
        item.get("source") == "Heartbeat_Ingestion_Runbook"
        for item in result.get("knowledge", [])
    ), "Retrieved runbook was not added to knowledge."

    # Knowledge search must not have an execution error.
    assert not any(
        error.get("tool") == "knowledge_search"
        for error in result.get("tool_errors", [])
    ), "Knowledge lookup unexpectedly failed."

    # No live Sentinel evidence was obtained.
    assert result.get("evidence", []) == []

    # Selector and evaluator should each run twice.
    assert selector_client.invoke_structured.call_count == 2
    assert evaluator_client.invoke_structured.call_count == 2

    # Investigation must remain incomplete.
    assert result["investigation_outcome"] == "incomplete"
    assert result["investigation_complete"] is False
    assert result["needs_more_investigation"] is False

    finding = result.get("finding", "").lower()
    assert "live verification" in finding

    print("\n✅ RECOVERY SUCCESS TEST PASSED")
    print("✅ Sentinel failure was handled.")
    print("✅ Alternative knowledge lookup succeeded.")
    print("✅ Retrieved runbook was added to knowledge.")
    print("✅ No unsupported live-health conclusion was produced.")
    print("✅ Final outcome correctly marked as INCOMPLETE.")


if __name__ == "__main__":
    run_test()