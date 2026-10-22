
from app.agent.graph import route_after_kql_validation


def test_valid_query_routes_to_investigator():
    state = {
        "kql_valid": True,
        "kql_attempts": 1,
    }

    assert route_after_kql_validation(state) == "investigator"


def test_invalid_query_retries():
    state = {
        "kql_valid": False,
        "kql_attempts": 1,
    }

    assert route_after_kql_validation(state) == "retry"


def test_invalid_query_stops_after_three_attempts():
    state = {
        "kql_valid": False,
        "kql_attempts": 3,
    }

    assert route_after_kql_validation(state) == "end"


if __name__ == "__main__":
    test_valid_query_routes_to_investigator()
    test_invalid_query_retries()
    test_invalid_query_stops_after_three_attempts()

    print("All graph routing tests passed.")
