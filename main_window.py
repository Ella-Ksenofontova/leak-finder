
from PyQt6.QtWidgets import QApplication, \
    QMainWindow, \
    QPushButton, \
    QLineEdit, \
    QLabel, \
    QWidget, \
    QGridLayout, \
    QComboBox, \
    QHBoxLayout,\
    QVBoxLayout, \
    QToolTip,\
    QFileDialog, \
    QMessageBox,\
    QTabWidget,\
    QLayout
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QFont

import matplotlib 
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

import ctypes
from threading import Thread
from multiprocessing.pool import ThreadPool
from pathlib import Path
import datetime
import time
import sched
from traceback import format_exc
from sys import stderr

from arduino_imitation import write_signals_in_file
from CustomSpinBox import CustomSpinBox

matplotlib.use("Qt5Agg")

lib = ctypes.CDLL("./Kfunc.dll")
lib.K.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double]
lib.K.restype = ctypes.POINTER(ctypes.c_double)

class CalculationFinishedSignal(QObject):
    calculation_finished = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.sound_speeds = {"Сталь": 5740, "Медь": 4720, "Полиэтилен": 2000, "Полипропилен": 1430, "Поливинилхлорид": 2395}
        
        self.analysing_params = {"file_names": None, "calculation_success": None, "reason_of_error": None}
        self.input_params = {"dir_path": None, "file_name": None, "distance": 0, "sound_speed": 0, "input_result": None}

        self.analyse_signal = CalculationFinishedSignal()
        self.analyse_signal.calculation_finished.connect(self.handle_end_of_calculation)

        self.input_signal = CalculationFinishedSignal()
        self.input_signal.calculation_finished.connect(self.handle_end_of_writing)
        
        self.central_widget_layout = QGridLayout()
        self.canvas = Canvas()
        self.adjust_central_widget_layout()

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_widget_layout)
        self.central_widget.setMaximumHeight(500)

        self.analysis_screen_layout = QHBoxLayout()
        self.adjust_analysis_widget_layout()

        self.input_screen_layout = QGridLayout()
        self.input_screen_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.add_widgets_to_input_screen_layout()

        QToolTip.setFont(QFont("sans-serif", 10, 0))

        self.tabs = QTabWidget()
        self.add_tabs()
        
        self.setCentralWidget(self.tabs)
        self.adjust_window_appereance()

    def adjust_central_widget_layout(self):
        self.central_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fill_left_column()
        self.right_column_layout = QVBoxLayout()
        self.right_column_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fill_right_column()

    def adjust_analysis_widget_layout(self):
        self.analysis_screen_layout.setSpacing(0)
        self.analysis_screen_layout.setContentsMargins(0, 0, 0, 0)
        self.add_widgets_to_screen_layout()

    def adjust_window_appereance(self):
        self.setWindowTitle("Работа с корреляционным течеискателем")
        self.setStyleSheet("background-color: whitesmoke")
        self.setWindowIcon(QIcon("C:\\Users\\User\\PycharmProjects\\leakFinder\\settings.ico"))

    def add_tabs(self):
        input_screen = QWidget()
        layout_with_side_widgets = QHBoxLayout()
        layout_with_side_widgets.setContentsMargins(0, 0, 0, 0)

        side_widget_1 = QWidget()
        side_widget_1.setStyleSheet("background-color: white")

        input_central_widget = QWidget()
        input_central_widget.setMaximumWidth(500)
        input_central_widget.setLayout(self.input_screen_layout)

        side_widget_2 = QWidget()
        side_widget_2.setStyleSheet("background-color: white")

        for widget in [side_widget_1, input_central_widget, side_widget_2]:
            layout_with_side_widgets.addWidget(widget)

        input_screen.setLayout(layout_with_side_widgets)
        self.tabs.addTab(input_screen, "Запись показаний")

        analysis_screen = QWidget()
        analysis_screen.setLayout(self.analysis_screen_layout)
        self.tabs.addTab(analysis_screen, "Анализ показаний")

    def add_widgets_to_screen_layout(self):
        self.analysis_screen_layout.addWidget(self.central_widget, alignment=Qt.AlignmentFlag.AlignTop)

        right_column = QWidget()
        right_column.setLayout(self.right_column_layout)
        self.analysis_screen_layout.addWidget(right_column)

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
        distance = self.central_widget.findChild(CustomSpinBox, "distanceSpinBox").value()
        sound_speed = self.central_widget.findChild(CustomSpinBox, "soundSpeedSpinBox").value()

        calculation_button = self.central_widget.findChild(QPushButton, "calculationButton")
        calculation_button.setText("Загрузка...")
        calculation_button.setCursor(Qt.CursorShape.WaitCursor)
        calculation_button.setDisabled(True)

        thread = Thread(target=self.perform_slow_calculation, args=(distance, sound_speed))
        thread.start()

    def perform_slow_calculation(self, distance, sound_speed):
        array_1 = []
        array_2 = []

        self.analysing_params["calculation_success"] = None
        self.analysing_params["reason_of_error"] = None

        with open(self.analysing_params["file_names"][0]) as values_1:
            for n in values_1:
                try:
                    n = float(n)
                    array_1.append(n)
                except ValueError:
                    self.analysing_params["calculation_success"] = 0
                    self.analysing_params["reason_of_error"] = "value"
                    break

        with open(self.analysing_params["file_names"][1]) as values_2:
            for n in values_2:
                try:
                    n = float(n)
                    array_2.append(n)
                except ValueError:
                    self.analysing_params["calculation_success"] = 0
                    self.analysing_params["reason_of_error"] = "value"
                    break
                finally:
                    if self.analysing_params["calculation_success"] == 0:
                        self.make_button_available()

        length_of_arrays = round(distance / sound_speed * 33600)

        if self.analysing_params["calculation_success"] != 0:
            if len(array_1) != length_of_arrays or len(array_2) != length_of_arrays:
                self.analysing_params["calculation_success"] = 0
                self.analysing_params["reason_of_error"] = "wrong_length"
                self.make_button_available()

        if self.analysing_params["calculation_success"] != 0:
            self.analysing_params["calculation_success"] = 1
            try:
                array_1 = (ctypes.c_double * length_of_arrays)(*array_1)
                array_2 = (ctypes.c_double * length_of_arrays)(*array_2)
                result_ptr = lib.K(array_1, array_2, sound_speed, distance)
                result_array = result_ptr[:round(len(array_1) / 3.5)]
                result_distances = self.calculate_distances(result_array, distance, sound_speed)

                self.change_canvas(result_array)
                self.change_distances_labels(result_distances)
            except:
                self.analysing_params["calculation_success"] = 0
                self.analysing_params["reason_of_error"] = "OS"
                print(format_exc(10), file=stderr)
            finally:
                self.make_button_available()

    def handle_end_of_calculation(self):
        if not self.analysing_params["calculation_success"]:
            if self.analysing_params["reason_of_error"] == "value":
                informative_text = "В файле должны быть только дробные числа, после которых стоит знак переноса. Целая часть от дробной должна отделяться точкой."
            else:
                informative_text = "Проверьте правильность данных, записанных в файл."

            self.show_error(main_text="Произошла ошибка при чтении файла.", informative_text=informative_text)
            self.clear_all_inputs()

            for key in self.analysing_params:
                self.analysing_params[key] = None

            self.canvas.axes.clear()
            self.right_column_layout.removeWidget(self.canvas)
            self.right_column_layout.addWidget(self.canvas)
            self.canvas.setToolTip("Здесь будет график")

    def show_error(self, main_text="", informative_text=""):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.setText(main_text)
        error_dialog.setInformativeText(informative_text)

        error_dialog.exec()

    def clear_all_inputs(self):
        identifiers = ["soundSpeedSpinBox", "distanceSpinBox"]
        for id in identifiers:
            input = self.central_widget.findChild(CustomSpinBox, id)
            input.setValue(0)

        material_combobox = self.central_widget.findChild(QComboBox, "materialCombobox")
        material_combobox.setCurrentIndex(0)

        self.central_widget.findChild(QPushButton, "fileChoiceButton").setText("Выберите 2 файла")
        self.analysing_params["file_names"] = []
        self.central_widget.findChild(QLabel, "fileName").setText("Файлы не выбраны")

        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]
        
        for i in range(len(labels_texts)):
            label = self.central_widget.findChild(QLabel, f"distanceLabel{i + 1}")
            label.setText(labels_texts[i])

    def change_canvas(self, result_array):
        self.canvas.axes.clear()
        try:
            self.canvas.axes.plot(list(range(len(result_array))), result_array)
            self.canvas.setToolTip("")
        except OverflowError:
            self.show_error(main_text="Произошла ошибка при построении графика.", informative_text="Проверьте правильность данных, введённых в файл.")
        finally:
            self.right_column_layout.removeWidget(self.canvas)
            self.right_column_layout.addWidget(self.canvas)
        
    def make_button_available(self):
        calculation_button = self.central_widget.findChild(QPushButton, "calculationButton")
        calculation_button.setDisabled(False)
        calculation_button.setText("Расчёт") 
        calculation_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.analyse_signal.calculation_finished.emit()

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
            label.setStyleSheet("font-size: 14px; width: 200px;")
            self.central_widget_layout.addWidget(label, i + 2, 0, 1, 2)

    def add_inputs(self):
        identifiers = ["soundSpeedSpinBox", "distanceSpinBox"]

        self.add_choice_button()
        self.add_file_names_label()

        for i in range(2):
            spinbox = CustomSpinBox()
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
        file_choice_button.clicked.connect(self.open_files_and_record_names)

    def add_file_names_label(self):
        file_names_label = QLabel("Файлы не выбраны")
        file_names_label.setObjectName("fileName")
        self.central_widget_layout.addWidget(file_names_label, 1, 1, 1, 2)        

    def check_spinboxes_values(self):
        spinbox_with_sound_speed = self.central_widget.findChild(CustomSpinBox, "soundSpeedSpinBox")
        spinbox_with_distance = self.central_widget.findChild(CustomSpinBox, "distanceSpinBox")

        return spinbox_with_sound_speed.value() > 0 and spinbox_with_distance.value() > 0
    
    def change_calc_button_appereance(self):
        result = self.check_spinboxes_values()
        calculation_button = self.findChild(QPushButton, "calculationButton")
        if result and self.analysing_params["file_names"]:
            calculation_button.setDisabled(False)
            calculation_button.setToolTip("")
            calculation_button.setStyleSheet("""QPushButton {color: white; background-color: navy; border: 0; font-weight: bold}""")
        else:
            calculation_button.setDisabled(True)
            calculation_button.setStyleSheet("""QPushButton {color: dimgray; background-color: lightgray}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
            if not result:
                calculation_button.setToolTip("Введите ненулевые значения расстояния и скорости звука")
            elif not self.analysing_params["file_names"]:
                calculation_button.setToolTip("Выберите 2 файла")


    def open_files_and_record_names(self):
         file_names = QFileDialog.getOpenFileNames(self, "Выбор файлов", "", filter="Текстовые файлы (*.txt)")
         if len(file_names[0]) > 1:
            self.analysing_params["file_names"] = file_names[0]

            self.change_calc_button_appereance()
            
            file_choice_button = self.findChild(QPushButton, "fileChoiceButton")
            file_choice_button.setText("Изменить")

            self.show_file_names()

    def show_file_names(self):
        file_name_label = self.central_widget.findChild(QLabel, "fileName")
        file_names = []
        for name in self.analysing_params["file_names"]:
            name = name[name.rindex("/") + 1:]
            if len(name) > 19:
                name = name[0:11] + "..." + name[-1:-6:-1][-1::-1]
            file_names.append(name)
        file_name_label.setText(file_names[0] + "; " + file_names[1])

    def change_sound_speed(self, material):
        spinbox_with_sound_speed = self.central_widget.findChild(CustomSpinBox, "soundSpeedSpinBox")
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

    def add_widgets_to_input_screen_layout(self):
        title = QLabel(f"<h2>Настройки записи с датчиков</h2>")
        title.setStyleSheet("font-weight: 600; color: #033E6B")
        self.input_screen_layout.addWidget(title, 0, 0, 1, 2)

        labels = ["Папка, куда будет записан файл: ", "Имя файла: ", "Время запуска: ", "Расстояние между датчиками: ", "Скорость звука в трубе: "]
        for i in range(len(labels)):
            label = QLabel(labels[i])
            self.input_screen_layout.addWidget(label, i + 1, 0)

        dir_choose_layout = QHBoxLayout()
        dir_choose_layout.setContentsMargins(0, 0, 0, 0)
        dir_choose_layout.setSpacing(0)

        dir_name_label = QLabel("Не выбрана")
        dir_name_label.setObjectName("dirName")
        dir_choose_layout.addWidget(dir_name_label)

        dir_choose_button = QPushButton("Выберите папку")
        dir_choose_button.setStyleSheet("QPushButton {max-width: 120px; padding: 5px; color: white; background-color: navy; border: 0; font-weight: bold}")
        dir_choose_button.setObjectName("dirChooseButton")
        dir_choose_button.clicked.connect(self.choose_and_record_directory)
        dir_choose_layout.addWidget(dir_choose_button)

        dir_choose = QWidget()
        dir_choose.setMaximumWidth(200)
        dir_choose.setLayout(dir_choose_layout)
        self.input_screen_layout.addWidget(dir_choose, 1, 1)

        self.add_file_name_input()

        self.add_spinboxes()

        record_start_button = QPushButton("Начать запись")
        record_start_button.setObjectName("recordStartButton")
        record_start_button.setStyleSheet("""QPushButton {color: dimgray; background-color: lightgray; max-width: 100px}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
        record_start_button.setToolTip("Заполните все поля")
        record_start_button.setDisabled(True)
        record_start_button.clicked.connect(self.show_confirmation_and_start_scheduling)
        self.input_screen_layout.addWidget(record_start_button, 6, 0, 1, 2)

    def write_value(self, param, value):
        self.input_params[param] = value
        self.change_state_of_start_button()

    def choose_and_record_directory(self):
        directory_path = QFileDialog.getExistingDirectory(self, "Выбор папки", str(Path.home()))
        if directory_path:
            self.input_params["dir_path"] = directory_path
            self.change_state_of_start_button()
            dir_choose_button = self.findChild(QPushButton, "dirChooseButton")
            if dir_choose_button.text != "Изменить":
                dir_choose_button.setText("Изменить")
            dir_choose_button.setStyleSheet("QPushButton {max-width: 80px; padding: 5px; color: white; background-color: navy; border: 0; font-weight: bold}")

            dir_name = directory_path[directory_path.rindex("/") + 1:]
            if len(dir_name) > 15:
                dir_name = dir_name[:13] + "..."
            elif len(dir_name) == 0:
                dir_name = directory_path[:directory_path.index("/")]

            dir_name_label = self.findChild(QLabel, "dirName")
            dir_name_label.setText(dir_name)    

    def add_file_name_input(self):
        file_name_layout = QHBoxLayout()
        file_name_layout.setContentsMargins(0, 0, 0, 0)

        file_name = QLineEdit()
        file_name.setObjectName("fileName")
        file_name.setStyleSheet("QLineEdit {background-color: white; max-width: 150px}")
        file_name.setMaximumWidth(150)
        file_name.textChanged.connect(lambda: self.write_value("file_name", file_name.text()))
        file_name_layout.addWidget(file_name)
        file_name_layout.addWidget(QLabel(".txt"))

        file_name_widget = QWidget()
        file_name_widget.setLayout(file_name_layout)
        self.input_screen_layout.addWidget(file_name_widget, 2, 1)

    def add_spinboxes(self):
        spinbox_names = ["startHour", "startMinute", "input_distance", "input_soundSpeed"]
        suffixes = [" ч", " мин", " м", " м/с"]
        properties = ["max-width: 100px", "max-width: 100px", "max-width: 150px", "max-width: 150px"]
        max_values = [23, 59, 1000000, 1000000]

        double_spin_boxes = []

        spinboxes_layout = QHBoxLayout()
        spinboxes_layout.setContentsMargins(0, 0, 0, 0)

        for i in range(len(spinbox_names)):
            if i < 2:
                supports_double = False
            else:
                supports_double = True
            spinbox = CustomSpinBox(supports_double=supports_double)

            spinbox.setStyleSheet(f"background-color: white; padding: 0;")
            prop = properties[i]
            if prop.startswith("max"):
                spinbox.setMaximumWidth(int(prop[prop.find(":") + 1:prop.find("px")].strip()))
            else:
                spinbox.setMinimumWidth(int(prop[prop.find(":") + 1:prop.find("px")].strip()))
                
            spinbox.setObjectName(spinbox_names[i])
            spinbox.setSuffix(suffixes[i])
            spinbox.setMaximum(max_values[i])   

            if i < 2:         
                spinboxes_layout.addWidget(spinbox)
            else:
                self.input_screen_layout.addWidget(spinbox, i + 2, 1)
                double_spin_boxes.append(spinbox)

        double_spin_boxes[0].valueChanged.connect(lambda value: self.write_value("distance", value))
        double_spin_boxes[1].valueChanged.connect(lambda value: self.write_value("sound_speed", value))

        spinboxes_wrapper = QWidget()
        spinboxes_wrapper.setLayout(spinboxes_layout)
        self.input_screen_layout.addWidget(spinboxes_wrapper, 3, 1, Qt.AlignmentFlag.AlignLeft)


    def find_date(self, hours, minutes):
        now = datetime.datetime.now()

        days_in_months = {
            1: 31,
            3: 31,
            4: 30,
            5: 31,
            6: 30,
            7: 31,
            8: 31,
            9: 30,
            10: 31,
            11: 30
        }

        if now.hour > hours or (now.hour == hours and now.minute > minutes):
            if now.month == 12 and now.day == 31:
                return datetime.datetime(now.year + 1, 1, 1, hours, minutes)
            elif now.month == 2:
                if (now.day == 29 and now.year % 4 == 0) or (now.day == 28 and now.year % 4 != 0):
                    return datetime.datetime(now.year, 3, 1, hours, minutes)
                else:
                    return datetime.datetime(now.year, now.month, now.day + 1, hours, minutes)
            else:
                if now.day == days_in_months[now.month]:
                   return datetime.datetime(now.year, now.month + 1, 1, hours, minutes)
                else:
                    return datetime.datetime(now.year, now.month, now.day + 1, hours, minutes)
                
        return datetime.datetime(now.year, now.month, now.day, hours, minutes)
    
    def change_state_of_start_button(self):
        values = [self.input_params[key] for key in self.input_params]
        record_start_button = self.findChild(QPushButton, "recordStartButton")
        if all(values[:4]):
            record_start_button.setStyleSheet("""QPushButton {color: white; background-color: navy; font-weight: bold; max-width: 100px}""")
            record_start_button.setToolTip("")
            record_start_button.setDisabled(False)
        else:
            record_start_button.setStyleSheet("""QPushButton {color: dimgray; font-weight: normal; background-color: lightgray; max-width: 100px}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
            record_start_button.setToolTip("Заполните все поля")
            record_start_button.setDisabled(True)

    def show_confirmation_and_start_scheduling(self):
        start_hour = self.findChild(CustomSpinBox, "startHour").value()
        start_minute = self.findChild(CustomSpinBox, "startMinute").value()

        date_of_start = self.find_date(start_hour, start_minute)
        date_string = date_of_start.strftime("%d.%m.%y, %H:%M")

        self.input_params["distance"] = self.findChild(CustomSpinBox, "input_distance").value()
        self.input_params["sound_speed"] = self.findChild(CustomSpinBox, "input_soundSpeed").value()

        confirm_pop_up = self.create_confirm_pop_up({"date_string": date_string})

        pool = ThreadPool(processes=1)
        input_params = self.input_params
        input_signal = self.input_signal

        def get_result_of_writing():
            async_result = pool.apply_async(write_signals_in_file, [input_params[key] for key in ["distance", "sound_speed"]] + [input_params["dir_path"] for i in range(2)] + [input_params["file_name"] + ".txt"] + [input_params["file_name"] + "_1.txt"])
            async_result.wait()
            a = async_result.get()
            input_params["input_result"] = a
            input_signal.calculation_finished.emit()

        schedule = sched.scheduler(time.time, time.sleep)
        event = schedule.enter((date_of_start - datetime.datetime.now()).total_seconds(), 1, get_result_of_writing)

        thread = Thread(target=self.start_writing, args=[schedule])
        thread.start()
        
        result = confirm_pop_up.exec()
        if not result and self.input_params["input_result"] == None:
            pool.close()
            try:
                schedule.cancel(event)
            except ValueError:
                pass
            finally:
                self.change_state_of_start_button()

    def create_confirm_pop_up(self, params: dict):
        confirm_pop_up = QMessageBox(self)
        confirm_pop_up.setObjectName("confirmPopUp")
        confirm_pop_up.setIcon(QMessageBox.Icon.Information)
        confirm_pop_up.setWindowTitle("Подтверждение операции")
        confirm_pop_up.setStandardButtons(QMessageBox.StandardButton.Ok)
        confirm_pop_up.addButton("Отменить", QMessageBox.ButtonRole.RejectRole)
        confirm_pop_up.setText("Потвердите операцию записи:")
        confirm_pop_up.setInformativeText(f"""<b>Имя файла:</b> {self.input_params["file_name"]}<br />
                                            <b>Папка, в которой будет находиться файл:</b> {self.input_params["dir_path"]}<br />
                                            <b>Расстояние между датчиками:</b> {self.input_params["distance"]}<br />
                                            <b>Скорость звука в трубе:</b> {self.input_params["sound_speed"]}<br />
                                            <b>Дата и время начала записи:</b> {params["date_string"]}<br />
                                            <i>(По наступлении этого времени запись начнётся автоматически, если Вы не закроете программу и не нажмёте кнопку "Отмена")</i>
                                          """)
        
        return confirm_pop_up
        
    def handle_end_of_writing(self):
        result = self.input_params["input_result"]
        if not result:
            self.show_error("Не удалось записать данные в файл.", "Проверьте правильность введённых данных, в частности, номер COM-порта.")
        else:
            dir_path = self.input_params["dir_path"]
            self.show_info("Данные успешно записаны в файл.", f"Файл находится в папке <i>{dir_path}</i>")

        self.dir_button = self.findChild(QPushButton, "dirChooseButton")
        self.dir_button.setText("Выберите папку")
        self.dir_button.setStyleSheet("QPushButton {max-width: 120px; padding: 5px; color: white; background-color: navy; border: 0; font-weight: bold}")
        self.findChild(QLabel, "dirName").setText("Не выбрана")

        for name in ["startHour", "startMinute"]:
            self.findChild(CustomSpinBox, name).setValue(0)

        for name in ["input_distance", "input_soundSpeed"]:
            self.findChild(CustomSpinBox, name).setValue(0)

        self.findChild(QLineEdit, "fileName").setText("")

        confirm_pop_up = self.findChild(QMessageBox, "confirmPopUp")
        if confirm_pop_up:
            confirm_pop_up.close()

        for key in self.input_params:
            self.input_params[key] = None

    def start_writing(self, schedule):
        record_start_button = self.findChild(QPushButton, "recordStartButton")
        record_start_button.setDisabled(True)
        record_start_button.setStyleSheet("""QPushButton {color: dimgray; font-weight: normal; background-color: lightgray; max-width: 100px}
                                         QTooltip {background-color: white; color: black; font-weight: normal}""")
        record_start_button.setToolTip("Дождитесь окончания предыдущей записи")
        schedule.run()

    def show_info(self, main_text="", informative_text=""):
        info_box = QMessageBox(self)
        info_box.setIcon(QMessageBox.Icon.Information)
        info_box.setText(main_text)
        info_box.setInformativeText(informative_text)
        info_box.setWindowTitle("Сообщение")
        info_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        info_box.exec()
    

class Canvas(FigureCanvas):
    def __init__(self) -> None:
        figure = Figure(figsize=(500, 500), facecolor="white")
        self.axes = figure.add_subplot()
        super().__init__(figure)

app = QApplication([])

window = MainWindow()
window.show()
        
app.exec()
