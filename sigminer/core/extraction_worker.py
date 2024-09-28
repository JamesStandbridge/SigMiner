from PyQt5.QtCore import QThread, pyqtSignal
import asyncio
import aiofiles
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, Type
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

    def __init__(self, access_token: str, launcher_config: LauncherConfig):
        super().__init__()
        self.launcher_config = launcher_config
        self.access_token = access_token
        self.llm = MultiModalLLM()
        self.csv_file_path = launcher_config["file_path"]
        self.total_cost = 0.0
        self.total_time = timedelta()
        self.total_contacts_processed = 0
        self.total_meta_processed = 0
        self.total_meta_found = 0
        self.meta_non_null_counts = {
            field["field_name"]: 0 for field in launcher_config["fields"]
        }

    def get_timestamp(self):
        """Return the current time formatted as a string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def log_message(self, message):
        timestamped_message = f"{self.get_timestamp()} - {message}"
        async with aiofiles.open("process_log.txt", "a") as log_file:
            await log_file.write(timestamped_message + "\n")
        self.log_signal.emit(timestamped_message)

    async def process_email_meta(self, email: dict, field: FieldConfig):
        field_name = field["field_name"]
        email_content = email.get("body", {}).get("content", "No content")
        email_subject = email.get("subject", "Unknown subject")
        images = email.get("images", [])

        await self.log_message(
            f"Processing field '{field_name}' for email '{email_subject}'"
        )

        MetaClass: Type[BaseModel] = self.create_dynamic_model(
            field,
            "This class defines the metas and the format needed for the answers. Always start with the thoughtProcess",
        )
        query: str = (
            f"Extract this meta: {field_name}. If you cannot extract the meta, return null as answer"
        )

        chunks = [
            f"<email_subject>{email_subject}</email_subject>",
            f"<email_content>{email_content}</email_content>",
        ]

        answer, cost = await self.llm.query(
            input_data=query,
            model=self.launcher_config["model"],
            chunks=chunks,
            images=images,
            output_cls=MetaClass,
        )

        self.total_cost += cost
        self.total_meta_processed += 1
        if answer.dict().get("answer") != "null":
            self.total_meta_found += 1
            self.meta_non_null_counts[field_name] += 1

        await self.log_message(f"Answer for {field_name}: {answer.dict()}")
        await self.log_message(f"Cost for {field_name}: ${cost:.4f}")
        return answer

    async def process_email(self, email: dict):
        email_address = (
            email.get("from", {})
            .get("emailAddress", {})
            .get("address", "Unknown sender")
        )
        results = {"email_address": email_address}

        tasks = [
            self.process_email_meta(email, field)
            for field in self.launcher_config["fields"]
        ]
        answers = await asyncio.gather(*tasks)

        for field, answer in zip(self.launcher_config["fields"], answers):
            results[field["field_name"]] = answer.dict().get("answer", "null")

        await self.write_to_csv(results)
        self.total_contacts_processed += 1

    async def write_to_csv(self, results: Dict[str, str]):
        file_exists = os.path.isfile(self.csv_file_path)
        async with aiofiles.open(self.csv_file_path, mode="a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=results.keys())
            if not file_exists:
                await writer.writeheader()
            await writer.writerow(results)

    async def launch_extraction(self):
        await self.log_message(f"Launcher Config: {self.launcher_config}")

        max_emails = self.launcher_config.get("max_emails", None)
        await self.log_message(
            f"Starting email extraction. Max emails: {max_emails or 'None'}"
        )

        email_manager = EmailManager(self.access_token)
        emails = email_manager.get_emails(max_emails)

        await self.log_message(
            f"Email extraction completed. Total emails gathered: {len(emails)}"
        )

        start_time = datetime.now()
        tasks = [self.process_email(email) for email in emails]
        await asyncio.gather(*tasks)
        end_time = datetime.now()

        self.total_time = end_time - start_time
        average_time_per_email = (
            self.total_time / len(emails) if emails else timedelta()
        )
        average_cost_per_email = self.total_cost / len(emails) if emails else 0.0

        await self.log_message("All emails processed.")
        await self.log_message(f"Total cost for all queries: ${self.total_cost:.4f}")
        await self.log_message(f"Total execution time: {self.total_time}")
        average_time_per_email_ms = average_time_per_email.total_seconds() * 1000
        await self.log_message(
            f"Average execution time per email: {average_time_per_email_ms:.2f} ms"
        )
        await self.log_message(f"Average cost per email: ${average_cost_per_email:.4f}")
        await self.log_message(
            f"Total contacts processed: {self.total_contacts_processed}"
        )
        await self.log_message(f"Total meta processed: {self.total_meta_processed}")
        await self.log_message(f"Total meta found: {self.total_meta_found}")

        # Log the number of non-null values for each meta
        for field_name, count in self.meta_non_null_counts.items():
            await self.log_message(f"Total non-null values for {field_name}: {count}")

    def create_dynamic_model(self, meta: Dict, model_description="") -> Type[BaseModel]:
        """Dynamically creates a Pydantic model based on a single meta configuration."""
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
