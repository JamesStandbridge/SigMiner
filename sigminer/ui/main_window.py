from PyQt5.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QDesktopWidget,
    QAction,
    QMenuBar,
)
from sigminer.ui.auth_view import AuthView
from sigminer.ui.email_view import EmailView
from sigminer.ui.settings_view import SettingsView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        self.init_ui()

    def init_ui(self):
        # Initialisation des vues
        self.auth_view = AuthView(self.on_authenticated)
        self.stack.addWidget(self.auth_view)

        # Passer un callback pour revenir en arrière
        self.settings_view = SettingsView(self.show_email_view)
        self.stack.addWidget(self.settings_view)

        # Menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Menu "Options"
        options_menu = self.menu_bar.addMenu("Options")

        # Ajout de l'option "Settings"
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)
        self.settings_action.setEnabled(False)  # Désactivé par défaut
        options_menu.addAction(self.settings_action)

        self.setWindowTitle("Sigminer")
        self.center()

    def center(self):
        screen_geometry = QDesktopWidget().availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(center_point.x() - window_geometry.width() // 2, 0)

    def on_authenticated(self, access_token):
        # Activer le bouton des réglages après l'authentification
        self.settings_action.setEnabled(True)

        # Ajouter et basculer vers la vue email
        self.email_view = EmailView(access_token)
        self.stack.addWidget(self.email_view)
        self.stack.setCurrentWidget(self.email_view)

    def show_settings(self):
        # Afficher la page des réglages
        self.stack.setCurrentWidget(self.settings_view)

    def show_email_view(self):
        # Retourner à la page email
        self.stack.setCurrentWidget(self.email_view)
