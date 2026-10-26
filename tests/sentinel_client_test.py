
from unittest.mock import MagicMock, patch

from azure.core.exceptions import ServiceRequestError
from azure.monitor.query import LogsQueryStatus

from app.tools.sentinel import (
    SentinelClient,
    SentinelQueryError,
)


def make_client():
    with patch(
        "app.tools.sentinel.ClientSecretCredential"
    ), patch(
        "app.tools.sentinel.LogsQueryClient"
    ):
        client = SentinelClient()

    client.client = MagicMock()
    return client


def test_empty_query_is_rejected():
    client = make_client()

    try:
        client.run_query("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("Empty KQL should be rejected.")

    client.client.query_workspace.assert_not_called()


def test_azure_failure_raises_clear_error():
    client = make_client()
    client.client.query_workspace.side_effect = ServiceRequestError(
        "Connection failed"
    )

    try:
        client.run_query("Heartbeat | take 1")
    except SentinelQueryError:
        pass
    else:
        raise AssertionError("Azure failure should raise an error.")


def test_partial_results_are_rejected():
    client = make_client()
    response = MagicMock()
    response.status = LogsQueryStatus.PARTIAL
    client.client.query_workspace.return_value = response

    try:
        client.run_query("Heartbeat | take 1")
    except SentinelQueryError:
        pass
    else:
        raise AssertionError("Partial results should be rejected.")


if __name__ == "__main__":
    test_empty_query_is_rejected()
    test_azure_failure_raises_clear_error()
    test_partial_results_are_rejected()

    print("All Sentinel client tests passed.")
