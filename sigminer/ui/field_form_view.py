from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QFrame,
    QCheckBox,
)
from PyQt5.QtGui import QFont


class FieldFormView(QWidget):
    def __init__(
        self,
        remove_callback,
        field_name="",
        guideline="",
        can_be_overwritten=False,
    ):
        super().__init__()
        self.remove_callback = remove_callback
        self.init_ui(field_name, guideline, can_be_overwritten)

    def init_ui(self, field_name, guideline, can_be_overwritten):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Cadre autour du field form view
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Box)
        frame.setLineWidth(1)  # Make the border of the frame lighter
        frame.setObjectName("fieldFrame")
        frame.setStyleSheet("#fieldFrame { border: 1px solid #d4d4d4; }")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(10)
        frame.setFixedHeight(180)  # Adjusted height to accommodate the new checkbox

        # Bouton de suppression avec une petite croix en haut à droite du cadre
        remove_button = QPushButton("x", self)
        remove_button.setFont(QFont("Arial", 12, QFont.Bold))

        remove_button.setStyleSheet(
            """
            QPushButton {
                padding: 1px 5px 3px 5px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FF0000;
                color: white;
            }
        """
        )
        remove_button.clicked.connect(self.remove_field)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(remove_button)
        frame_layout.addLayout(button_layout)

        # Champ pour le nom du champ
        self.field_name_input = QLineEdit(self)
        self.field_name_input.setPlaceholderText("Field Name")
        self.field_name_input.setText(field_name)
        field_name_layout = QVBoxLayout()
        field_name_layout.setSpacing(5)  # Reduce space between label and input
        field_name_layout.addWidget(QLabel("Field Name:"))
        field_name_layout.addWidget(self.field_name_input)
        frame_layout.addLayout(field_name_layout)

        # Champ pour la guideline
        self.guideline_input = QLineEdit(self)
        self.guideline_input.setPlaceholderText("Guideline")
        self.guideline_input.setText(guideline)
        guideline_layout = QVBoxLayout()
        guideline_layout.setSpacing(5)  # Reduce space between label and input
        guideline_layout.addWidget(QLabel("Guideline:"))
        guideline_layout.addWidget(self.guideline_input)
        frame_layout.addLayout(guideline_layout)

        # Checkbox for can be overwritten
        self.can_be_overwritten_checkbox = QCheckBox("Can be overwritten", self)
        self.can_be_overwritten_checkbox.setChecked(can_be_overwritten)
        frame_layout.addWidget(self.can_be_overwritten_checkbox)

        layout.addWidget(frame)
        self.setLayout(layout)

    def remove_field(self):
        self.remove_callback(self)  # Appeler le callback pour supprimer ce champ

    def get_field_data(self):
        return {
            "field_name": self.field_name_input.text(),
            "guideline": self.guideline_input.text(),
            "can_be_overwritten": self.can_be_overwritten_checkbox.isChecked(),
        }
