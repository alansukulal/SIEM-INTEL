
from app.agent.nodes.kql_validator import kql_validator_node


def test_valid_query():
    state = {
        "query": "SigninLogs | take 10",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is True, result["kql_validation_errors"]


def test_unknown_table_is_rejected():
    state = {
        "query": "UnknownLogs | take 10",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


def test_empty_query_is_rejected():
    state = {
        "query": "",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


def test_blocked_operator_is_rejected():
    state = {
        "query": ".drop table SigninLogs",
        "knowledge": [
            {"metadata": {"table": "SigninLogs"}}
        ],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False


if __name__ == "__main__":
    test_valid_query()
    test_unknown_table_is_rejected()
    test_empty_query_is_rejected()
    test_blocked_operator_is_rejected()

    print("All KQL validator tests passed.")
