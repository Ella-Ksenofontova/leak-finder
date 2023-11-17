from PyQt6.QtWidgets import QApplication, \
    QMainWindow, \
    QVBoxLayout, \
    QHBoxLayout, \
    QPushButton, \
    QDoubleSpinBox, \
    QLabel, \
    QWidget
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.left_column = QVBoxLayout()
        self.fill_left_column()

        self.right_column = QVBoxLayout()
        self.fill_right_column()

        self.screen_layout = QHBoxLayout()
        self.screen_layout.addLayout(self.left_column, stretch=1)
        self.screen_layout.addLayout(self.right_column, stretch=1)

        self.screen = QWidget()
        self.screen.setLayout(self.screen_layout)
        self.setCentralWidget(self.screen)

        self.setWindowTitle("Просмотр данных с датчиков")
        self.setMaximumSize(800, 200)

    def fill_left_column(self):
        self.add_layout_with_spinboxes()

        calculation_button = QPushButton("Расчёт")
        calculation_button.setMaximumSize(100, 100)
        self.left_column.addWidget(calculation_button)

        labels_texts = ["Относительно центра: ",
                        "Относительно датчика A: ",
                        "Относительно датчика B: "]

        for label_text in labels_texts:
            label = QLabel(label_text)
            self.left_column.addWidget(label, stretch=1)

    def add_layout_with_spinboxes(self):
        spinboxes_and_labels_layout = QHBoxLayout()

        labels_layout = QVBoxLayout()
        sound_speed_label = QLabel("Скорость звука, м/с:")
        sound_speed_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        labels_layout.addWidget(sound_speed_label, stretch=1)
        distance_label = QLabel("Расстояние между датчиками:")  # Уточнить единицу измерения
        distance_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        labels_layout.addWidget(distance_label, stretch=1)
        spinboxes_and_labels_layout.addLayout(labels_layout)

        spinboxes_layout = QVBoxLayout()
        sound_speed_spinbox = QDoubleSpinBox()
        sound_speed_spinbox.setStyleSheet("width: 150px")
        spinboxes_layout.addWidget(sound_speed_spinbox, stretch=1)
        spinboxes_and_labels_layout.addLayout(spinboxes_layout, stretch=1)
        distance_spinbox = QDoubleSpinBox()
        distance_spinbox.setStyleSheet("width: 150px")
        spinboxes_layout.addWidget(distance_spinbox, stretch=1)
        spinboxes_and_labels_layout.addLayout(spinboxes_layout, stretch=1)

        self.left_column.addLayout(spinboxes_and_labels_layout)

    def fill_right_column(self):
        labels_texts = ["График 1 (датчик A)",
                        "График 2 (датчик B)",
                        "Корреляционная функция"]

        for label_text in labels_texts:
            label = QLabel(label_text)
            self.right_column.addWidget(label, stretch=1)
            label.setStyleSheet("font-size: 14px; font-weight: 600")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            plot = QLabel("Здесь будет график") #Потом нужно будет поменять на график
            plot.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.right_column.addWidget(plot, stretch=1)


app = QApplication([])

window = MainWindow()
window.show()

app.exec()
#Test comment
