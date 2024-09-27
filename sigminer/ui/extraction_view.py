from PyQt5.QtWidgets import QVBoxLayout, QDialog, QTextEdit, QDialogButtonBox
from PyQt5.QtGui import QTextCursor


from sigminer.core.extraction_worker import ExtractionWorker, LauncherConfig


class ExtractionView(QDialog):
    def __init__(self, parent, access_token: str, launcher_config: LauncherConfig):
        super().__init__(parent)
        self.init_ui()

        # Lancer le service dans un thread séparé
        self.worker = ExtractionWorker(access_token, launcher_config)
        self.worker.log_signal.connect(self.append_log)
        self.worker.start()

    def init_ui(self):
        self.setWindowTitle("Service Launched")

        # Augmenter la taille de la fenêtre
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Affichage des logs du processus en cours
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)

        # Augmenter la taille de la police du texte
        self.log_output.setStyleSheet("font-size: 14pt;")
        layout.addWidget(self.log_output)

        # Bouton pour fermer la modal
        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.rejected.connect(self.cancel_process)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def append_log(self, log):
        """Ajouter des logs à la zone de texte."""
        self.log_output.append(log)
        self.log_output.moveCursor(
            QTextCursor.End
        )  # Défilement automatique vers le bas

    def cancel_process(self):
        # Arrêter le processus si possible et fermer la modal
        self.worker.terminate()  # Stopper le thread de manière brute (peut être amélioré)
        self.accept()  # Fermer la modal
