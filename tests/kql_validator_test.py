
from app.agent.nodes.kql_validator import kql_validator_node


def test_valid_query():
    state = {
        "query": "SigninLogs | take 10",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is True, result["kql_validation_errors"]


def test_unknown_table_is_rejected():
    state = {
        "query": "UnknownLogs | take 10",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


def test_empty_query_is_rejected():
    state = {
        "query": "",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


def test_blocked_operator_is_rejected():
    state = {
        "query": ".drop table SigninLogs",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


def test_previously_executed_query_is_rejected():
    state = {
        "query": "SigninLogs | take 10",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [
            {
                "query": "SigninLogs | take 10",
                "evidence": [],
                "status": "success",
            }
        ],
        "kql_correction_attempts": 0,
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False
    assert any(
        "already been executed" in error
        for error in result["kql_validation_errors"]
    )
    assert result["kql_correction_attempts"] == 1


def test_duplicate_query_ignores_case_and_whitespace():
    state = {
        "query": " signinlogs   | TAKE 10 ",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [
            {
                "query": "SigninLogs | take 10",
                "evidence": [],
                "status": "success",
            }
        ],
        "kql_correction_attempts": 0,
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


def test_different_query_is_allowed():
    state = {
        "query": "SigninLogs | take 20",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
        "investigation_history": [
            {
                "query": "SigninLogs | take 10",
                "evidence": [],
                "status": "success",
            }
        ],
        "kql_correction_attempts": 0,
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is True, result["kql_validation_errors"]


if __name__ == "__main__":
    test_valid_query()
    test_unknown_table_is_rejected()
    test_empty_query_is_rejected()
    test_blocked_operator_is_rejected()
    test_previously_executed_query_is_rejected()
    test_duplicate_query_ignores_case_and_whitespace()
    test_different_query_is_allowed()

    print("All KQL validator tests passed.")
