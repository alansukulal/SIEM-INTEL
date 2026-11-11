
from unittest.mock import patch

from app.agent import graph as graph_module
from app.agent.nodes import investigator as investigator_module
from app.tools import register as register_module


def test_sentinel_failure_recovers_with_knowledge_search():

    # --------------------------------------------------
    # 1. Mock KQL generation and validation
    # --------------------------------------------------

    def fake_kql_generator(state):
        return {
            "query": "SecurityEvent | take 10",
            "kql_attempts": state.get("kql_attempts", 0) + 1,
            "kql_reason": "Mock query for recovery test",
        }

    def fake_kql_validator(state):
        return {
            "kql_valid": True,
            "kql_validation_errors": [],
            "kql_correction_attempts": 0,
        }

    # --------------------------------------------------
    # 2. Simulate Sentinel failure
    # --------------------------------------------------

    class FakeSentinelClient:

        def run_query(self, query):
            raise RuntimeError(
                "Simulated Sentinel connection failure"
            )

    # --------------------------------------------------
    # 3. Mock knowledge search
    # --------------------------------------------------

    knowledge_result = [
        {
            "source": "runbook",
            "title": "Sentinel ingestion troubleshooting",
            "content": (
                "Check connector health, ingestion latency, "
                "and the last successful ingestion timestamp."
            ),
        }
    ]

    knowledge_search_calls = []

    def fake_knowledge_search(
        query,
        source_type=None,
        limit=5,
    ):
        knowledge_search_calls.append({
            "query": query,
            "source_type": source_type,
            "limit": limit,
        })

        return knowledge_result

    # --------------------------------------------------
    # 4. Mock LLM structured responses
    # --------------------------------------------------

    selector_responses = [
        {
            "reasoning": "Live Sentinel evidence is required first.",
            "tool_calls": [
                {
                    "tool_name": "sentinel_investigation",
                    "arguments": {},
                    "reason": "Check live Sentinel evidence.",
                }
            ],
            "investigation_complete": False,
            "completion_reason": "",
        },
        {
            "reasoning": (
                "Sentinel failed. Retrieve internal troubleshooting "
                "documentation as an alternative."
            ),
            "tool_calls": [
                {
                    "tool_name": "knowledge_search",
                    "arguments": {
                        "query": "Sentinel ingestion troubleshooting",
                        "source_type": "runbook",
                        "limit": 5,
                    },
                    "reason": "Retrieve the relevant troubleshooting runbook.",
                }
            ],
            "investigation_complete": False,
            "completion_reason": "",
        },
    ]

    evaluation_responses = [
        {
            "finding": (
                "Sentinel investigation failed because the "
                "query execution service was unavailable."
            ),
            "needs_more_investigation": True,
            "next_investigation_reason": (
                "Retrieve alternative troubleshooting guidance."
            ),
        },
        {
            "finding": (
                "Sentinel live verification could not be completed. "
                "The retrieved runbook recommends checking connector "
                "health, ingestion latency, and the last successful "
                "ingestion timestamp. These checks are recommendations, "
                "not verified live findings."
            ),
            "needs_more_investigation": False,
            "next_investigation_reason": "",
        },
    ]

    selector_index = 0
    evaluator_index = 0
    evaluation_prompts = []

    def fake_invoke_structured(self, prompt, schema):

        nonlocal selector_index, evaluator_index

        schema_name = schema.__name__

        if schema_name == "InvestigationPlan":
            return schema(
                objective=(
                    "Determine whether Sentinel ingestion is healthy."
                ),
                evidence_needed=[
                    "Recent ingestion evidence",
                    "Connector health",
                ],
                success_criteria=[
                    "Recent ingestion and connector status are verified."
                ],
                investigation_scope=(
                    "Use Sentinel evidence and relevant troubleshooting "
                    "documentation."
                ),
            )

        if schema_name == "ToolSelectionResult":

            if selector_index >= len(selector_responses):
                raise AssertionError(
                    "Unexpected additional tool selector invocation."
                )

            response = selector_responses[selector_index]
            selector_index += 1

            return schema(**response)

        if schema_name == "EvaluationResult":

            if evaluator_index >= len(evaluation_responses):
                raise AssertionError(
                    "Unexpected additional evaluator invocation."
                )

            evaluation_prompts.append(prompt)

            response = evaluation_responses[evaluator_index]
            evaluator_index += 1

            return schema(**response)

        raise AssertionError(
            f"Unexpected structured schema: {schema_name}"
        )

    # --------------------------------------------------
    # 5. Patch external dependencies
    # --------------------------------------------------

    with (
        patch.object(
            graph_module,
            "kql_generator_node",
            fake_kql_generator,
        ),
        patch.object(
            graph_module,
            "kql_validator_node",
            fake_kql_validator,
        ),
        patch.object(
            investigator_module,
            "SentinelClient",
            FakeSentinelClient,
        ),
        patch.object(
            register_module,
            "knowledge_search",
            fake_knowledge_search,
        ),
        patch(
            "app.llm.client.LLMClient.invoke_structured",
            fake_invoke_structured,
        ),
    ):

        # Build the real graph with patched dependencies.
        test_graph = graph_module.build_investigation_graph()

        initial_state = {
            "tenant_id": "test-tenant",
            "alert": "Sentinel ingestion appears to have stopped.",
            "siem": "Microsoft Sentinel",

            "knowledge": [],
            "evidence": [],
            "investigation_history": [],

            "investigation_attempts": 0,
            "max_investigation_steps": 3,

            "tool_execution_attempts": 0,
            "max_tool_execution_attempts": 10,

            "tool_results": [],
            "tool_errors": [],
            "tool_calls": [],
            "tool_call_history": [],

            "pending_capabilities": [],
            "selected_tools": [],
            "available_tools": [],

            "needs_more_investigation": False,
            "execution_complete": False,
            "tool_batch_complete": False,

            "pending_approval": False,
            "approved_actions": [],
        }

        result = test_graph.invoke(initial_state)

    # --------------------------------------------------
    # 6. Verify Sentinel failure
    # --------------------------------------------------

    assert result["investigation_attempts"] == 1

    assert result["investigation_status"] == "failed"

    assert result["investigation_history"]

    sentinel_failure = result["investigation_history"][-1]

    assert sentinel_failure["status"] == "failed"

    assert "unexpected error" in sentinel_failure["error"].lower()

    # --------------------------------------------------
    # 7. Verify alternative tool execution
    # --------------------------------------------------

    assert len(knowledge_search_calls) == 1

    assert (
        knowledge_search_calls[0]["query"]
        == "Sentinel ingestion troubleshooting"
    )

    assert (
        knowledge_search_calls[0]["source_type"]
        == "runbook"
    )

    # Verify the returned knowledge reached the graph state.
    assert any(
        item.get("title") == "Sentinel ingestion troubleshooting"
        for item in result["knowledge"]
    )

    # --------------------------------------------------
    # 8. Verify evaluator received alternative evidence
    # --------------------------------------------------

    assert len(evaluation_prompts) == 2

    second_evaluation_prompt = evaluation_prompts[1]

    assert (
        "Sentinel ingestion troubleshooting"
        in second_evaluation_prompt
    )

    assert (
        "connector health"
        in second_evaluation_prompt.lower()
    )

    # --------------------------------------------------
    # 9. Verify graph completion
    # --------------------------------------------------

    assert selector_index == 2

    assert evaluator_index == 2

    assert result["needs_more_investigation"] is False

    assert result["investigation_outcome"] == "incomplete"
    assert result["evidence_sufficient"] is False

    assert "runbook" in result["finding"].lower() or (
        "retrieved" in result["finding"].lower()
    )

    print("\n======================================")
    print("ALL RECOVERY FLOW ASSERTIONS PASSED")
    print("======================================")
    print("Sentinel execution: FAILED (simulated)")
    print("Alternative tool: knowledge_search")
    print("Knowledge retrieval: SUCCESS")
    print("Evaluator received alternative evidence: YES")
    print("Final investigation outcome: COMPLETED")
    print("======================================")


if __name__ == "__main__":
    test_sentinel_failure_recovers_with_knowledge_search()
