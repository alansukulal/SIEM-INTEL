
from unittest.mock import patch

from app.agent.graph import build_investigation_graph


def fake_planner(state):
    return {"plan": "Investigate failed sign-ins"}


def fake_knowledge_retriever(state):
    return {
        "knowledge": [
            {
                "document": "## SigninLogs",
                "metadata": {"table": "SigninLogs"},
                "distance": 0.1,
            }
        ]
    }


def fake_kql_generator(state):
    return {
        "query": "SigninLogs | take 10",
        "kql_reason": "Test query",
        "kql_attempts": state.get("kql_attempts", 0) + 1,
    }


def fake_investigator(state):
    return {
        "evidence": [{"ResultType": "50074"}],
        "investigation_attempts": (
            state.get("investigation_attempts", 0) + 1
        ),
        "investigation_status": "success",
        "investigation_error": "",
    }


def fake_evaluator(state):
    return {
        "finding": "Test evidence received successfully.",
        "needs_more_investigation": False,
        "next_investigation_reason": "",
    }


def initial_state():
    return {
        "alert": "Investigate failed user sign-ins",
        "siem": "Microsoft Sentinel",
        "plan": "",
        "query": "",
        "evidence": [],
        "finding": "",
        "needs_more_investigation": False,
        "investigation_attempts": 0,
        "investigation_status": "pending",
        "investigation_error": "",
        "next_investigation_reason": "",
        "kql_valid": False,
        "kql_validation_errors": [],
        "kql_attempts": 0,
        "kql_reason": "",
        "knowledge": [],
    }


def test_valid_query_completes_investigation():
    with (
        patch("app.agent.graph.planner_node", fake_planner),
        patch(
            "app.agent.graph.knowledge_retriever_node",
            fake_knowledge_retriever,
        ),
        patch("app.agent.graph.kql_generator_node", fake_kql_generator),
        patch("app.agent.graph.investigator_node", fake_investigator),
        patch("app.agent.graph.evaluator_node", fake_evaluator),
    ):
        graph = build_investigation_graph()
        result = graph.invoke(initial_state())

    assert result["kql_valid"] is True
    assert result["investigation_attempts"] == 1
    assert result["investigation_status"] == "success"
    assert result["finding"] == "Test evidence received successfully."

    print("Valid-query graph flow passed.")


def test_invalid_query_never_reaches_investigator():
    def invalid_generator(state):
        return {
            "query": "UnknownLogs | take 10",
            "kql_reason": "Intentional invalid test query",
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    def investigator_must_not_run(state):
        raise AssertionError(
            "Invalid KQL must never reach the investigator."
        )

    with (
        patch("app.agent.graph.planner_node", fake_planner),
        patch(
            "app.agent.graph.knowledge_retriever_node",
            fake_knowledge_retriever,
        ),
        patch("app.agent.graph.kql_generator_node", invalid_generator),
        patch(
            "app.agent.graph.investigator_node",
            investigator_must_not_run,
        ),
    ):
        graph = build_investigation_graph()
        result = graph.invoke(initial_state())

    assert result["kql_valid"] is False
    assert result["kql_attempts"] == 3
    assert result["investigation_attempts"] == 0

    print("Invalid-query safety routing passed.")


def test_evaluator_can_request_follow_up():
    generated_queries = []
    evaluator_calls = []

    def follow_up_generator(state):
        reason = state.get("next_investigation_reason", "")

        if state.get("investigation_attempts", 0) == 0:
            query = "SigninLogs | take 10"
        else:
            assert reason == "Check the result type of failed sign-ins."
            query = (
                "SigninLogs | where ResultType == '50074' | take 10"
            )

        generated_queries.append(query)

        return {
            "query": query,
            "kql_reason": "Test follow-up query",
            "kql_attempts": state.get("kql_attempts", 0) + 1,
        }

    def follow_up_evaluator(state):
        evaluator_calls.append(state["investigation_attempts"])

        if len(evaluator_calls) == 1:
            return {
                "finding": "More evidence is required.",
                "needs_more_investigation": True,
                "next_investigation_reason": (
                    "Check the result type of failed sign-ins."
                ),
            }

        return {
            "finding": "Follow-up investigation completed.",
            "needs_more_investigation": False,
            "next_investigation_reason": "",
        }

    with (
        patch("app.agent.graph.planner_node", fake_planner),
        patch(
            "app.agent.graph.knowledge_retriever_node",
            fake_knowledge_retriever,
        ),
        patch(
            "app.agent.graph.kql_generator_node",
            follow_up_generator,
        ),
        patch(
            "app.agent.graph.investigator_node",
            fake_investigator,
        ),
        patch(
            "app.agent.graph.evaluator_node",
            follow_up_evaluator,
        ),
    ):
        graph = build_investigation_graph()
        result = graph.invoke(initial_state())

    assert len(generated_queries) == 2
    assert generated_queries[0] != generated_queries[1]
    assert evaluator_calls == [1, 2]
    assert result["investigation_attempts"] == 2
    assert result["needs_more_investigation"] is False
    assert result["finding"] == "Follow-up investigation completed."

    print("Evaluator follow-up investigation passed.")


def test_sentinel_failure_stops_investigation():
    def failed_investigator(state):
        return {
            "evidence": [],
            "investigation_attempts": (
                state.get("investigation_attempts", 0) + 1
            ),
            "investigation_status": "failed",
            "investigation_error": "Sentinel query failed.",
        }

    def evaluator_requests_retry(state):
        return {
            "finding": "Investigation failed.",
            "needs_more_investigation": True,
            "next_investigation_reason": "Retry the query.",
        }

    with (
        patch("app.agent.graph.planner_node", fake_planner),
        patch(
            "app.agent.graph.knowledge_retriever_node",
            fake_knowledge_retriever,
        ),
        patch("app.agent.graph.kql_generator_node", fake_kql_generator),
        patch(
            "app.agent.graph.investigator_node",
            failed_investigator,
        ),
        patch(
            "app.agent.graph.evaluator_node",
            evaluator_requests_retry,
        ),
    ):
        graph = build_investigation_graph()
        result = graph.invoke(initial_state())

    assert result["investigation_status"] == "failed"
    assert result["investigation_attempts"] == 1
    assert result["kql_attempts"] == 1

    print("Sentinel failure routing passed.")


if __name__ == "__main__":
    test_valid_query_completes_investigation()
    test_invalid_query_never_reaches_investigator()
    test_evaluator_can_request_follow_up()
    test_sentinel_failure_stops_investigation()
    print("All graph flow tests passed.")
