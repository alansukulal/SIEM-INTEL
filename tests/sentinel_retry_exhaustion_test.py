
from unittest.mock import MagicMock, patch

from azure.core.exceptions import HttpResponseError

from app.tools.sentinel import SentinelClient, SentinelQueryError


def make_http_error(status_code):
    response = MagicMock()
    response.status_code = status_code
    response.headers = {}

    return HttpResponseError(
        message=f"Simulated HTTP {status_code} error",
        response=response,
    )


def run_test():
    sentinel = SentinelClient.__new__(SentinelClient)
    sentinel.client = MagicMock()
    sentinel.workspace_id = "test-workspace"

    # All four attempts fail with HTTP 503.
    sentinel.client.query_workspace.side_effect = [
        make_http_error(503),
        make_http_error(503),
        make_http_error(503),
        make_http_error(503),
    ]

    with patch("app.tools.sentinel.time.sleep") as mock_sleep:
        try:
            sentinel.run_query("Heartbeat | take 10")
            raise AssertionError("Expected SentinelQueryError.")
        except SentinelQueryError as exc:
            print("Expected exception:", exc)

    assert sentinel.client.query_workspace.call_count == 4
    assert mock_sleep.call_count == 3

    print("\nAPI calls:", sentinel.client.query_workspace.call_count)
    print("Retry waits:", mock_sleep.call_count)

    print("\n========== RETRY EXHAUSTION TEST ==========")
    print("✅ All four attempts failed.")
    print("✅ Retry limit was respected.")
    print("✅ No infinite retry loop.")
    print("✅ Controlled exception was raised.")
    print("\n✅ RETRY EXHAUSTION TEST PASSED")


if __name__ == "__main__":
    run_test()
