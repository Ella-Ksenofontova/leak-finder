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
    QToolTip
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont, QCursor

import matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

import ctypes
from random import uniform
from math import ceil
from threading import Thread

matplotlib.use("Qt5Agg")

lib = ctypes.CDLL("./Kfunc.dll")
lib.K.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double]
lib.K.restype = ctypes.POINTER(ctypes.c_double)

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

        self.readings_1 = None
        self.readings_2 = None
        
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

        self.setWindowTitle("Просмотр данных с датчиков")
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
        self.central_widget_layout.addWidget(label, 0, 0)

        self.add_labels()
        self.add_spinboxes_and_combobox()

        calculation_button = QPushButton("Расчёт")
        calculation_button.setDisabled(True)
        calculation_button.setToolTip("Введите ненулевые значения расстояния и скорости звука")
        calculation_button.setObjectName("calculationButton")
        calculation_button.setStyleSheet("""QPushButton {color: dimgray; background-color: lightgray}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
        calculation_button.setMaximumSize(100, 100)
        self.central_widget_layout.addWidget(calculation_button, 4, 0, 1, 2)
        calculation_button.clicked.connect(self.prepare_for_slow_calculations)

        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]

        for i in range(len(labels_texts)):
            label = QLabel(labels_texts[i])
            label.setObjectName(f"distanceLabel{i + 1}")
            label.setStyleSheet("font-size: 14px")
            self.central_widget_layout.addWidget(label, i + 5, 0, 1, 2)

    def prepare_for_slow_calculations(self):
        distance = self.central_widget.findChild(QDoubleSpinBox, "distanceSpinBox").value()
        sound_speed = self.central_widget.findChild(QDoubleSpinBox, "soundSpeedSpinBox").value()

        calculation_button = self.central_widget.findChild(QPushButton, "calculationButton")
        calculation_button.setText("Загрузка...")
        calculation_button.setCursor(Qt.CursorShape.WaitCursor)
        calculation_button.setDisabled(True)

        thread = Thread(target=self.perform_slow_calculation, args=(distance, sound_speed))
        thread.start()

    def make_array(self, shift, array_length, values):
        array_b = []
        index = shift
        while len(array_b)  < array_length:
            if index > len(values) - 1:
                index = 0
            
            array_b.append(values[index])

            index += 1

        return array_b

    def perform_slow_calculation(self, distance, sound_speed):
        array_length = ceil(distance / sound_speed * 10000)
        values = [uniform(1.0, 5.0) for i in range(array_length)]
        array_b =  self.make_array(0, ceil(array_length * 3.5), values)
        array_c =  self.make_array(15, ceil(array_length * 3.5), array_b)

        array_b = (ctypes.c_double * ceil(array_length * 3.5))(*array_b)
        array_c = (ctypes.c_double * ceil(array_length * 3.5))(*array_c)

        result_ptr = lib.K(array_b, array_c, sound_speed, distance)
        result_double_array = ctypes.cast(result_ptr, ctypes.POINTER(ctypes.c_double * ceil(array_length))).contents
        result_array = list(result_double_array)
        result_distances = self.calculate_distances(result_array, distance, sound_speed)

        self.change_canvas(result_array)
        self.make_button_available()
        self.change_distances_labels(result_distances)

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

    def change_distances_labels(self, result_distances):
        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]
        
        for i in range(len(result_distances)):
            label = self.central_widget.findChild(QLabel, f"distanceLabel{i + 1}")
            label.setText(labels_texts[i] + str(round(result_distances[i], 2)))

    def calculate_distances(self, result_array, distance, sound_speed):
        t = (len(result_array) - result_array.index(max(result_array))) / 10000
        distance_from_first_sensor = (distance + t * sound_speed) / 2
        distance_from_second_sensor = (distance - t * sound_speed) / 2
        distance_from_center = max(distance_from_first_sensor, distance_from_second_sensor) - distance / 2

        return [distance_from_center, distance_from_first_sensor, distance_from_second_sensor]

    def add_labels(self):
        labels_texts = ["Скорость звука, м/с:", "Расстояние между датчиками, м:", "Материал трубы:"]

        for i in range(len(labels_texts)):
            label = QLabel(labels_texts[i])
            label.setStyleSheet("font-size: 14px; width: 200px")
            self.central_widget_layout.addWidget(label, i + 1, 0)

    def add_spinboxes_and_combobox(self):
        identifiers = ["soundSpeedSpinBox", "distanceSpinBox"]

        for i in range(2):
            spinbox = QDoubleSpinBox()
            spinbox.setObjectName(identifiers[i])
            spinbox.setStyleSheet("margin-right: 20px; min-width: 150px; max-width: 200px;"
                                  "background-color: white; font-size: 14px")
            spinbox.setMinimum(0)
            spinbox.setMaximum(1000000)
            spinbox.valueChanged.connect(self.change_button_appereance)
            self.central_widget_layout.addWidget(spinbox, i + 1, 1)

        material_combobox = QComboBox()
        material_combobox.addItems(["Выберите материал...", "Сталь", "Медь", "Полиэтилен", "Полипропилен",
                                    "Поливинилхлорид"])
        material_combobox.setStyleSheet("max-width: 165px; background-color: white; border: 1px solid gainsboro")
        material_combobox.currentTextChanged.connect(self.change_sound_speed)
        self.central_widget_layout.addWidget(material_combobox, 3, 1)

    def check_spinboxes_values(self):
        spinbox_with_sound_speed = self.central_widget.findChild(QDoubleSpinBox, "soundSpeedSpinBox")
        spinbox_with_distance = self.central_widget.findChild(QDoubleSpinBox, "distanceSpinBox")

        return spinbox_with_sound_speed.value() > 0 and spinbox_with_distance.value() > 0
    
    def change_button_appereance(self):
        result = self.check_spinboxes_values()
        calculation_button = self.findChild(QPushButton, "calculationButton")
        if result:
            calculation_button.setDisabled(False)
            calculation_button.setToolTip("")
            calculation_button.setStyleSheet("""QPushButton {color: white; background-color: navy; border: 0; font-weight: bold}""")
        else:
            calculation_button.setDisabled(True)
            calculation_button.setToolTip("Введите ненулевые значения расстояния и скорости звука")
            calculation_button.setStyleSheet("""QPushButton {color: dimgray; background-color: lightgray}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")


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
