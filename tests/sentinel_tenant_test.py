from app.config import settings
from app.services.tenant_integration_service import get_tenant_integration
from app.tools.sentinel import SentinelClient


def main():
    integration = get_tenant_integration(
        tenant_id=settings.dev_tenant_id,
        siem_type="microsoft_sentinel",
    )

    sentinel = SentinelClient(integration)

    print("Sentinel client initialized successfully.")

    results = sentinel.run_query(
        "print TestMessage = 'SIEM-INTEL connection successful'",
    )

    print("Query executed successfully.")
    print("Rows returned:", len(results))
    print("Workspace:", integration["workspace_id"])


if __name__ == "__main__":
    main()