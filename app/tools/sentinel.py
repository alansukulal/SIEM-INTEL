
from datetime import timedelta
import logging
import re

from azure.core.exceptions import AzureError
from azure.identity import ClientSecretCredential
from azure.monitor.query import (
    LogsQueryClient,
    LogsQueryStatus,
)

from app.config import settings


logger = logging.getLogger(__name__)


class SentinelQueryError(RuntimeError):
    """Raised when a Sentinel query cannot be completed reliably."""


class SentinelClient:
    def __init__(self) -> None:
        self.credential = ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )

        self.client = LogsQueryClient(self.credential)
        self.workspace_id = settings.azure_workspace_id

    def run_query(
        self,
        kql: str,
        *,
        timespan: timedelta = timedelta(hours=1),
        server_timeout: int = 30,
    ) -> list[dict]:
        """Execute a KQL query against the configured Log Analytics workspace."""
        if not kql or not kql.strip():
            raise ValueError("KQL query cannot be empty.")

        if not 1 <= server_timeout <= 600:
            raise ValueError(
                "server_timeout must be between 1 and 600 seconds."
            )

        try:
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=kql,
                timespan=timespan,
                server_timeout=server_timeout,
            )
        except AzureError as exc:
            # Avoid logging credentials or the full query.
            logger.warning(
                "Sentinel query request failed. Error type: %s",
                type(exc).__name__,
            )
            raise SentinelQueryError(
                "Sentinel query request failed. Check Azure permissions, "
                "KQL syntax, and service availability."
            ) from exc

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
