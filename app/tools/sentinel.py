
from datetime import timedelta
import logging
import random
import re
import time

from azure.core.exceptions import (
    AzureError,
    HttpResponseError,
    ServiceRequestError,
    ServiceResponseError,
)
from azure.identity import ClientSecretCredential
from azure.monitor.query import (
    LogsQueryClient,
    LogsQueryStatus,
)


logger = logging.getLogger(__name__)


class SentinelQueryError(RuntimeError):
    """Raised when a Sentinel query cannot be completed reliably."""


class SentinelClient:
    MAX_RETRIES = 3
    BASE_DELAY = 2
    MAX_DELAY = 30

    RETRYABLE_STATUS_CODES = {
        408,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(self, integration: dict) -> None:
        self.credential = ClientSecretCredential(
            tenant_id=integration["azure_tenant_id"],
            client_id=integration["client_id"],
            client_secret=integration["client_secret"],
        )

        self.client = LogsQueryClient(self.credential)
        self.workspace_id = integration["workspace_id"]

    def _is_retryable_error(self, exc: AzureError) -> bool:
        """Determine whether an Azure error is safe to retry."""

        if isinstance(
            exc,
            (ServiceRequestError, ServiceResponseError),
        ):
            return True

        if isinstance(exc, HttpResponseError):
            status_code = getattr(exc, "status_code", None)

            if status_code is None and exc.response is not None:
                status_code = getattr(
                    exc.response,
                    "status_code",
                    None,
                )

            return status_code in self.RETRYABLE_STATUS_CODES

        return False

    def _get_retry_after(self, exc: AzureError) -> float | None:
        """Extract Retry-After from an Azure HTTP response."""

        response = getattr(exc, "response", None)

        if response is None:
            return None

        headers = getattr(response, "headers", {})

        retry_after = headers.get("Retry-After")

        if retry_after is None:
            return None

        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            return None

    def run_query(
        self,
        kql: str,
        *,
        timespan: timedelta = timedelta(hours=1),
        server_timeout: int = 30,
    ) -> list[dict]:
        """Execute a KQL query with bounded retries."""

        if not kql or not kql.strip():
            raise ValueError("KQL query cannot be empty.")

        if not 1 <= server_timeout <= 600:
            raise ValueError(
                "server_timeout must be between 1 and 600 seconds."
            )

        response = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.client.query_workspace(
                    workspace_id=self.workspace_id,
                    query=kql,
                    timespan=timespan,
                    server_timeout=server_timeout,
                )
                break

            except AzureError as exc:
                logger.warning(
                    "Sentinel Azure diagnostic: status_code=%s, "
                    "error_code=%s, message=%s",
                    getattr(exc, "status_code", None),
                    getattr(exc, "error_code", None),
                    str(exc)[:1000],
                )
                logger.warning(
                    "Sentinel query request failed. "
                    "Attempt %d/%d. Error type: %s",
                    attempt + 1,
                    self.MAX_RETRIES + 1,
                    type(exc).__name__,
                )

                if not self._is_retryable_error(exc):
                    raise SentinelQueryError(
                        "Sentinel query failed with a non-retryable "
                        "Azure error. Check authentication, permissions, "
                        "and KQL syntax."
                    ) from exc

                if attempt >= self.MAX_RETRIES:
                    raise SentinelQueryError(
                        "Sentinel query failed after exhausting retries."
                    ) from exc

                retry_after = self._get_retry_after(exc)

                if retry_after is not None:
                    delay = min(retry_after, self.MAX_DELAY)
                else:
                    exponential_delay = (
                        self.BASE_DELAY * (2 ** attempt)
                    )
                    jitter = random.uniform(0, 0.5)

                    delay = min(
                        exponential_delay + jitter,
                        self.MAX_DELAY,
                    )

                logger.info(
                    "Retrying Sentinel query in %.2f seconds.",
                    delay,
                )

                time.sleep(delay)

        if response.status == LogsQueryStatus.PARTIAL:
            logger.warning("Sentinel returned partial query results.")
            raise SentinelQueryError(
                "Sentinel returned partial results. The investigation "
                "cannot treat them as complete evidence."
            )

        if response.status != LogsQueryStatus.SUCCESS:
            raise SentinelQueryError(
                "Sentinel did not return a successful query result."
            )

        if not response.tables:
            return []

        rows = []

        for table in response.tables:
            column_names = [
                column if isinstance(column, str) else column.name
                for column in table.columns
            ]

            rows.extend(
                dict(zip(column_names, row))
                for row in table.rows
            )

        return rows

    def get_table_schema(
        self,
        table_name: str,
    ) -> list[dict[str, str]]:
        """
        Discover a table's columns and data types in the configured workspace.

        Only a simple KQL table identifier is accepted. Arbitrary query text
        is never accepted as a table name.
        """

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            table_name,
        ):
            raise ValueError("Invalid Sentinel table identifier.")

        schema_query = f"{table_name} | getschema"

        rows = self.run_query(
            schema_query,
            timespan=timedelta(days=1),
            server_timeout=30,
        )

        schema = [
            {
                "name": str(row["ColumnName"]),
                "type": str(row["DataType"]),
            }
            for row in rows
            if row.get("ColumnName") and row.get("DataType")
        ]

        if not schema:
            raise SentinelQueryError(
                f"No schema metadata was returned for '{table_name}'."
            )

        logger.info(
            "Discovered schema for table %s: %d columns",
            table_name,
            len(schema),
        )

        return schema
