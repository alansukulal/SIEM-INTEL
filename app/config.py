from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SIEM-INTEL"
    environment: str = "development"

    azure_tenant_id: str
    azure_client_id: str
    azure_client_secret: str
    azure_workspace_id: str
    openai_api_key: str
    tavily_api_key: str | None = None


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()