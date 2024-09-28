from PyQt5.QtWidgets import (
    QVBoxLayout,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QProgressBar,
)
from PyQt5.QtGui import QTextCursor

from sigminer.core.extraction_worker import ExtractionWorker, LauncherConfig


class ExtractionView(QDialog):
    def __init__(self, parent, access_token: str, launcher_config: LauncherConfig):
        super().__init__(parent)
        self.init_ui()

        # Launch the service in a separate thread
        self.worker = ExtractionWorker(access_token, launcher_config)
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.start()

    def init_ui(self):
        self.setWindowTitle("Service Launched")

        # Increase the window size
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Display logs of the ongoing process
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("font-size: 14pt;")
        layout.addWidget(self.log_output)

        # Add a progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Button to close the modal
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.cancel_process)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.update_close_button_message(0)  # Initialize the close button message

    def append_log(self, log):
        """Add logs to the text area."""
        self.log_output.append(log)
        self.log_output.moveCursor(QTextCursor.End)  # Auto-scroll to the bottom

    def update_progress(self, progress):
        """Update the progress bar."""
        self.progress_bar.setValue(progress)
        self.update_close_button_message(progress)

    def update_close_button_message(self, progress):
        """Update the close button message based on progress."""
        close_button = self.button_box.button(QDialogButtonBox.Close)
        if progress < 100:
            close_button.setText("Cancel process")
            close_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                """
            )
        else:
            close_button.setText("Finish process")
            close_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
                """
            )

    def cancel_process(self):
        # Stop the process if possible and close the modal
        self.worker.terminate()  # Forcefully stop the thread (can be improved)
        self.accept()  # Close the modal
