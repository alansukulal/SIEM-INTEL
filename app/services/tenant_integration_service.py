
from sqlalchemy import create_engine, text

from app.config import settings


engine = create_engine(settings.database_url)


def get_tenant_integration(tenant_id: str, siem_type: str) -> dict:
    with engine.connect() as connection:
        integration = connection.execute(
            text("""
                SELECT
                    tenant_id,
                    siem_type,
                    azure_tenant_id,
                    client_id,
                    workspace_id,
                    secret_name,
                    credential_source,
                    is_active
                FROM tenant_integrations
                WHERE tenant_id = :tenant_id
                  AND siem_type = :siem_type
                  AND is_active = TRUE
            """),
            {
                "tenant_id": tenant_id,
                "siem_type": siem_type,
            },
        ).mappings().one_or_none()

    if integration is None:
        raise ValueError(
            f"No active {siem_type} integration found for this tenant"
        )

    integration = dict(integration)

    if integration["credential_source"] == "environment":
        if settings.environment != "development":
            raise ValueError(
                "Environment-based customer credentials are only "
                "allowed in development"
            )

        # Development-only: these environment credentials currently
        # belong to the registered Outseer integration.
        integration["client_secret"] = settings.azure_client_secret

    elif integration["credential_source"] == "key_vault":
        raise NotImplementedError(
            "Key Vault credential retrieval has not been implemented yet"
        )

    else:
        raise ValueError("Unsupported credential source")

    return integration
