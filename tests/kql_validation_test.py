
import pytest

from app.agent.nodes.kql_validator import kql_validator_node


def make_state(query: str) -> dict:
    return {
        "query": query,
        "knowledge": [
            {"metadata": {"table": "Heartbeat"}},
        ],
    }


def test_valid_query_passes():
    result = kql_validator_node(
        make_state("Heartbeat | take 10")
    )

    assert result["kql_valid"] is True
    assert result["kql_validation_errors"] == []


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "Heartbeat | take 10; Heartbeat | take 5",
        "OtherTable | take 10",
        "Heartbeat | union OtherTable",
        ".drop table Heartbeat",
        "```kql\nHeartbeat | take 10\n```",
    ],
)
def test_invalid_queries_are_rejected(query):
    result = kql_validator_node(make_state(query))

    assert result["kql_valid"] is False
    assert result["kql_validation_errors"]


def test_query_is_rejected_when_no_table_is_allow_listed():
    state = {
        "query": "Heartbeat | take 10",
        "knowledge": [],
    }

    result = kql_validator_node(state)

    assert result["kql_valid"] is False
