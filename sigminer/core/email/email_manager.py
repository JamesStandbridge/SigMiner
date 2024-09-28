import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
import base64
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class EmailManager:
    def __init__(self, access_token: str) -> None:
        self.headers = {"Authorization": f"Bearer {access_token}"}

    def get_emails(self, max_emails: Optional[int] = None) -> List[Dict]:
        """
        Fetches emails from the Microsoft Graph API.

        Args:
            max_emails (Optional[int]): Maximum number of emails to fetch. If None, fetches all emails.

        Returns:
            List[Dict]: A list of email data dictionaries.
        """
        endpoint = "https://graph.microsoft.com/v1.0/me/messages"
        emails: List[Dict] = []
        while endpoint and (max_emails is None or len(emails) < max_emails):
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            emails.extend(data.get("value", []))
            endpoint = data.get("@odata.nextLink", None)
        return emails if max_emails is None else emails[:max_emails]

    def extract_images_from_text(self, text: str) -> List[str]:
        """
        Extracts image content IDs from the HTML text.

        Args:
            text (str): The HTML content of the email.

        Returns:
            List[str]: A list of image content IDs.
        """
        soup = BeautifulSoup(text, "html.parser")
        images = soup.find_all("img")
        image_cids: List[str] = [
            img["src"].replace("cid:", "")
            for img in images
            if "src" in img.attrs and img["src"].startswith("cid:")
        ]
        return image_cids

    def fetch_image_attachments(
        self, message_id: str, cids: List[str]
    ) -> Dict[str, str]:
        """
        Fetches image attachments from an email by content IDs.

        Args:
            message_id (str): The ID of the email message.
            cids (List[str]): A list of content IDs to fetch.

        Returns:
            Dict[str, str]: A dictionary mapping content IDs to base64-encoded image data.
        """
        logger.info(f"Fetching image attachments for message {message_id}")
        attachments_endpoint = (
            f"https://graph.microsoft.com/v1.0/me/messages/{message_id}/attachments"
        )
        response = requests.get(attachments_endpoint, headers=self.headers)
        response.raise_for_status()
        attachments = response.json().get("value", [])

        images: Dict[str, str] = {}
        for attachment in attachments:
            if attachment.get("contentId") in cids:
                image_data = attachment.get("contentBytes")
                images[attachment["contentId"]] = image_data

        return images

    def get_images_from_text(self, text: str, message_id: str) -> List[bytes]:
        """
        Extracts and decodes image attachments from an email's HTML content.

        Args:
            text (str): The HTML content of the email.
            message_id (str): The ID of the email message.

        Returns:
            List[bytes]: A list of image data in bytes.
        """
        image_cids = self.extract_images_from_text(text)
        if not image_cids:
            return []

        images = self.fetch_image_attachments(message_id, image_cids)
        image_bytes_list: List[bytes] = []

        for _, image_data in images.items():
            image_bytes = base64.b64decode(image_data)
            image_bytes_list.append(image_bytes)

        return image_bytes_list
