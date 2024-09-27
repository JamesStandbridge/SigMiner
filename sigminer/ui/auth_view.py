from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QLabel,
    QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from sigminer.auth.auth_manager import AuthManager
from sigminer.config.config_manager import ConfigManager


class AuthView(QWidget):
    def __init__(self, on_authenticated_callback):
        super().__init__()
        self.config_manager = ConfigManager()
        self.on_authenticated_callback = on_authenticated_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Ajouter des marges pour tout le formulaire
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # Titre de l'authentification
        title_label = QLabel("Authentication", self)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Container for input fields
        input_container = QVBoxLayout()
        input_container.setSpacing(10)

        # Label et champ de saisie pour le Client ID
        client_id_label = QLabel("Client ID:", self)
        client_id_label.setFont(QFont("Arial", 12))
        input_container.addWidget(client_id_label)

        self.client_id_input = QLineEdit(self)
        self.client_id_input.setPlaceholderText("Enter your Client ID")
        self.client_id_input.setText(self.config_manager.get_client_id() or "")
        self.client_id_input.setFont(QFont("Arial", 11))
        self.client_id_input.setStyleSheet(
            "padding: 6px; border-radius: 4px; border: 1px solid #ccc;"
        )
        input_container.addWidget(self.client_id_input)

        # Label et champ de saisie pour le Tenant ID
        tenant_id_label = QLabel("Tenant ID:", self)
        tenant_id_label.setFont(QFont("Arial", 12))
        input_container.addWidget(tenant_id_label)

        self.tenant_id_input = QLineEdit(self)
        self.tenant_id_input.setPlaceholderText("Enter your Tenant ID")
        self.tenant_id_input.setText(self.config_manager.get_tenant_id() or "")
        self.tenant_id_input.setFont(QFont("Arial", 11))
        self.tenant_id_input.setStyleSheet(
            "padding: 6px; border-radius: 4px; border: 1px solid #ccc;"
        )
        input_container.addWidget(self.tenant_id_input)

        # Add input container to main layout
        layout.addLayout(input_container)

        # Spacer between input container and button
        spacer = QFrame(self)
        spacer.setFrameShape(QFrame.HLine)
        spacer.setFrameShadow(QFrame.Sunken)
        layout.addWidget(spacer)

        # Bouton d'authentification avec style
        self.auth_button = QPushButton("Authenticate", self)
        self.auth_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.auth_button.setStyleSheet(
            """
            QPushButton {
                background-color: #007BFF;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """
        )
        self.auth_button.clicked.connect(self.authenticate)
        layout.addWidget(self.auth_button)

        self.setLayout(layout)
        self.setWindowTitle("Authentication")
        self.setFixedSize(400, 300)

    def authenticate(self):
        client_id = self.client_id_input.text()
        tenant_id = self.tenant_id_input.text()

        # Sauvegarder séparément le client_id et tenant_id
        self.config_manager.set_client_id(client_id)
        self.config_manager.set_tenant_id(tenant_id)

        try:
            auth_manager = AuthManager(client_id, tenant_id)
            access_token = auth_manager.get_access_token(["User.Read", "Mail.Read"])
            QMessageBox.information(self, "Success", "Authentication successful")
            self.on_authenticated_callback(access_token)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Authentication failed: {e}")
