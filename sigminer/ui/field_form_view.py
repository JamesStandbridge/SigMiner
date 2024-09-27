from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QHBoxLayout,
)


class FieldFormView(QWidget):
    def __init__(
        self,
        remove_callback,
        field_name="",
        guideline="",
        field_type="TEXT",
    ):
        # print(remove_callback)
        # print(field_name)
        # print(guideline)
        # print(field_type)
        super().__init__()
        self.remove_callback = remove_callback
        self.init_ui(field_name, guideline, field_type)

    def init_ui(self, field_name, guideline, field_type):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Champ pour le nom du champ
        self.field_name_input = QLineEdit(self)
        self.field_name_input.setPlaceholderText("Field Name")
        self.field_name_input.setText(field_name)
        field_name_layout = QVBoxLayout()
        field_name_layout.setSpacing(5)  # Reduce space between label and input
        field_name_layout.addWidget(QLabel("Field Name:"))
        field_name_layout.addWidget(self.field_name_input)
        layout.addLayout(field_name_layout)

        # Champ pour la guideline
        self.guideline_input = QLineEdit(self)
        self.guideline_input.setPlaceholderText("Guideline")
        self.guideline_input.setText(guideline)
        guideline_layout = QVBoxLayout()
        guideline_layout.setSpacing(5)  # Reduce space between label and input
        guideline_layout.addWidget(QLabel("Guideline:"))
        guideline_layout.addWidget(self.guideline_input)
        layout.addLayout(guideline_layout)

        # Sélecteur pour le type de champ
        self.type_selector = QComboBox(self)
        self.type_selector.addItems(["TEXT", "INT", "BOOLEAN", "select"])
        self.type_selector.setCurrentText(field_type)
        type_layout = QVBoxLayout()
        type_layout.setSpacing(5)  # Reduce space between label and input
        type_layout.addWidget(QLabel("Type:"))
        type_layout.addWidget(self.type_selector)
        layout.addLayout(type_layout)

        # Bouton de suppression
        remove_button = QPushButton("Remove Field", self)
        remove_button.clicked.connect(self.remove_field)
        layout.addWidget(remove_button)

        self.setLayout(layout)

    def remove_field(self):
        self.remove_callback(self)  # Appeler le callback pour supprimer ce champ

    def get_field_data(self):
        return {
            "field_name": self.field_name_input.text(),
            "guideline": self.guideline_input.text(),
            "type": self.type_selector.currentText(),
        }
