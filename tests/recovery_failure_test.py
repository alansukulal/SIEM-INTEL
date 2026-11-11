
import json
from unittest.mock import MagicMock, patch

from app.models.tool_definition import ToolDefinition
from app.models.evaluation import EvaluationResult
from app.models.tool_selection import ToolCall, ToolSelectionResult
from app.models.kql import KQLGenerationResult
from app.agent.graph import investigation_graph
from app.tools.sentinel import SentinelQueryError


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
                "Sentinel failed. Retrieve alternative troubleshooting "
                "documentation."
            ),
            tool_calls=[
                ToolCall(
                    tool_name="knowledge_search",
                    arguments={
                        "query": "Sentinel ingestion health troubleshooting"
                    },
                    reason="Retrieve an alternative troubleshooting runbook.",
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
                "Alternative troubleshooting documentation is required."
            ),
            investigation_complete=False,
            needs_more_investigation=True,
            next_investigation_reason=(
                "Retrieve alternative troubleshooting guidance."
            ),
        )

    return EvaluationResult(
        finding=(
            "The Sentinel connection failed after retries. "
            "An alternative troubleshooting runbook was successfully "
            "retrieved. However, the runbook provides general guidance "
            "and does not establish the current live ingestion status. "
            "Live Sentinel ingestion health remains unverified."
        ),
        investigation_complete=False,
        needs_more_investigation=False,
        next_investigation_reason="",
    )


def mock_sentinel_run_query(*args, **kwargs):
    raise SentinelQueryError(
        "Sentinel query failed after exhausting retries."
    )


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


def mock_registry_execute(*args, **kwargs):
    return [
        {
            "source": "Sentinel Ingestion Troubleshooting Runbook",
            "content": (
                "Check the data connector status, ingestion configuration, "
                "and recent ingestion errors when investigating missing logs."
            ),
            "score": 0.91,
        }
    ]


def run_test():
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

    print("\n========== RECOVERY SUCCESS TEST ==========")
    print(json.dumps(result, indent=2, default=str))

    # Sentinel investigation must fail.
    assert result["investigation_status"] == "failed"

    # Sentinel failure must be recorded.
    assert result["investigation_history"]
    assert result["investigation_history"][0]["status"] == "failed"

    # Alternative knowledge search must succeed.
    assert mock_registry.execute.called
    assert not any(
        error.get("tool") == "knowledge_search"
        for error in result.get("tool_errors", [])
    ), "Knowledge search unexpectedly failed."

    # Retrieved knowledge must be present.
    knowledge = result.get("knowledge", [])
    assert knowledge, "No alternative knowledge was retrieved."

    assert any(
        "runbook" in str(item).lower()
        or "troubleshooting" in str(item).lower()
        for item in knowledge
    ), "Retrieved runbook was not found in knowledge."

    # The agent must not claim live ingestion health is verified.
    finding = result.get("finding", "").lower()

    assert "live sentinel ingestion health remains unverified" in finding
    assert result["investigation_complete"] is False
    assert result["investigation_outcome"] == "incomplete"

    print("\n✅ RECOVERY SUCCESS TEST PASSED")
    print("✅ Sentinel failure was handled.")
    print("✅ Alternative knowledge lookup succeeded.")
    print("✅ Retrieved runbook was added to knowledge.")
    print("✅ No unsupported live-health conclusion was produced.")
    print("✅ Final outcome correctly marked as INCOMPLETE.")


if __name__ == "__main__":
    run_test()
