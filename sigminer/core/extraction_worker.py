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
        self.existing_contacts = {}  # Dictionnaire email => row contact
        self.headers = set(["email_address"])  # Les headers du fichier CSV

    def get_timestamp(self):
        """Retourne l'horodatage actuel."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def log_message(self, message):
        """Écrit un message dans le fichier log."""
        timestamped_message = f"{self.get_timestamp()} - {message}"
        async with aiofiles.open("process_log.txt", "a") as log_file:
            await log_file.write(timestamped_message + "\n")
        self.log_signal.emit(timestamped_message)

    async def load_existing_contacts(self):
        """Charge les contacts existants du fichier CSV."""
        if os.path.exists(self.csv_file_path):
            await self.log_message(
                f"Chargement des contacts existants depuis {self.csv_file_path}"
            )
            async with aiofiles.open(self.csv_file_path, mode="r") as csvfile:
                content = await csvfile.readlines()
                if not content:
                    await self.log_message(f"Le fichier CSV est vide.")
                    return
                reader = csv.DictReader(content)
                if reader.fieldnames is None:
                    await self.log_message(f"Le fichier CSV est corrompu ou vide.")
                    return
                # Sauvegarde des en-têtes existants
                self.headers = set(reader.fieldnames)
                # Mise à jour des contacts existants
                self.existing_contacts = {row["email_address"]: row for row in reader}

    async def write_final_csv(self):
        """Écrit les contacts mis à jour dans le fichier CSV."""
        # S'assurer que les en-têtes incluent tous les champs des contacts
        all_fieldnames = set(self.headers)
        for contact in self.existing_contacts.values():
            all_fieldnames.update(contact.keys())

        async with aiofiles.open(self.csv_file_path, mode="w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
            await self.log_message("Écriture des en-têtes dans le fichier CSV.")
            await writer.writeheader()  # Écrit les en-têtes
            for contact in self.existing_contacts.values():
                # Écrire uniquement les champs qui existent dans les en-têtes
                contact_filtered = {key: contact.get(key, "") for key in all_fieldnames}
                await writer.writerow(contact_filtered)

    async def process_email_meta(self, email: dict, field: FieldConfig):
        field_name = field["field_name"]
        email_content = email.get("body", {}).get("content", "No content")
        email_subject = email.get("subject", "Unknown subject")
        images = email.get("images", [])

        await self.log_message(
            f"Traitement de la meta '{field_name}' pour l'email '{email_subject}'"
        )

        MetaClass: Type[BaseModel] = self.create_dynamic_model(
            field,
            "Cette classe définit les metas et le format requis pour les réponses.",
        )
        query = f"Extraire cette meta: {field_name}. Si impossible, renvoyer null."

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

        await self.log_message(f"Réponse pour {field_name}: {answer.dict()}")
        await self.log_message(f"Coût pour {field_name}: ${cost:.4f}")
        return answer

    async def process_email(self, email: dict):
        """Traite un email et met à jour les metas manquantes ou nulles."""
        email_address = (
            email.get("from", {})
            .get("emailAddress", {})
            .get("address", "Unknown sender")
        )

        if email_address in self.existing_contacts:
            # Contact déjà existant, mise à jour uniquement des champs manquants
            results = self.existing_contacts[email_address]
        else:
            # Nouveau contact
            results = {"email_address": email_address}

        tasks = [
            self.process_email_meta(email, field)
            for field in self.launcher_config["fields"]
            if field["field_name"] not in results
            or results[field["field_name"]] in ["", "0", "null"]
        ]
        answers = await asyncio.gather(*tasks)

        for field, answer in zip(self.launcher_config["fields"], answers):
            if answer.dict().get("answer") != "null":
                results[field["field_name"]] = answer.dict().get("answer", "null")

        self.existing_contacts[email_address] = results
        self.total_contacts_processed += 1

    async def launch_extraction(self):
        """Lance le processus d'extraction et met à jour le fichier CSV à la fin."""
        await self.log_message(f"Configuration du Launcher: {self.launcher_config}")

        max_emails = self.launcher_config.get("max_emails", None)
        await self.log_message(
            f"Nombre max d'emails à traiter : {max_emails or 'None'}"
        )

        # Chargement des contacts existants depuis le fichier CSV
        await self.load_existing_contacts()

        email_manager = EmailManager(self.access_token)
        emails = email_manager.get_emails(max_emails)

        await self.log_message(f"Extraction des emails terminée. Total : {len(emails)}")

        start_time = datetime.now()
        tasks = [self.process_email(email) for email in emails]
        await asyncio.gather(*tasks)
        end_time = datetime.now()

        # Mise à jour du fichier CSV avec les nouvelles données
        await self.write_final_csv()

        self.total_time = end_time - start_time
        average_time_per_email = (
            self.total_time / len(emails) if emails else timedelta()
        )
        average_cost_per_email = self.total_cost / len(emails) if emails else 0.0

        await self.log_message("Tous les emails ont été traités.")
        await self.log_message(f"Coût total des requêtes : ${self.total_cost:.4f}")
        await self.log_message(f"Temps total d'exécution : {self.total_time}")
        await self.log_message(
            f"Temps moyen par email : {average_time_per_email.total_seconds() * 1000:.2f} ms"
        )
        await self.log_message(f"Coût moyen par email : ${average_cost_per_email:.4f}")
        await self.log_message(
            f"Total des contacts traités : {self.total_contacts_processed}"
        )
        await self.log_message(
            f"Total des metas traitées : {self.total_meta_processed}"
        )
        await self.log_message(f"Total des metas trouvées : {self.total_meta_found}")

        # Log des valeurs non nulles pour chaque meta
        for field_name, count in self.meta_non_null_counts.items():
            await self.log_message(
                f"Total des valeurs non nulles pour {field_name}: {count}"
            )

    def create_dynamic_model(self, meta: Dict, model_description="") -> Type[BaseModel]:
        """Crée dynamiquement un modèle Pydantic basé sur la configuration d'une meta."""
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
