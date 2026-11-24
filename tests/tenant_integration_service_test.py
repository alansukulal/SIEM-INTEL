from app.services.tenant_integration_service import get_tenant_integration


OUTSEER_TENANT_ID = "d34249ab-034e-422f-955d-aa665c1fb6f5"


def main():
    integration = get_tenant_integration(
        tenant_id=OUTSEER_TENANT_ID,
        siem_type="microsoft_sentinel",
    )
    try:
        get_tenant_integration(
            tenant_id="00000000-0000-0000-0000-000000000001",
            siem_type="microsoft_sentinel",
        )
    except ValueError as exc:
        print("Tenant isolation working:", exc)

    print("Tenant integration retrieved successfully")
    print("Tenant ID:", integration["tenant_id"])
    print("SIEM:", integration["siem_type"])
    print("Workspace ID:", integration["workspace_id"])
    print("Credential source:", integration["credential_source"])
    print("Client secret loaded:", bool(integration.get("client_secret")))


if __name__ == "__main__":
    main()