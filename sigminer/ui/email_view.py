import hashlib
import json
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QMessageBox,
    QInputDialog,
    QScrollArea,
    QListWidget,
    QLineEdit,
    QFileDialog,
    QFrame,
    QDialog,
    QTextEdit,
)
from PyQt5.QtGui import QFont

from sigminer.ui.extraction_view import ExtractionView
from sigminer.ui.field_form_view import FieldFormView
from sigminer.config.config_manager import ConfigManager


class EmailView(QWidget):
    def __init__(self, access_token):
        super().__init__()
        self.access_token = access_token
        self.config_manager = ConfigManager()
        self.field_forms = []
        self.excluded_hosts = []  # Liste des domaines à exclure
        self.include_mode = False  # Par défaut, "include" mode

        self.original_preset_hash = None  # Stocke le hash du preset chargé
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Scroll area for the entire layout
        main_scroll_area = QScrollArea(self)
        main_scroll_area.setWidgetResizable(True)
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_scroll_area.setWidget(main_container)
        layout.addWidget(main_scroll_area)

        # Set maximum height for the main scroll area
        main_scroll_area.setFixedHeight(600)

        # Set fixed width for the window
        self.setFixedWidth(800)

        # Sélection des presets
        self.preset_selector = QComboBox(self)
        self.preset_selector.addItems(
            ["Select preset"] + self.config_manager.get_all_presets()
        )
        self.preset_selector.currentTextChanged.connect(self.load_preset)
        main_layout.addWidget(self.preset_selector)

        # Label to indicate fields to extract from emails
        self.fields_label = QLabel("Fields to extract from emails:")
        main_layout.addWidget(self.fields_label)

        # Scroll area for fields
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        # Espace pour les champs d'extraction
        fields_container = QWidget()
        self.fields_layout = QVBoxLayout(fields_container)
        scroll_area.setWidget(fields_container)
        main_layout.addWidget(scroll_area)

        # Set maximum height for scroll area to avoid full overflow
        scroll_area.setFixedHeight(300)
        # Bouton pour ajouter un champ
        self.add_field_button = QPushButton("Add Field", self)
        self.add_field_button.clicked.connect(lambda: self.add_field_form())
        main_layout.addWidget(self.add_field_button)

        # Section pour la liste des domaines d'e-mails à exclure
        self.hosts_label = QLabel("Excluded email hosts (double-click to delete):")
        main_layout.addWidget(self.hosts_label)

        self.excluded_hosts_input = QLineEdit(self)
        self.excluded_hosts_input.setPlaceholderText(
            "Enter email host (e.g., gmail.com)"
        )
        self.excluded_hosts_input.returnPressed.connect(self.add_excluded_host)
        main_layout.addWidget(self.excluded_hosts_input)

        self.excluded_hosts_list = QListWidget(self)
        self.excluded_hosts_list.itemDoubleClicked.connect(
            self.remove_excluded_host
        )  # Ajout d'un signal pour double-clic
        main_layout.addWidget(self.excluded_hosts_list)

        # Switch pour indiquer si la liste de hosts est à inclure ou à exclure
        self.host_mode_switch = QComboBox(self)
        self.host_mode_switch.addItems(["Include Hosts", "Exclude Hosts"])
        self.host_mode_switch.setCurrentIndex(0 if self.include_mode else 1)
        self.host_mode_switch.currentIndexChanged.connect(self.on_host_mode_changed)
        main_layout.addWidget(self.host_mode_switch)

        # Bouton pour choisir le chemin de fichier
        self.file_path_button = QPushButton("Select File to Save Contacts", self)
        self.file_path_button.clicked.connect(self.open_file_dialog)
        main_layout.addWidget(self.file_path_button)

        # Label for max emails input
        self.max_emails_label = QLabel("Max emails to process (leave empty for all):")
        main_layout.addWidget(self.max_emails_label)

        # Input for max amount of emails to process
        self.max_emails_input = QLineEdit(self)
        self.max_emails_input.setPlaceholderText(
            "Enter max emails to process (leave empty for no max)"
        )
        main_layout.addWidget(self.max_emails_input)
        # Champ select pour le modèle OpenAI
        self.model_selector_label = QLabel("Select OpenAI Model:")
        main_layout.addWidget(self.model_selector_label)

        self.model_selector = QComboBox(self)
        self.model_selector.addItems(
            [
                "gpt-4o",
                "gpt-4o-2024-08-06",
                "gpt-4o-mini",
                "o1-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo-0125",
            ]
        )
        self.model_selector.setCurrentIndex(0)  # Set default selected value
        main_layout.addWidget(self.model_selector)

        # Button to show model pricing
        self.model_pricing_button = QPushButton("Show Model Pricing", self)
        self.model_pricing_button.clicked.connect(self.show_model_pricing)
        main_layout.addWidget(self.model_pricing_button)

        # Layout for save and delete preset buttons
        preset_buttons_layout = QHBoxLayout()

        # Bouton pour sauvegarder un preset (initialement caché)
        self.save_preset_button = QPushButton("Save Preset", self)
        self.save_preset_button.clicked.connect(self.save_preset)
        self.save_preset_button.hide()
        self.save_preset_button.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 3px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """
        )

        # Bouton pour supprimer un preset
        self.delete_preset_button = QPushButton("Delete Preset", self)
        self.delete_preset_button.clicked.connect(self.delete_preset)
        self.delete_preset_button.setStyleSheet(
            """
            QPushButton {
                background-color: white;
                padding: 3px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d3d3d3;
            }
        """
        )
        preset_buttons_layout.addWidget(self.delete_preset_button)
        preset_buttons_layout.addWidget(self.save_preset_button)

        main_layout.addLayout(preset_buttons_layout)

        # Spacer between preset buttons and launch button
        spacer = QFrame(self)
        spacer.setFrameShape(QFrame.HLine)
        spacer.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(spacer)

        # Bouton d'extraction
        self.launch_button = QPushButton("Launch Extraction", self)
        self.launch_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.launch_button.setStyleSheet(
            """
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:disabled {
                background-color: #d3d3d3;
                color: #a0a0a0;
            }
            QPushButton:hover:!disabled {
                background-color: #0056b3;
            }
        """
        )
        self.launch_button.clicked.connect(self.launch_service)
        main_layout.addWidget(self.launch_button)

        self.setLayout(layout)
        self.setWindowTitle("SigMiner Launcher")

        # Initial state of delete button
        self.update_delete_button_visibility()
        # Initial state of launch button
        self.update_launch_button_visibility()

    def launch_service(self):
        try:
            # Collect all the configured settings
            fields = [field_form.get_field_data() for field_form in self.field_forms]
            include_mode = self.host_mode_switch.currentIndex() == 0
            config_data = {
                "fields": fields,
                "excluded_hosts": self.excluded_hosts,
                "include_mode": include_mode,
                "file_path": self.file_path_button.text(),
                "max_emails": (
                    int(self.max_emails_input.text())
                    if self.max_emails_input.text()
                    else None
                ),
                "model": self.model_selector.currentText(),  # Add selected model to config
            }

            # Créer la modal et lancer le processus en arrière-plan
            modal = ExtractionView(self, self.access_token, config_data)
            modal.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch service: {e}")

    def show_launch_modal(self, data):
        modal = ExtractionView(self, data)
        modal.exec_()

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            if not file_path.endswith(".csv"):
                file_path += ".csv"  # Forcer l'extension CSV si elle n'est pas présente
            self.file_path_button.setText(file_path)  # Use the file path as button text
            self.on_field_modified()  # Mettre à jour l'état de modification

    def add_field_form(self, field_name="", guideline="", can_be_overwritten=False):
        field_form = FieldFormView(
            self.remove_field_form, str(field_name), str(guideline), can_be_overwritten
        )
        self.fields_layout.addWidget(field_form)
        self.field_forms.append(field_form)

        # Connect signals for field modification
        field_form.field_name_input.textChanged.connect(self.on_field_modified)
        field_form.guideline_input.textChanged.connect(self.on_field_modified)

        self.update_save_preset_button_visibility()
        self.update_launch_button_visibility()

    def remove_field_form(self, field_form):
        self.fields_layout.removeWidget(field_form)
        field_form.setParent(None)
        self.field_forms.remove(field_form)
        self.update_save_preset_button_visibility()
        self.update_launch_button_visibility()

    def add_excluded_host(self):
        host = self.excluded_hosts_input.text().strip()
        if host and host not in self.excluded_hosts:
            self.excluded_hosts.append(host)
            self.excluded_hosts_list.addItem(host)
            self.excluded_hosts_input.clear()
            self.on_field_modified()

    def remove_excluded_host(self, item):
        # Suppression du domaine exclu lors du double-clic
        host = item.text()
        if host in self.excluded_hosts:
            self.excluded_hosts.remove(host)
            self.excluded_hosts_list.takeItem(self.excluded_hosts_list.row(item))
            self.on_field_modified()

    def save_preset(self):
        fields = [field_form.get_field_data() for field_form in self.field_forms]
        include_mode = self.host_mode_switch.currentIndex() == 0

        preset_data = {
            "fields": fields,
            "excluded_hosts": self.excluded_hosts,
            "include_mode": include_mode,
            "file_path": self.file_path_button.text(),  # Use button text for file path
            "max_emails": self.max_emails_input.text(),
            "model": self.model_selector.currentText(),  # Add selected model to preset
        }

        current_preset_name = self.preset_selector.currentText()
        if current_preset_name == "Select preset":
            current_preset_name = ""

        preset_name, ok = QInputDialog.getText(
            self, "Save Preset", "Enter preset name:", text=current_preset_name
        )

        if ok and preset_name:
            self.config_manager.save_preset(preset_name, preset_data)
            self.original_preset_hash = self.get_preset_hash(preset_data)  # Update hash
            self.update_preset_selector(preset_name)
            self.update_save_preset_button_visibility()

    def update_preset_selector(self, selected_preset):
        self.preset_selector.clear()
        self.preset_selector.addItems(
            ["Select preset"] + self.config_manager.get_all_presets()
        )
        index = self.preset_selector.findText(selected_preset)
        if index >= 0:
            self.preset_selector.setCurrentIndex(index)
        self.update_delete_button_visibility()

    def delete_preset(self):
        preset_name = self.preset_selector.currentText()
        if preset_name == "Select preset":
            QMessageBox.warning(self, "Error", "No preset selected.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Preset",
            f"Are you sure you want to delete '{preset_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.config_manager.delete_preset(preset_name)
            self.preset_selector.removeItem(self.preset_selector.currentIndex())
            self.clear_field_forms()
            self.excluded_hosts_list.clear()
            self.update_delete_button_visibility()

    def load_preset(self, preset_name):
        if preset_name != "Select preset":
            preset_data = self.config_manager.get_preset(preset_name)
            self.clear_field_forms()

            # Charger les champs d'extraction
            for field in preset_data.get("fields", []):
                self.add_field_form(
                    field["field_name"],
                    field["guideline"],
                    field.get("can_be_overwritten", False),
                )

            # Charger les domaines d'emails
            self.excluded_hosts = preset_data.get("excluded_hosts", [])
            self.excluded_hosts_list.clear()
            for host in self.excluded_hosts:
                self.excluded_hosts_list.addItem(host)

            # Charger l'état du switch
            self.host_mode_switch.setCurrentIndex(
                0 if preset_data.get("include_mode", True) else 1
            )

            # Charger le chemin du fichier
            file_path = preset_data.get("file_path", "No file selected")
            self.file_path_button.setText(file_path)  # Use button text for file path

            # Charger le nombre maximum d'emails
            max_emails = preset_data.get("max_emails", "")
            self.max_emails_input.setText(max_emails)

            # Charger le modèle OpenAI
            model = preset_data.get("model", "")
            index = self.model_selector.findText(model)
            if index >= 0:
                self.model_selector.setCurrentIndex(index)

            self.update_hosts_label()

            self.original_preset_hash = self.get_preset_hash(preset_data)

        self.update_save_preset_button_visibility()
        self.update_delete_button_visibility()  # Ensure delete button visibility is updated
        self.update_launch_button_visibility()

    def clear_field_forms(self):
        for field_form in self.field_forms:
            field_form.setParent(None)
        self.field_forms = []

    def update_save_preset_button_visibility(self):
        fields = [field_form.get_field_data() for field_form in self.field_forms]
        include_mode = self.host_mode_switch.currentIndex() == 0

        preset_data = {
            "fields": fields,
            "excluded_hosts": self.excluded_hosts,
            "include_mode": include_mode,
            "model": self.model_selector.currentText(),  # Add selected model to hash calculation
        }
        current_hash = self.get_preset_hash(preset_data)
        if len(self.field_forms) > 0 and current_hash != self.original_preset_hash:
            self.save_preset_button.show()
        else:
            self.save_preset_button.hide()

    def on_field_modified(self):
        self.update_save_preset_button_visibility()
        self.update_launch_button_visibility()

    def get_preset_hash(self, preset_data):
        preset_string = json.dumps(preset_data, sort_keys=True)
        return hashlib.md5(preset_string.encode()).hexdigest()

    def update_delete_button_visibility(self):
        if self.preset_selector.currentText() == "Select preset":
            self.delete_preset_button.hide()
        else:
            self.delete_preset_button.show()

    def on_host_mode_changed(self):
        self.on_field_modified()
        self.update_hosts_label()

    def update_hosts_label(self):
        if self.host_mode_switch.currentIndex() == 0:
            self.hosts_label.setText("Included email hosts (double-click to delete):")
        else:
            self.hosts_label.setText("Excluded email hosts (double-click to delete):")

    def update_launch_button_visibility(self):
        if (
            len(self.field_forms) > 0
            and self.file_path_button.text() != "No file selected"
        ):
            self.launch_button.setEnabled(True)
        else:
            self.launch_button.setEnabled(False)

    def show_model_pricing(self):
        pricing_info = [
            ("gpt-4o", "$5.00 / 1M input tokens", "$15.00 / 1M output tokens"),
            (
                "gpt-4o-2024-08-06",
                "$2.50 / 1M input tokens",
                "$10.00 / 1M output tokens",
            ),
            ("gpt-4o-mini", "$0.150 / 1M input tokens", "$0.600 / 1M output tokens"),
            ("o1-mini", "$3.00 / 1M input tokens", "$12.00 / 1M output tokens"),
            ("gpt-4-turbo", "$10.00 / 1M tokens", "$30.00 / 1M tokens"),
            ("gpt-3.5-turbo-0125", "$0.50 / 1M tokens", "$1.50 / 1M tokens"),
        ]

        dialog = QDialog(self)
        dialog.setWindowTitle("Model Pricing")
        dialog.resize(600, 300)  # Make the modal wider and taller
        layout = QVBoxLayout(dialog)

        explanation = QTextEdit(dialog)
        explanation.setReadOnly(True)
        explanation.setHtml(
            """
            <p><b>What is a token?</b></p>
            <p>A token is a unit of text that the model processes. Tokens can be as short as one character or as long as one word (e.g., "a", "apple"). For example, the word "email" is one token, while the sentence "I received an email" is four tokens.</p>
            <p>When processing emails, the number of tokens will depend on the length and complexity of the email content. For instance, a short email might be 50 tokens, while a longer email could be 200 tokens or more.</p>
            """
        )
        layout.addWidget(explanation)

        table = QTextEdit(dialog)
        table.setReadOnly(True)

        table_html = "<table border='1' style='width:100%; border-collapse: collapse;'>"
        table_html += (
            "<tr><th>Model</th><th>Input Tokens</th><th>Output Tokens</th></tr>"
        )

        for model, input_price, output_price in pricing_info:
            table_html += f"<tr><td>{model}</td><td>{input_price}</td><td>{output_price}</td></tr>"

        table_html += "</table>"

        table.setHtml(table_html)
        layout.addWidget(table)

        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec_()
