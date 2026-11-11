
from unittest.mock import MagicMock, patch

from azure.core.exceptions import HttpResponseError
from azure.monitor.query import LogsQueryStatus

from app.tools.sentinel import SentinelClient


def make_http_error(status_code):
    """Create a simulated Azure HTTP error."""

    response = MagicMock()
    response.status_code = status_code
    response.headers = {}

    return HttpResponseError(
        message="Simulated Azure service failure",
        response=response,
    )


def run_test():
    # Create SentinelClient without initializing Azure credentials.
    sentinel = SentinelClient.__new__(SentinelClient)

    sentinel.client = MagicMock()
    sentinel.workspace_id = "test-workspace"

    # Simulate:
    # Attempt 1 -> HTTP 503
    # Attempt 2 -> HTTP 503
    # Attempt 3 -> Success

    sentinel.client.query_workspace.side_effect = [
        make_http_error(503),
        make_http_error(503),
        MagicMock(
            status=LogsQueryStatus.SUCCESS,
            tables=[],
        ),
    ]

    with patch("app.tools.sentinel.time.sleep") as mock_sleep:
        result = sentinel.run_query(
            "Heartbeat | take 10"
        )

    # Verify the query succeeded.
    assert result == []

    # Verify three total attempts.
    assert sentinel.client.query_workspace.call_count == 3

    # Verify two waits occurred between attempts.
    assert mock_sleep.call_count == 2

    print(
        "Retry attempts:",
        sentinel.client.query_workspace.call_count,
    )

    print(
        "Wait calls:",
        mock_sleep.call_count,
    )

    print("\n========== SENTINEL RETRY TEST ==========")

    print("✅ First temporary failure handled.")
    print("✅ Second temporary failure handled.")
    print("✅ Third attempt succeeded.")
    print("✅ Retry count verified.")
    print("✅ Backoff waits verified.")

    print("\n✅ SENTINEL RETRY TEST PASSED")


if __name__ == "__main__":
    run_test()
