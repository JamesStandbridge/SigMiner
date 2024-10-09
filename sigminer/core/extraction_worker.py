from PyQt5.QtCore import QThread, pyqtSignal
import asyncio
import aiofiles
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, Type, Optional
from pydantic import BaseModel, create_model, Field

from sigminer.core.email.email_manager import EmailManager
from sigminer.core.llm.multi_modal_llm import MultiModalLLM
from sigminer.core.models.extraction import FieldConfig, LauncherConfig
from sigminer.core.utils.prompt_models import (
    THOUGHT_PROCESS_DESCRIPTION,
    get_answer_field_description,
)


class ExtractionWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)  # Signal for updating progress bar

    def __init__(self, access_token: str, launcher_config: LauncherConfig):
        super().__init__()
        self.launcher_config = launcher_config
        self.access_token = access_token
        self.llm = MultiModalLLM()
        self.email_manager = EmailManager(self.access_token)
        self.csv_file_path = launcher_config["file_path"]
        self.total_cost = 0.0
        self.total_time = timedelta()
        self.total_contacts_processed = 0
        self.total_meta_processed = 0
        self.total_meta_found = 0
        self.meta_non_null_counts = {
            field["field_name"]: 0 for field in launcher_config["fields"]
        }
        self.meta_costs = {
            field["field_name"]: 0.0 for field in launcher_config["fields"]
        }
        self.existing_contacts = {}  # Dictionary email => contact row
        self.headers = set(["email_address"])  # CSV file headers

    def get_timestamp(self):
        """Returns the current timestamp."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def log_message(self, message):
        """Writes a message to the log file."""
        timestamped_message = f"{self.get_timestamp()} - {message}"
        async with aiofiles.open("process_log.txt", "a") as log_file:
            await log_file.write(timestamped_message + "\n")
        self.log_signal.emit(timestamped_message)

    async def load_existing_contacts(self):
        """Loads existing contacts from the CSV file."""
        if os.path.exists(self.csv_file_path):
            await self.log_message(
                f"Loading existing contacts from {self.csv_file_path}"
            )
            async with aiofiles.open(self.csv_file_path, mode="r") as csvfile:
                content = await csvfile.readlines()
                if not content:
                    await self.log_message("The CSV file is empty.")
                    return
                reader = csv.DictReader(content)
                if reader.fieldnames is None:
                    await self.log_message("The CSV file is corrupted or empty.")
                    return
                self.headers = set(reader.fieldnames)
                self.existing_contacts = {row["email_address"]: row for row in reader}

    async def write_final_csv(self):
        """Writes the updated contacts to the CSV file."""
        all_fieldnames = set(self.headers)
        for field in self.launcher_config["fields"]:
            all_fieldnames.add(field["field_name"])

        all_fieldnames = ["email_address"] + [
            field for field in all_fieldnames if field != "email_address"
        ]

        async with aiofiles.open(self.csv_file_path, mode="w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
            await self.log_message("Writing headers to the CSV file.")
            await writer.writeheader()
            for contact in self.existing_contacts.values():
                contact_filtered = {key: contact.get(key, "") for key in all_fieldnames}
                await writer.writerow(contact_filtered)

    async def process_email_meta(self, email: dict, field: FieldConfig) -> Optional[BaseModel]:
        field_name = field["field_name"]
        email_content = email.get("body", {}).get("content", "No content")
        email_subject = email.get("subject", "Unknown subject")
        email_address = (
            email.get("from", {}).get("emailAddress", {}).get("address", None)
        )
        images = email.get("images", [])

        await self.log_message(
            f"Processing metadata '{field_name}' for email '{email_subject}'"
        )

        MetaClass: Type[BaseModel] = self.create_dynamic_model(
            field,
            "This class defines the metadata and the required format for responses.",
        )
        query = f"Extract this metadata: {field_name}. If impossible, return null."

        chunks = [
            f"<email_subject>{email_subject}</email_subject>",
            f"<email_content>{email_content}</email_content>",
        ]

        result = await self.llm.query(
            input_data=query,
            model=self.launcher_config["model"],
            chunks=chunks,
            images=images,
            output_cls=MetaClass,
        )

        if result is None:
            await self.log_message(f"Query for {field_name} returned None.")
            return None

        answer, cost = result
        self.total_cost += cost
        self.meta_costs[field_name] += cost
        self.total_meta_processed += 1
        if answer.dict().get("answer") != "null":
            self.total_meta_found += 1
            self.meta_non_null_counts[field_name] += 1

        await self.log_message(
            f"Response for {field_name} from {email_address}: {answer.dict()}"
        )
        return answer

    async def process_email(self, email: dict, total_emails: int):
        """Processes an email and updates missing or null metadata."""
        email_address = (
            email.get("from", {}).get("emailAddress", {}).get("address", None)
        )

        if email_address is None:
            self.total_contacts_processed += 1
            progress = int((self.total_contacts_processed / total_emails) * 100)
            self.progress_signal.emit(progress)
            return

        email_host = email_address.split("@")[-1]
        excluded_hosts = self.launcher_config["excluded_hosts"]
        include_mode = self.launcher_config["include_mode"]

        if excluded_hosts:
            if include_mode and email_host not in excluded_hosts:
                self.total_contacts_processed += 1
                progress = int((self.total_contacts_processed / total_emails) * 100)
                self.progress_signal.emit(progress)
                return
            elif not include_mode and email_host in excluded_hosts:
                self.total_contacts_processed += 1
                progress = int((self.total_contacts_processed / total_emails) * 100)
                self.progress_signal.emit(progress)
                return

        if email_address in self.existing_contacts:
            results = self.existing_contacts[email_address]
        else:
            results = {"email_address": email_address}

        message_id = email.get("id", "")
        images = self.email_manager.get_images_from_text(
            email.get("body", {}).get("content", ""), message_id
        )
        email["images"] = images

        tasks = [
            self.process_email_meta(email, field)
            for field in self.launcher_config["fields"]
            if field["field_name"] not in results
            or results[field["field_name"]] in ["", "0", "null"]
            or (
                field["can_be_overwritten"]
                and results[field["field_name"]] not in ["", "0", "null"]
            )
        ]
        answers = await asyncio.gather(*tasks)

        for field, answer in zip(self.launcher_config["fields"], answers):
            if answer and answer.dict().get("answer") not in ["null", "", "0"]:
                results[field["field_name"]] = answer.dict().get("answer", "null")

        self.existing_contacts[email_address] = results
        self.total_contacts_processed += 1
        # Emit the progress update
        progress = int((self.total_contacts_processed / total_emails) * 100)
        self.progress_signal.emit(progress)

    async def launch_extraction(self):
        """Launches the extraction process and updates the CSV file at the end."""
        await self.log_message(f"Launcher configuration: {self.launcher_config}")

        max_emails = self.launcher_config.get("max_emails", None)
        await self.log_message(
            f"Maximum number of emails to process: {max_emails or 'None'}"
        )

        await self.load_existing_contacts()

        emails = self.email_manager.get_emails(max_emails)

        await self.log_message(
            f"Email extraction completed. Total emails processed: {len(emails)}"
        )

        start_time = datetime.now()
        tasks = [self.process_email(email, len(emails) - 1) for email in emails]
        await asyncio.gather(*tasks)
        end_time = datetime.now()

        await self.write_final_csv()

        self.total_time = end_time - start_time
        average_time_per_email = (
            self.total_time / len(emails) if emails else timedelta()
        )
        average_cost_per_email = self.total_cost / len(emails) if emails else 0.0

        await self.log_message("All emails have been processed successfully.")
        await self.log_message(f"Total request cost: ${self.total_cost:.4f}")
        await self.log_message(f"Total execution time: {self.total_time}")
        await self.log_message(
            f"Average time per email: {average_time_per_email.total_seconds() * 1000:.2f} ms"
        )
        await self.log_message(f"Average cost per email: ${average_cost_per_email:.4f}")
        await self.log_message(
            f"Total contacts processed: {self.total_contacts_processed}"
        )
        await self.log_message(f"Total metadata processed: {self.total_meta_processed}")
        await self.log_message(f"Total metadata found: {self.total_meta_found}")

        for field_name, count in self.meta_non_null_counts.items():
            await self.log_message(f"Total non-null values for {field_name}: {count}")

        for field_name, cost in self.meta_costs.items():
            await self.log_message(f"Total cost for {field_name}: ${cost:.4f}")

        await self.log_message(
            "The extraction process is now complete. You may safely close this thread."
        )

    def create_dynamic_model(self, meta: Dict, model_description="") -> Type[BaseModel]:
        """Dynamically creates a Pydantic model based on the configuration of a metadata."""
        fields = {}
        description = meta.get("field_name", "")
        if guideline := meta.get("guideline"):
            description += f" {guideline}"

        fields["thoughtProcess"] = (str, Field(description=THOUGHT_PROCESS_DESCRIPTION))

        fields["answer"] = (
            str,
            Field(
                description=get_answer_field_description(meta.get("meta"), description)
            ),
        )

        DynamicModel = create_model("MetaExtraction", **fields)
        DynamicModel.__doc__ = model_description
        return DynamicModel

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.launch_extraction())
