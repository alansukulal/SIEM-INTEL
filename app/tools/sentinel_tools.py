from datetime import timedelta
from typing import Any

from app.tools.kql_safety import validate_kql
from app.tools.sentinel import SentinelClient


def sentinel_query(
    query: str,
    knowledge: list[dict[str, Any]],
    investigation_history: list[dict[str, Any]] | None = None,
    timespan_hours: int = 1,
) -> dict[str, Any]:
    """
    Validate and execute a read-only Sentinel KQL query.
    """

    if not query or not query.strip():
        raise ValueError("KQL query cannot be empty.")

    if not 1 <= timespan_hours <= 168:
        raise ValueError("Timespan must be between 1 and 168 hours.")

    errors = validate_kql(
        query=query,
        knowledge=knowledge,
        investigation_history=investigation_history or [],
    )

    if errors:
        raise ValueError(
            "KQL validation failed: " + "; ".join(errors)
        )

    client = SentinelClient()

    results = client.run_query(
        query,
        timespan=timedelta(hours=timespan_hours),
        server_timeout=30,
    )

    return {
        "query": query,
        "status": "success",
        "row_count": len(results),
        "results": results,
    }