from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SIEM-INTEL"
    environment: str = "development"

    openai_api_key: str
    tavily_api_key: str | None = None

    database_url: str
    dev_tenant_id: str
    keyvault_url: str
    keyvault_tenant_id: str
    keyvault_client_id: str
    keyvault_client_secret: str



    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

settings = Settings()