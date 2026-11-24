
from app.services.keyvault_service import KeyVaultService


def main():
    keyvault = KeyVaultService()

    secret = keyvault.get_secret("outseer-client-secret")

    print("Key Vault authentication successful.")
    print("Secret retrieved successfully:", bool(secret))


if __name__ == "__main__":
    main()
