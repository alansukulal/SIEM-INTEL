from datetime import timedelta

from azure.identity import ClientSecretCredential
from azure.monitor.query import LogsQueryClient

from app.config import settings


class SentinelClient:
    def __init__(self) -> None:
        self.credential = ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )

        self.client = LogsQueryClient(self.credential)
        self.workspace_id = settings.azure_workspace_id

    def run_query(self, kql: str):
        response = self.client.query_workspace(
            workspace_id=self.workspace_id,
            query=kql,
            timespan=timedelta(hours=1),
        )

        if not response.tables:
            return []

        table = response.tables[0]

        return [
            dict(zip(table.columns, row))
            for row in table.rows
        ]