from PyQt5.QtWidgets import QStackedWidget, QDesktopWidget
from sigminer.ui.auth_view import AuthView
from sigminer.ui.email_view import EmailView


class MainWindow(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.auth_view = AuthView(self.on_authenticated)
        self.addWidget(self.auth_view)

        self.setWindowTitle("Sigminer")

        # Centrer la fenêtre
        self.center()

    def center(self):
        # Obtenir les dimensions de l'écran
        screen_geometry = QDesktopWidget().availableGeometry()
        window_geometry = self.frameGeometry()

        # Calculer la position pour centrer la fenêtre
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)

        # Déplacer la fenêtre à la nouvelle position calculée
        self.move(window_geometry.topLeft())

    def on_authenticated(self, access_token):
        self.email_view = EmailView(access_token)
        self.addWidget(self.email_view)
        self.setCurrentWidget(self.email_view)
