import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QFileDialog,
)


def open_file():
    file_path, _ = QFileDialog.getOpenFileName(
        None, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
    )
    if file_path:
        pixmap = QPixmap(file_path)
        label.setPixmap(
            pixmap.scaled(800, 500, Qt.AspectRatioMode.KeepAspectRatio)
        )
app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1000, 650)
window.setStyleSheet("background-color: #1e1e1e;")

layout = QVBoxLayout()

label = QLabel("RawStudio")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("color: #ffffff; font-size: 16px;")

open_button = QPushButton("Open Image")
open_button.setStyleSheet(
    "background-color: #333333; color: #ffffff; padding: 8px;"
)
open_button.clicked.connect(open_file)

layout.addWidget(label)
layout.addWidget(open_button)

window.setLayout(layout)
window.show()

sys.exit(app.exec())

