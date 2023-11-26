from PyQt6.QtWidgets import QApplication, \
    QMainWindow, \
    QPushButton, \
    QDoubleSpinBox, \
    QLabel, \
    QWidget, \
    QGridLayout, \
    QComboBox, \
    QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


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
        
        self.central_widget_layout = QGridLayout()
        self.central_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.fill_left_column()
        self.fill_right_column()

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_widget_layout)
        self.central_widget.setMaximumHeight(250)

        self.screen_layout = QHBoxLayout()
        self.add_widgets_to_screen_layout()

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
        side_widget_2 = QWidget()
        side_widget_2.setStyleSheet("background-color: white")
        self.screen_layout.addWidget(side_widget_2)

    def fill_left_column(self):
        label = QLabel("<h2>Ввод параметров</h2>")
        label.setStyleSheet("font-weight: 600; color: #033E6B")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.central_widget_layout.addWidget(label, 0, 0, 0, 2)

        calculation_button = QPushButton("Расчёт")
        calculation_button.setMaximumSize(100, 100)
        calculation_button.setStyleSheet("max-height: 20px;margin-top: 3px; background-color: navy; "
                                         "border: 1px solid midnigthblue; "
                                         "color: white; font-weight: bold; font-size:14px")
        self.central_widget_layout.addWidget(calculation_button, 5, 0)

        self.add_labels()
        self.add_spinboxes_and_combobox()

        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]

        for i in range(len(labels_texts)):
            label = QLabel(labels_texts[i])
            label.setStyleSheet("font-size: 14px")

            self.central_widget_layout.addWidget(label, i + 6, 0)

    def add_labels(self):
        labels_texts = ["Скорость звука, м/с:", "Расстояние между датчиками:", "Диаметр трубы:", "Материал трубы:"]

        for i in range(len(labels_texts)):
            label = QLabel(labels_texts[i])
            label.setStyleSheet("font-size: 14px")
            self.central_widget_layout.addWidget(label, i + 1, 0)

    def add_spinboxes_and_combobox(self):
        identifiers = ["soundSpeedSpinBox", "distanceSpinBox", "diameterSpinBox"]

        for i in range(3):
            spinbox = QDoubleSpinBox()
            spinbox.setObjectName(identifiers[i])
            spinbox.setStyleSheet("margin-right: 20px; min-width: 150px; max-width: 200px;"
                                  "background-color: white; font-size: 14px")
            spinbox.setMaximum(100000)
            self.central_widget_layout.addWidget(spinbox, i + 1, 1)

        material_combobox = QComboBox()
        material_combobox.addItems(["Выберите материал...", "Сталь", "Медь", "Полиэтилен", "Полипропилен",
                                    "Поливинилхлорид"])
        material_combobox.setStyleSheet("max-width: 165px; background-color: white; border: 1px solid gainsboro")
        material_combobox.currentTextChanged.connect(self.change_sound_speed)
        self.central_widget_layout.addWidget(material_combobox, 4, 1)

    def change_sound_speed(self, material):
        spinbox_with_sound_speed = self.central_widget.findChild(QDoubleSpinBox, "soundSpeedSpinBox")
        if material in self.sound_speeds:
            spinbox_with_sound_speed.setValue(self.sound_speeds[material])
        else:
            spinbox_with_sound_speed.setValue(0)


    def fill_right_column(self):
        common_label = QLabel("<h2>Графики</h2>")
        common_label.setStyleSheet("font-weight: 600; color: #033E6B")
        common_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.central_widget_layout.addWidget(common_label, 0, 2)

        labels_texts = ["График 1 (датчик A)",
                        "График 2 (датчик B)",
                        "Корреляционная функция"]

        for i in range(len(labels_texts)):
            label = QLabel(f"<h3>{labels_texts[i]}</h3>")
            label.setAlignment(Qt.AlignmentFlag.AlignTop)
            label.setStyleSheet("font-weight: 600; color: #033E6B")
            self.central_widget_layout.addWidget(label, i * 2 + 1, 2)

            plot = QLabel("Здесь будет график")   # Потом нужно будет поменять на график
            plot.setAlignment(Qt.AlignmentFlag.AlignTop)
            plot.setStyleSheet("font-size: 14px")
            self.central_widget_layout.addWidget(plot, i * 2 + 2, 2)


app = QApplication([])

window = MainWindow()
window.show()

app.exec()
