from app.tools.sentinel_tools import sentinel_query


def test_sentinel_rejects_empty_query():
    try:
        sentinel_query(
            query="",
            knowledge=[],
        )
    except ValueError:
        print("PASS: Empty query rejected.")
        return

    raise AssertionError("Empty query was not rejected.")


def test_sentinel_rejects_invalid_kql():
    try:
        sentinel_query(
            query=".drop table SentinelOne_CL",
            knowledge=[],
        )
    except ValueError:
        print("PASS: Invalid KQL rejected.")
        return

    raise AssertionError("Invalid KQL was not rejected.")


if __name__ == "__main__":
    test_sentinel_rejects_empty_query()
    test_sentinel_rejects_invalid_kql()

    print("All Sentinel safety tests passed!")