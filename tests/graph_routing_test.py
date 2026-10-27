
from app.agent.graph import route_after_kql_validation
from app.agent.graph import (
    route_after_kql_validation,
    route_after_evaluation,
)


def test_valid_query_routes_to_investigator():
    state = {
        "kql_valid": True,
        "kql_attempts": 1,
        "kql_correction_attempts": 0,
    }

    assert route_after_kql_validation(state) == "investigator"


def test_invalid_query_retries():
    state = {
        "kql_valid": False,
        "kql_attempts": 1,
        "kql_correction_attempts": 1,
    }

    assert route_after_kql_validation(state) == "retry"


def test_invalid_query_stops_after_three_attempts():
    state = {
        "kql_valid": False,
        "kql_attempts": 3,
        "kql_correction_attempts": 3,
    }

    assert route_after_kql_validation(state) == "kql_exhausted"


def test_evaluation_completes_when_no_more_investigation_needed():
    state = {
        "investigation_status": "success",
        "needs_more_investigation": False,
        "investigation_attempts": 1,
        "max_investigation_steps": 3,
    }

    assert route_after_evaluation(state) == "completed"


def test_evaluation_stops_at_maximum_investigation_steps():
    state = {
        "investigation_status": "success",
        "needs_more_investigation": True,
        "investigation_attempts": 3,
        "max_investigation_steps": 3,
    }

    assert route_after_evaluation(state) == "incomplete"


def test_failed_investigation_routes_to_failure():
    state = {
        "investigation_status": "failed",
        "needs_more_investigation": True,
        "investigation_attempts": 1,
        "max_investigation_steps": 3,
    }

    assert route_after_evaluation(state) == "failed"


if __name__ == "__main__":
    test_valid_query_routes_to_investigator()
    test_invalid_query_retries()
    test_invalid_query_stops_after_three_attempts()
    test_evaluation_completes_when_no_more_investigation_needed()
    test_evaluation_stops_at_maximum_investigation_steps()
    test_failed_investigation_routes_to_failure()

    print("All graph routing tests passed.")
