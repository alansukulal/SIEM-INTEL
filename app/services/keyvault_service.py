
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

from app.config import settings


class KeyVaultService:

    def __init__(self):
        self.credential = ClientSecretCredential(
            tenant_id=settings.keyvault_tenant_id,
            client_id=settings.keyvault_client_id,
            client_secret=settings.keyvault_client_secret,
        )

        self.client = SecretClient(
            vault_url=settings.keyvault_url,
            credential=self.credential,
        )

    def get_secret(self, secret_name: str) -> str:
        if not secret_name:
            raise ValueError("Secret name cannot be empty.")

        secret = self.client.get_secret(secret_name)

        if not secret.value:
            raise ValueError(
                f"Key Vault returned an empty secret: {secret_name}"
            )

        return secret.value
