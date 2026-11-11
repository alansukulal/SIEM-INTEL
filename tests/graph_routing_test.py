
from app.agent.graph import (
    route_after_kql_validation,
    route_after_evaluation,
    route_after_tool_execution,
)


def test_valid_query_routes_to_investigator():
    state = {
        "query": "SecurityEvent | take 10",
        "kql_valid": True,
        "kql_correction_attempts": 0,
    }

    assert route_after_kql_validation(state) == "investigator"


def test_invalid_query_retries():
    state = {
        "query": "SecurityEvent | invalid",
        "kql_valid": False,
        "kql_correction_attempts": 1,
    }

    assert route_after_kql_validation(state) == "retry"


def test_invalid_query_stops_after_correction_budget():
    state = {
        "query": "SecurityEvent | invalid",
        "kql_valid": False,
        "kql_correction_attempts": 2,
    }

    assert route_after_kql_validation(state) == "kql_exhausted"


def test_empty_query_stops():
    state = {
        "query": "",
        "kql_valid": False,
        "kql_correction_attempts": 0,
    }

    assert route_after_kql_validation(state) == "kql_exhausted"


def test_evaluation_completes_only_when_explicitly_complete():
    state = {
        "investigation_status": "success",
        "investigation_complete": True,
        "needs_more_investigation": False,
    }

    assert route_after_evaluation(state) == "completed"


def test_success_status_alone_does_not_complete_investigation():
    state = {
        "investigation_status": "success",
        "investigation_complete": False,
        "needs_more_investigation": False,
    }

    assert route_after_evaluation(state) == "incomplete"


def test_evaluation_requests_another_tool_selection():
    state = {
        "investigation_complete": False,
        "needs_more_investigation": True,
        "tool_execution_attempts": 2,
        "max_tool_execution_attempts": 10,
    }

    assert route_after_evaluation(state) == "select_again"


def test_evaluation_stops_when_tool_budget_is_exhausted():
    state = {
        "investigation_complete": False,
        "needs_more_investigation": True,
        "tool_execution_attempts": 10,
        "max_tool_execution_attempts": 10,
    }

    assert route_after_evaluation(state) == "incomplete"


def test_failed_investigation_does_not_route_to_completed():
    state = {
        "investigation_status": "failed",
        "investigation_complete": False,
        "needs_more_investigation": False,
    }

    assert route_after_evaluation(state) == "incomplete"


def test_sentinel_capability_routes_to_kql_when_budget_available():
    state = {
        "pending_capabilities": ["sentinel_investigation"],
        "investigation_attempts": 1,
        "max_investigation_steps": 3,
    }

    assert route_after_tool_execution(state) == "sentinel_investigation"


def test_sentinel_capability_routes_to_evaluation_when_budget_exhausted():
    state = {
        "pending_capabilities": ["sentinel_investigation"],
        "investigation_attempts": 3,
        "max_investigation_steps": 3,
    }

    assert route_after_tool_execution(state) == "evaluate"


if __name__ == "__main__":
    test_valid_query_routes_to_investigator()
    test_invalid_query_retries()
    test_invalid_query_stops_after_correction_budget()
    test_empty_query_stops()
    test_evaluation_completes_only_when_explicitly_complete()
    test_success_status_alone_does_not_complete_investigation()
    test_evaluation_requests_another_tool_selection()
    test_evaluation_stops_when_tool_budget_is_exhausted()
    test_failed_investigation_does_not_route_to_completed()
    test_sentinel_capability_routes_to_kql_when_budget_available()
    test_sentinel_capability_routes_to_evaluation_when_budget_exhausted()

    print("All graph routing tests passed.")
