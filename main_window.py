from PyQt6.QtWidgets import QApplication, \
    QMainWindow, \
    QPushButton, \
    QDoubleSpinBox, \
    QLabel, \
    QWidget, \
    QGridLayout, \
    QComboBox, \
    QHBoxLayout,\
    QVBoxLayout, \
    QToolTip,\
    QFileDialog, \
    QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont

import matplotlib 
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

import ctypes
from random import uniform
from math import ceil
from threading import Thread
from pathlib import Path

matplotlib.use("Qt5Agg")

lib = ctypes.CDLL("./Kfunc.dll")
lib.K.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double]
lib.K.restype = ctypes.POINTER(ctypes.c_double)

class CalculationFinishedSignal(QObject):
    calculation_finished = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.sound_speeds = {
            "Сталь": 5740,
            "Медь": 4720,
            "Полиэтилен": 2000,
            "Полипропилен": 1430,
            "Поливинилхлорид": 2395
        }

        self.file_names = None
        self.calculation_success = None
        self.signal = CalculationFinishedSignal()
        self.signal.calculation_finished.connect(self.handle_end_of_calculation)
        
        self.central_widget_layout = QGridLayout()
        self.central_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fill_left_column()
        self.right_column_layout = QVBoxLayout()
        self.right_column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.canvas = Canvas()
        self.fill_right_column()

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_widget_layout)
        self.central_widget.setMaximumHeight(500)

        self.screen_layout = QHBoxLayout()
        self.screen_layout.setSpacing(0)
        self.screen_layout.setContentsMargins(0, 0, 0, 0)
        self.add_widgets_to_screen_layout()

        QToolTip.setFont(QFont("sans-serif", 10, 0))

        self.screen = QWidget()
        self.screen.setLayout(self.screen_layout)
        
        self.setCentralWidget(self.screen)

        self.setWindowTitle("Просмотр результатов вычислений корреляционной функции")
        self.setStyleSheet("background-color: whitesmoke")
        self.setWindowIcon(QIcon("settings.png"))

    def add_widgets_to_screen_layout(self):
        side_widget_1 = QWidget()
        side_widget_1.setStyleSheet("background-color: white")
        self.screen_layout.addWidget(side_widget_1)
        self.screen_layout.addWidget(self.central_widget, alignment=Qt.AlignmentFlag.AlignTop)

        right_column = QWidget()
        right_column.setLayout(self.right_column_layout)
        self.screen_layout.addWidget(right_column)

        side_widget_2 = QWidget()
        side_widget_2.setStyleSheet("background-color: white")
        self.screen_layout.addWidget(side_widget_2)

    def fill_left_column(self):
        label = QLabel("<h2>Ввод параметров</h2>")
        label.setStyleSheet("font-weight: 600; color: #033E6B")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.central_widget_layout.addWidget(label, 0, 0, 1, 2)

        self.add_labels()
        self.add_inputs()

        calculation_button = QPushButton("Расчёт")
        calculation_button.setDisabled(True)
        calculation_button.setToolTip("Введите ненулевые значения расстояния и скорости звука")
        calculation_button.setObjectName("calculationButton")
        calculation_button.setStyleSheet("""QPushButton {color: dimgray; background-color: lightgray}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
        calculation_button.setMaximumSize(100, 100)
        self.central_widget_layout.addWidget(calculation_button, 5, 0, 1, 2)
        calculation_button.clicked.connect(self.prepare_for_slow_calculations)

        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]

        for i in range(len(labels_texts)):
            label = QLabel(labels_texts[i])
            label.setObjectName(f"distanceLabel{i + 1}")
            label.setStyleSheet("font-size: 14px")
            self.central_widget_layout.addWidget(label, i + 6, 0, 1, 2)

    def prepare_for_slow_calculations(self):
        distance = self.central_widget.findChild(QDoubleSpinBox, "distanceSpinBox").value()
        sound_speed = self.central_widget.findChild(QDoubleSpinBox, "soundSpeedSpinBox").value()

        calculation_button = self.central_widget.findChild(QPushButton, "calculationButton")
        calculation_button.setText("Загрузка...")
        calculation_button.setCursor(Qt.CursorShape.WaitCursor)
        calculation_button.setDisabled(True)

        thread = Thread(target=self.perform_slow_calculation, args=(distance, sound_speed))
        thread.start()

    def perform_slow_calculation(self, distance, sound_speed):
        array_1 = []
        array_2 = []

        self.calculation_success = None

        with open(self.file_names[0]) as values_1:
            for n in values_1:
                try:
                    n = float(n)
                    array_1.append(n)
                except ValueError:
                    self.calculation_success = 0
                    break

        with open(self.file_names[1]) as values_2:
            for n in values_2:
                try:
                    n = float(n)
                    array_2.append(n)
                except ValueError:
                    self.calculation_success = 0
                    break

        if self.calculation_success != 0:
            self.calculation_success = 1

            min_length = min(len(array_1), len(array_2))

            array_1 = (ctypes.c_double * min_length)(*array_1[0:min_length])
            array_2 = (ctypes.c_double * min_length)(*array_2[0:min_length])

            result_ptr = lib.K(array_1, array_2, sound_speed, distance)
            result_double_array = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_double * min_length)).contents
            result_array = list(result_double_array)
            result_distances = self.calculate_distances(result_array, distance, sound_speed)
            self.change_canvas(result_array)
            self.change_distances_labels(result_distances)

        self.make_button_available()

    def handle_end_of_calculation(self):
        if not self.calculation_success:
            self.show_error()
            self.clear_all_inputs()
            self.canvas.axes.clear()
            self.right_column_layout.removeWidget(self.canvas)
            self.right_column_layout.addWidget(self.canvas)
            self.canvas.setToolTip("Здесь будет график")

    def show_error(self):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.setText("Произошла ошибка при чтении файла.")
        error_dialog.setInformativeText("В файле должны быть только дробные числа, после которых стоит знак переноса. Целая часть от дробной должна отделяться точкой.")

        error_dialog.exec()

    def clear_all_inputs(self):
        identifiers = ["soundSpeedSpinBox", "distanceSpinBox"]
        for id in identifiers:
            input = self.central_widget.findChild(QDoubleSpinBox, id)
            input.setValue(0)

        material_combobox = self.central_widget.findChild(QComboBox, "materialCombobox")
        material_combobox.setCurrentIndex(0)

        self.central_widget.findChild(QPushButton, "fileChoiceButton").setText("Выберите 2 файла")
        self.file_names = []
        self.central_widget.findChild(QLabel, "fileNames").setText("Файлы не выбраны")

        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]
        
        for i in range(len(labels_texts)):
            label = self.central_widget.findChild(QLabel, f"distanceLabel{i + 1}")
            label.setText(labels_texts[i])

    def change_canvas(self, result_array):
        self.canvas.axes.clear()
        self.canvas.axes.plot(list(range(len(result_array))), result_array)
        self.right_column_layout.removeWidget(self.canvas)
        self.right_column_layout.addWidget(self.canvas)
        self.canvas.setToolTip("")

    def make_button_available(self):
        calculation_button = self.central_widget.findChild(QPushButton, "calculationButton")
        calculation_button.setDisabled(False)
        calculation_button.setText("Расчёт") 
        calculation_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.signal.calculation_finished.emit()

    def change_distances_labels(self, result_distances):
        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]
        
        for i in range(len(result_distances)):
            label = self.central_widget.findChild(QLabel, f"distanceLabel{i + 1}")
            label.setText(labels_texts[i] + str(round(result_distances[i], 2)) + " м")

    def calculate_distances(self, result_array, distance, sound_speed):
        t = (len(result_array) - result_array.index(max(result_array))) / 9600
        distance_from_first_sensor = (distance + t * sound_speed) / 2
        distance_from_second_sensor = (distance - t * sound_speed) / 2
        distance_from_center = max(distance_from_first_sensor, distance_from_second_sensor) - distance / 2

        return [distance_from_center, distance_from_first_sensor, distance_from_second_sensor]

    def add_labels(self):
        labels_texts = ["Скорость звука, м/с:", "Расстояние между датчиками, м:", "Материал трубы:"]

        for i in range(len(labels_texts)):
            label = QLabel(labels_texts[i])
            label.setStyleSheet("font-size: 14px; width: 200px")
            self.central_widget_layout.addWidget(label, i + 2, 0, 1, 2)

    def add_inputs(self):
        identifiers = ["soundSpeedSpinBox", "distanceSpinBox"]

        self.add_choice_button()
        self.add_file_names_label()

        for i in range(2):
            spinbox = QDoubleSpinBox()
            spinbox.setObjectName(identifiers[i])
            spinbox.setStyleSheet("margin-right: 20px; min-width: 150px; max-width: 200px;"
                                  "background-color: white; font-size: 14px")
            spinbox.setMinimum(0)
            spinbox.setMaximum(1000000)
            spinbox.valueChanged.connect(self.change_calc_button_appereance)
            self.central_widget_layout.addWidget(spinbox, i + 2, 2)

        material_combobox = QComboBox()
        material_combobox.setObjectName("materialCombobox")
        material_combobox.addItems(["Выберите материал...", "Сталь", "Медь", "Полиэтилен", "Полипропилен",
                                    "Поливинилхлорид"])
        material_combobox.setStyleSheet("max-width: 165px; background-color: white; border: 1px solid gainsboro")
        material_combobox.currentTextChanged.connect(self.change_sound_speed)
        self.central_widget_layout.addWidget(material_combobox, 4, 2)

    def add_choice_button(self):
        file_choice_button = QPushButton("Выберите 2 файла")
        file_choice_button.setObjectName("fileChoiceButton")
        file_choice_button.setStyleSheet("""QPushButton {max-width: 120px; padding: 5px; color: white; background-color: navy; border: 0; font-weight: bold}""")
        self.central_widget_layout.addWidget(file_choice_button, 1, 0)
        file_choice_button.clicked.connect(self.open_file_and_record_names)

    def add_file_names_label(self):
        file_names_label = QLabel("Файлы не выбраны")
        file_names_label.setObjectName("fileNames")
        self.central_widget_layout.addWidget(file_names_label, 1, 1, 1, 2)        

    def check_spinboxes_values(self):
        spinbox_with_sound_speed = self.central_widget.findChild(QDoubleSpinBox, "soundSpeedSpinBox")
        spinbox_with_distance = self.central_widget.findChild(QDoubleSpinBox, "distanceSpinBox")

        return spinbox_with_sound_speed.value() > 0 and spinbox_with_distance.value() > 0
    
    def change_calc_button_appereance(self):
        result = self.check_spinboxes_values()
        calculation_button = self.findChild(QPushButton, "calculationButton")
        if result and self.file_names:
            calculation_button.setDisabled(False)
            calculation_button.setToolTip("")
            calculation_button.setStyleSheet("""QPushButton {color: white; background-color: navy; border: 0; font-weight: bold}""")
        else:
            calculation_button.setDisabled(True)
            calculation_button.setStyleSheet("""QPushButton {color: dimgray; background-color: lightgray}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
            if not result:
                calculation_button.setToolTip("Введите ненулевые значения расстояния и скорости звука")
            elif not self.file_names:
                calculation_button.setToolTip("Выберите 2 файла")


    def open_file_and_record_names(self):
         file_names = QFileDialog.getOpenFileNames(self, "Выбор файлов", str(Path.home()), filter="Текстовые файлы (*.txt)")
         if len(file_names[0]) >= 2:
            self.file_names = file_names[0][0:2]
                    
            self.change_calc_button_appereance()
            
            file_choice_button = self.findChild(QPushButton, "fileChoiceButton")
            file_choice_button.setText("Изменить")

            self.show_file_names()

    def show_file_names(self):
        file_names_labels = self.central_widget.findChild(QLabel, "fileNames")
        file_names = []
        for name in self.file_names:
            name = name[name.rindex("/") + 1:]
            if len(name) > 19:
                file_names.append(name[0:11] + "..." + name[-1:-6:-1][-1::-1])
            else:
                file_names.append(name)
        file_names_labels.setText(file_names[0] + "; " + file_names[1])

    def change_sound_speed(self, material):
        spinbox_with_sound_speed = self.central_widget.findChild(QDoubleSpinBox, "soundSpeedSpinBox")
        if material in self.sound_speeds:
            spinbox_with_sound_speed.setValue(self.sound_speeds[material])
        else:
            spinbox_with_sound_speed.setValue(0)

    def fill_right_column(self):
        label = QLabel(f"<h2>Корреляционная функция</h2>")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setStyleSheet("font-weight: 600; color: #033E6B")
        self.right_column_layout.addWidget(label)
        self.canvas.setToolTip("Здесь будет график")
        self.right_column_layout.addWidget(self.canvas)


class Canvas(FigureCanvas):
    def __init__(self) -> None:
        figure = Figure(figsize=(500, 500), facecolor="white")
        self.axes = figure.add_subplot()
        super().__init__(figure)

app = QApplication([])

window = MainWindow()
window.show()

app.exec()
