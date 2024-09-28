from msal import PublicClientApplication, SerializableTokenCache
import os


class AuthManager:
    # Define the path to the token cache file
    CACHE_PATH = os.path.join(
        os.path.expanduser("~"),
        "Library",
        "Application Support",
        "sigminer",
        "token_cache.bin",
    )

    def __init__(self, client_id, tenant_id):
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.app = PublicClientApplication(client_id, authority=authority)

        self.token_cache = SerializableTokenCache()
        if os.path.exists(self.CACHE_PATH):
            self.token_cache.deserialize(open(self.CACHE_PATH, "r").read())
        self.app.token_cache = self.token_cache

    def get_access_token(self, scopes):
        accounts = self.app.get_accounts()
        if accounts:
            result = self.app.acquire_token_silent(scopes=scopes, account=accounts[0])
            if result and "access_token" in result:
                return result["access_token"]

        result = self.app.acquire_token_interactive(scopes=scopes)
        if "access_token" in result:
            self.save_cache()
            return result["access_token"]
        raise Exception(f"Unable to obtain a token: {result.get('error_description')}")

    def save_cache(self):
        if self.token_cache.has_state_changed:
            os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)
            with open(self.CACHE_PATH, "w") as f:
                f.write(self.token_cache.serialize())
