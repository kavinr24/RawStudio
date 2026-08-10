import sys
import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
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
    if not file_path:
        return

    img = cv2.imread(file_path)
    if img is None:
        print(f"Failed to load image: {file_path}")
        return

    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_img.shape
    bytes_per_line = ch * w
    q_img = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    pixmap = QPixmap.fromImage(q_img)
    scaled = pixmap.scaled(
        800, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
    )
    label.setPixmap(scaled)


app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1000, 650)
window.setStyleSheet("background-color: #1e1e1e;")

layout = QVBoxLayout()

label = QLabel("RawStudio")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("color: #ffffff; font-size: 16px;")
label.setFixedSize(800, 500)

open_button = QPushButton("Open Image")
open_button.setStyleSheet("background-color: #333333; color: #ffffff; padding: 8px;")
open_button.clicked.connect(open_file)

layout.addWidget(label)
layout.addWidget(open_button)

window.setLayout(layout)
window.show()

sys.exit(app.exec())
