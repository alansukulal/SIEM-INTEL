
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
    for status_code in (401, 403):
        sentinel = SentinelClient.__new__(SentinelClient)
        sentinel.client = MagicMock()
        sentinel.workspace_id = "test-workspace"

        sentinel.client.query_workspace.side_effect = make_http_error(
            status_code
        )

        with patch("app.tools.sentinel.time.sleep") as mock_sleep:
            try:
                sentinel.run_query("Heartbeat | take 10")
                raise AssertionError(
                    f"HTTP {status_code} should have failed."
                )
            except SentinelQueryError:
                pass

        assert sentinel.client.query_workspace.call_count == 1
        assert mock_sleep.call_count == 0

        print(f"✅ HTTP {status_code}: failed immediately.")
        print("   API calls:", sentinel.client.query_workspace.call_count)
        print("   Retry waits:", mock_sleep.call_count)

    print("\n✅ NON-RETRYABLE ERROR TEST PASSED")


if __name__ == "__main__":
    run_test()
