
from app.agent.graph import route_after_kql_validation


def test_first_validation_failure_retries():
    state = {
        "query": "SecurityEvent | take 10",
        "kql_valid": False,
        "kql_correction_attempts": 1,
    }

    assert route_after_kql_validation(state) == "retry"
    print("First KQL correction retry passed.")


def test_second_validation_failure_exhausts():
    state = {
        "query": "SecurityEvent | take 10",
        "kql_valid": False,
        "kql_correction_attempts": 2,
    }

    assert route_after_kql_validation(state) == "kql_exhausted"
    print("KQL exhaustion routing passed.")


def test_valid_query_executes():
    state = {
        "query": "SecurityEvent | take 10",
        "kql_valid": True,
        "kql_correction_attempts": 0,
    }

    assert route_after_kql_validation(state) == "investigator"
    print("Valid KQL routing passed.")


def test_empty_query_exhausts():
    state = {
        "query": "",
        "kql_valid": False,
        "kql_correction_attempts": 1,
    }

    assert route_after_kql_validation(state) == "kql_exhausted"
    print("Empty KQL routing passed.")


if __name__ == "__main__":
    test_first_validation_failure_retries()
    test_second_validation_failure_exhausts()
    test_valid_query_executes()
    test_empty_query_exhausts()

    print("All KQL routing tests passed.")
