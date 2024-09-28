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
        # Initialize views
        self.auth_view = AuthView(self.on_authenticated)
        self.stack.addWidget(self.auth_view)

        # Pass a callback to return to the email view
        self.settings_view = SettingsView(self.show_email_view)
        self.stack.addWidget(self.settings_view)

        # Menu bar
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # "Options" menu
        options_menu = self.menu_bar.addMenu("Options")

        # Add "Settings" option
        self.settings_action = QAction("Settings", self)
        self.settings_action.triggered.connect(self.show_settings)
        self.settings_action.setEnabled(False)  # Disabled by default
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
        # Enable the settings button after authentication
        self.settings_action.setEnabled(True)

        # Add and switch to the email view
        self.email_view = EmailView(access_token)
        self.stack.addWidget(self.email_view)
        self.stack.setCurrentWidget(self.email_view)

    def show_settings(self):
        # Display the settings page
        self.stack.setCurrentWidget(self.settings_view)

    def show_email_view(self):
        # Return to the email page
        self.stack.setCurrentWidget(self.email_view)
