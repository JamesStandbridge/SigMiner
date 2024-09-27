import requests


class EmailManager:
    def __init__(self, access_token):
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_emails(self, max_emails=10):
        endpoint = "https://graph.microsoft.com/v1.0/me/messages"
        emails = []
        while endpoint and len(emails) < max_emails:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            emails.extend(data.get("value", []))
            endpoint = data.get("@odata.nextLink", None)
        return emails[:max_emails]
