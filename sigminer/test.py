import os
import requests
import logging
from msal import PublicClientApplication

# Configuration
CLIENT_ID = "dab49510-cf7e-442f-b5a4-60f1f44b8610"
TENANT_ID = "ad0c9bcb-86b9-4df0-aa79-5064609889a5"  # Utilisez 'common' pour un compte personnel ou multitenant
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["User.Read", "Mail.Read"]

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Créer l'application cliente publique
app = PublicClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
)


# Obtenir un token d'accès via une authentification interactive
def get_access_token():
    logger.info("Attempting to acquire access token interactively.")
    result = app.acquire_token_interactive(scopes=SCOPE)
    if "access_token" in result:
        logger.info("Access token acquired successfully.")
        return result["access_token"]
    else:
        error_msg = f"Impossible d'obtenir un token: {result.get('error')}, {result.get('error_description')}"
        logger.error(error_msg)
        raise Exception(error_msg)


def get_emails(access_token, max_emails=10):
    logger.info("Fetching emails from Microsoft Graph API.")
    headers = {"Authorization": f"Bearer {access_token}"}
    endpoint = "https://graph.microsoft.com/v1.0/me/messages"

    emails = []
    while endpoint and len(emails) < max_emails:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()

        emails.extend(data.get("value", []))

        endpoint = data.get("@odata.nextLink", None)

    return emails[:max_emails]


if __name__ == "__main__":
    try:
        access_token = get_access_token()
        logger.info(f"Access Token: {access_token}")

        max_emails = 50

        emails = get_emails(access_token, max_emails)
        logger.info(f"{len(emails)} emails récupérés :")

        for email in emails:
            from_info = (
                email.get("from", {})
                .get("emailAddress", {})
                .get("name", "Expéditeur inconnu")
            )
            subject = email.get("subject", "Sans sujet")
            body = email.get("body", {}).get("content", "Pas de contenu")

            logger.info(f"De: {from_info} - Sujet: {subject}")
            logger.info(f"Contenu: {body}")

    except Exception as e:
        logger.error(f"Une erreur est survenue: {e}")
