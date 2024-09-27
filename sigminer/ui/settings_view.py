from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QSpacerItem,
    QSizePolicy,
)
from PyQt5.QtGui import QFont
from sigminer.config.config_manager import ConfigManager


class SettingsView(QWidget):
    def __init__(self, go_back_callback):
        super().__init__()
        self.config_manager = ConfigManager()
        self.go_back_callback = go_back_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Label pour représenter le contenu de la page "Settings"
        self.page_label = QLabel("Settings", self)
        self.page_label.setFont(QFont("Arial", weight=QFont.Bold))  # Set font to bold
        layout.addWidget(self.page_label)

        # Champ pour entrer la clé d'API
        self.api_key_label = QLabel("API Key:", self)
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setPlaceholderText("Enter your API Key")
        self.api_key_input.setText(self.config_manager.get_api_key() or "")

        # Layout for API Key input and label
        api_key_layout = QVBoxLayout()
        api_key_layout.setSpacing(5)
        api_key_layout.addWidget(self.api_key_label)
        api_key_layout.addWidget(self.api_key_input)

        layout.addLayout(api_key_layout)

        # Spacer for better spacing between form and buttons
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Bouton pour sauvegarder la clé d'API
        self.save_button = QPushButton("Save Changes", self)
        self.save_button.clicked.connect(self.save_api_key)
        layout.addWidget(self.save_button)

        # Bouton pour revenir en arrière
        self.back_button = QPushButton("Back", self)
        self.back_button.clicked.connect(self.go_back_callback)
        layout.addWidget(self.back_button)

        self.setLayout(layout)
        self.setWindowTitle("Settings")

    def save_api_key(self):
        api_key = self.api_key_input.text()
        if api_key:
            self.config_manager.set_api_key(api_key)
            QMessageBox.information(self, "Success", "API Key saved successfully")
        else:
            QMessageBox.warning(self, "Error", "API Key cannot be empty")
