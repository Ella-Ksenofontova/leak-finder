from PyQt6.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMainWindow
from PyQt6.QtGui import QIcon, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression, QObject, pyqtSignal

import re

class ValueChanged(QObject):
    valueChanged = pyqtSignal(float)
    
class CustomSpinBox(QWidget):
    def __init__(self, height=24, supports_double=True):
        super().__init__()
        
        self.setObjectName("customSpinbox")

        self.valueChangedSignal = ValueChanged()
        self.valueChanged = self.valueChangedSignal.valueChanged

        self.supports_double = supports_double

        self.suffix = ""
        self.min_value = 0
        self.max_value = 100000
        self.last_correct_value = self.min_value
        if self.supports_double:
            self.regexp = "(\d*,?\d*)" + self.suffix
        else:
            self.regexp = "(\d*)" + self.suffix
        self.height = height

        self.main_layout = QHBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.sub_layout = QVBoxLayout()
        self.sub_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.sub_layout.setSpacing(0)
        self.sub_layout.setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("min-width: 150px; background-color: white; font-size: 14px;")
        self.add_line_edit()
        self.add_buttons()
        self.add_controls()

        self.setLayout(self.main_layout)
        
        controls = self.findChild(QWidget, "controls")
        controls.setFixedHeight(self.height)
        
        for child in controls.children():
            if isinstance(child, QPushButton):
                child.setFixedHeight(self.height // 2)

    def add_line_edit(self):
        input_field = QLineEdit(str(self.last_correct_value) + self.suffix)
        input_field.setObjectName("inputField")
        input_field.setStyleSheet("QLineEdit{border-radius: 0; border: 1px solid gray; border-right: 0; outline: 2px solid black;} QLineEdit:focus, QlineEdit:hover {border-width: 2px; border-right: 2px solid gray}")
        input_field.setValidator(QRegularExpressionValidator(QRegularExpression(self.regexp)))
        input_field.setFixedHeight(self.height)
        self.main_layout.addWidget(input_field)

        input_field.textChanged.connect(self.text_changed)

    def add_buttons(self):
        increase_button = QPushButton()
        increase_button.setObjectName("increase_button")
        increase_button.setIcon(QIcon("./arrow-up.png"))
        increase_button.setStyleSheet("width: 100%")
        increase_button.clicked.connect(lambda: self.setValue(self.value() + 1))
        self.sub_layout.addWidget(increase_button)

        decrease_button = QPushButton()
        decrease_button.setObjectName("decrease_button")
        decrease_button.setIcon(QIcon("./arrow-down.png"))
        decrease_button.setStyleSheet("width: 100%")
        decrease_button.clicked.connect(lambda: self.setValue(self.value() - 1))
        self.sub_layout.addWidget(decrease_button)

        increase_button.setContentsMargins(0, 0, 0, 0)
        decrease_button.setContentsMargins(0, 0, 0, 0)

    def add_controls(self):
        controls = QWidget()
        controls.setStyleSheet("QWidget {background-color: white; padding: 0; border: 1px solid gray;} QLineEdit + QWidget {border-left:0; max-width: 25px;}")
        controls.setFixedWidth(25)
        controls.setObjectName("controls")
        controls.setLayout(self.sub_layout)
        controls.setMaximumWidth(25)
        controls.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(controls, 1)

    def setSuffix(self, suffix):
        if isinstance(suffix, str):
            self.suffix = suffix
            if self.supports_double:
                self.regexp = "(\d*,?\d*)" + suffix
            else:
                self.regexp = "(\d*)" + suffix
            input_field = self.findChild(QLineEdit, "inputField")
            input_field.setValidator(QRegularExpressionValidator(QRegularExpression(self.regexp)))
            input_field.setText(input_field.text() + suffix)
        else:
            wrong_type = str(type(suffix))
            wrong_type = wrong_type[wrong_type.find("'") + 1:wrong_type.rfind("'")]
            raise ValueError(f"Argument 'suffix' must be string, not {wrong_type}")

    def value(self):
        line_edit = self.findChild(QLineEdit, "inputField")
        value = line_edit.text()
        if len(self.suffix) > 0:
            value = value[:value.rfind(self.suffix[0])]
        if len(value) > 0 and any([i.isdigit() for i in list(value)]):
            if value.find(",") == -1:
                return int(value)
            elif value[value.find(",") + 1:] == "" or int(value[value.find(",") + 1:]) == 0:
                return int(value[:value.find(",")])
            else:
                return float(value.replace(",", "."))
        return 0

    def text_changed(self):
        input_field = self.findChild(QLineEdit, "inputField")

        value_is_proper = True
        if self.max_value != None:
            if self.max_value < self.value():
                value_is_proper = False
            
        if self.min_value != None:
            if self.min_value > self.value():
                value_is_proper = False

        if value_is_proper:
            self.last_correct_value = self.value()
            self.valueChanged.emit(self.last_correct_value)
        else:
            self.setValue(str(self.last_correct_value).replace(".", ","))

        if not input_field.text().endswith(self.suffix):
            self.setValue(str(self.last_correct_value).replace(".", ","))

    def setMinimum(self, number):
        input_field = self.findChild(QLineEdit, "inputField")
        self.min_value = number
        if self.max_value != None:
            if self.min_value > self.max_value:
                self.max_value = None
        
        if self.value() < number:
            input_field.setText(str(number) + self.suffix)
            self.last_correct_value = number

    def setMaximum(self, number):
        input_field = self.findChild(QLineEdit, "inputField")
        self.max_value = number
        if self.min_value != None:
            if self.min_value > self.max_value:
                self.min_value = None
        
        if self.value() > number:
            input_field.setText(str(number) + self.suffix)
            self.last_correct_value = number

    def setStyleSheet(self, stylesheet):
        unwanted_properties = ["min-width", "max-width", "margin-right"]
        for property in unwanted_properties:
            regexp = re.compile(f"^{property}: ?.+?; ?| ?{property}: ?.+?; ?| ?{property}: ?.+?\Z")
            result = regexp.findall(stylesheet)
            for rule in result:
                stylesheet = stylesheet.replace(rule, "")   

        super().setStyleSheet(stylesheet)

    def setValue(self, new_value):
        input_field = self.findChild(QLineEdit, "inputField")
        if input_field:
            input_field.setText(str(new_value).replace(".", ",") + self.suffix)
