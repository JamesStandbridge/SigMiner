from PyQt5.QtCore import QThread, pyqtSignal

import asyncio
import aiofiles
from datetime import datetime  # Add this import for timestamps

from sigminer.core.email.email_manager import EmailManager


from typing import TypedDict, List


class FieldConfig(TypedDict):
    field_name: str
    guideline: str


class LauncherConfig(TypedDict):
    fields: List[FieldConfig]
    excluded_hosts: List[str]
    include_mode: bool
    file_path: str
    max_emails: int


class ExtractionWorker(QThread):
    log_signal = pyqtSignal(str)  # Signal for sending logs to the UI

    def __init__(self, access_token: str, launcher_config: LauncherConfig):
        super().__init__()
        self.launcher_config = launcher_config
        self.access_token = access_token

    def get_timestamp(self):
        """Return the current time formatted as a string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def log_message(self, message):
        timestamped_message = f"{self.get_timestamp()} - {message}"
        async with aiofiles.open("process_log.txt", "a") as log_file:
            await log_file.write(timestamped_message + "\n")
        self.log_signal.emit(
            timestamped_message
        )  # Send the log with timestamp to the UI

    async def send_message(self, email, message_content):
        email_address = email.get("emailAddress", {}).get("address", "Unknown")
        await self.log_message(f"Sending message to {email_address}...")
        await asyncio.sleep(2)  # Simulate sending delay
        await self.log_message(f"Message sent to {email_address}.")

    async def launch_extraction(self):
        # Log all the launch config at the start
        await self.log_message(f"Launcher Config: {self.launcher_config}")

        max_emails = self.launcher_config.get("max_emails", None)
        if max_emails:
            await self.log_message(
                f"Starting email extraction. Maximum emails to process: {max_emails}."
            )
        else:
            await self.log_message(
                "Starting email extraction. No maximum email limit set."
            )

        email_manager = EmailManager(self.access_token)
        self.emails = email_manager.get_emails(max_emails)

        await self.log_message(
            f"Email extraction completed. Total emails gathered: {len(self.emails)}."
        )

        print(self.emails)

        tasks = []
        for email in self.emails:
            # tasks.append(self.send_message(email, message_content))
            from_info = (
                email.get("from", {})
                .get("emailAddress", {})
                .get("name", "Expéditeur inconnu")
            )
            subject = email.get("subject", "Sans sujet")
            body = email.get("body", {}).get("content", "Pas de contenu")
            await self.log_message(f"from: {from_info}")
            await self.log_message(f"subject: {subject}")

        # await asyncio.gather(*tasks)  # Send all messages in parallel
        await self.log_message("All messages sent.")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.launch_extraction())
