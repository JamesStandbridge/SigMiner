import hashlib
import json
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QMessageBox,
    QInputDialog,
    QScrollArea,
    QListWidget,
    QLineEdit,
)
from sigminer.core.email.email_manager import EmailManager
from sigminer.ui.field_form_view import FieldFormView
from sigminer.config.config_manager import ConfigManager


class EmailView(QWidget):
    def __init__(self, access_token):
        super().__init__()
        self.access_token = access_token
        self.config_manager = ConfigManager()
        self.field_forms = []
        self.excluded_hosts = []  # Liste des domaines à exclure
        self.include_mode = True  # Par défaut, "include" mode

        self.original_preset_hash = None  # Stocke le hash du preset chargé
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Sélection des presets
        self.preset_selector = QComboBox(self)
        self.preset_selector.addItems(
            ["Select preset"] + self.config_manager.get_all_presets()
        )
        self.preset_selector.currentTextChanged.connect(self.load_preset)
        layout.addWidget(self.preset_selector)

        # Bouton pour ajouter un champ
        self.add_field_button = QPushButton("Add Field", self)
        self.add_field_button.clicked.connect(lambda: self.add_field_form())
        layout.addWidget(self.add_field_button)

        # Scroll area for fields
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)

        # Espace pour les champs d'extraction
        fields_container = QWidget()
        self.fields_layout = QVBoxLayout(fields_container)
        scroll_area.setWidget(fields_container)
        layout.addWidget(scroll_area)

        # Set maximum height for scroll area to avoid full overflow
        scroll_area.setFixedHeight(300)

        # Section pour la liste des domaines d'e-mails à exclure
        layout.addWidget(QLabel("Excluded email hosts (double-click to delete):"))

        self.excluded_hosts_input = QLineEdit(self)
        self.excluded_hosts_input.setPlaceholderText(
            "Enter email host (e.g., gmail.com)"
        )
        self.excluded_hosts_input.returnPressed.connect(self.add_excluded_host)
        layout.addWidget(self.excluded_hosts_input)

        self.excluded_hosts_list = QListWidget(self)
        self.excluded_hosts_list.itemDoubleClicked.connect(
            self.remove_excluded_host
        )  # Ajout d'un signal pour double-clic
        layout.addWidget(self.excluded_hosts_list)

        # Switch pour indiquer si la liste de hosts est à inclure ou à exclure
        self.host_mode_switch = QComboBox(self)
        self.host_mode_switch.addItems(["Include Hosts", "Exclude Hosts"])
        self.host_mode_switch.currentIndexChanged.connect(self.on_field_modified)
        layout.addWidget(self.host_mode_switch)

        # Bouton pour sauvegarder un preset (initialement caché)
        self.save_preset_button = QPushButton("Save Preset", self)
        self.save_preset_button.clicked.connect(self.save_preset)
        self.save_preset_button.hide()  # Caché par défaut
        layout.addWidget(self.save_preset_button)

        # Bouton pour supprimer un preset
        self.delete_preset_button = QPushButton("Delete Preset", self)
        self.delete_preset_button.clicked.connect(self.delete_preset)
        layout.addWidget(self.delete_preset_button)

        # Bouton d'extraction
        self.extract_button = QPushButton("Extract Emails", self)
        self.extract_button.clicked.connect(self.extract_emails)
        layout.addWidget(self.extract_button)

        self.setLayout(layout)
        self.setWindowTitle("Email Extraction")

        # Initial state of delete button
        self.update_delete_button_visibility()

    def add_field_form(self, field_name="", guideline="", field_type="TEXT"):
        field_form = FieldFormView(
            self.remove_field_form, str(field_name), str(guideline), str(field_type)
        )
        self.fields_layout.addWidget(field_form)
        self.field_forms.append(field_form)

        # Connect signals for field modification
        field_form.field_name_input.textChanged.connect(self.on_field_modified)
        field_form.guideline_input.textChanged.connect(self.on_field_modified)
        field_form.type_selector.currentIndexChanged.connect(self.on_field_modified)

        self.update_save_preset_button_visibility()

    def remove_field_form(self, field_form):
        self.fields_layout.removeWidget(field_form)
        field_form.setParent(None)
        self.field_forms.remove(field_form)
        self.update_save_preset_button_visibility()

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
                    field["field_name"], field["guideline"], field["type"]
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

            self.original_preset_hash = self.get_preset_hash(preset_data)

        self.update_save_preset_button_visibility()

    def clear_field_forms(self):
        for field_form in self.field_forms:
            field_form.setParent(None)
        self.field_forms = []

    def extract_emails(self):
        try:
            email_manager = EmailManager(self.access_token)
            emails = email_manager.get_emails(
                excluded_hosts=self.excluded_hosts
            )  # Exclure les emails
            self.result_label.setText(f"{len(emails)} emails extracted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to extract emails: {e}")

    def update_save_preset_button_visibility(self):
        fields = [field_form.get_field_data() for field_form in self.field_forms]
        include_mode = self.host_mode_switch.currentIndex() == 0

        preset_data = {
            "fields": fields,
            "excluded_hosts": self.excluded_hosts,
            "include_mode": include_mode,
        }
        current_hash = self.get_preset_hash(preset_data)
        if len(self.field_forms) > 0 and current_hash != self.original_preset_hash:
            self.save_preset_button.show()
        else:
            self.save_preset_button.hide()

    def on_field_modified(self):
        self.update_save_preset_button_visibility()

    def get_preset_hash(self, preset_data):
        preset_string = json.dumps(preset_data, sort_keys=True)
        return hashlib.md5(preset_string.encode()).hexdigest()

    def update_delete_button_visibility(self):
        if self.preset_selector.currentText() == "Select preset":
            self.delete_preset_button.hide()
        else:
            self.delete_preset_button.show()
