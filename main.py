import sys
import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
)


current_image = None


def update_display(img):
    if img is None:
        label.clear()
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


def open_file():
    global current_image
    file_path, _ = QFileDialog.getOpenFileName(
        None, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
    )
    if not file_path:
        return
    img = cv2.imread(file_path)
    if img is None:
        print(f"Failed to load image: {file_path}")
        return
    current_image = img
    brightness_slider.setValue(0)
    contrast_slider.setValue(100)
    update_display(current_image)


def apply_adjustments():
    if current_image is None:
        return
    brightness = brightness_slider.value()
    contrast = contrast_slider.value() / 100.0
    adjusted = cv2.convertScaleAbs(current_image, alpha=contrast, beta=int(brightness))
    update_display(adjusted)


app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1000, 650)
window.setStyleSheet("background-color: #1e1e1e;")
layout = QVBoxLayout()

label = QLabel("RawStudio Canvas")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("color: #ffffff; font-size: 16px;")
label.setFixedSize(800, 500)

controls_layout = QHBoxLayout()

open_button = QPushButton("Open Image")
open_button.setStyleSheet("background-color: #333333; color: #ffffff; padding: 8px;")
open_button.clicked.connect(open_file)

brightness_slider = QSlider(Qt.Orientation.Horizontal)
brightness_slider.setRange(-100, 100)
brightness_slider.setValue(0)
brightness_slider.valueChanged.connect(apply_adjustments)

contrast_slider = QSlider(Qt.Orientation.Horizontal)
contrast_slider.setRange(10, 300)
contrast_slider.setValue(100)
contrast_slider.valueChanged.connect(apply_adjustments)

controls_layout.addWidget(open_button)
controls_layout.addWidget(QLabel("Brightness:"))
controls_layout.addWidget(brightness_slider)
controls_layout.addWidget(QLabel("Contrast:"))
controls_layout.addWidget(contrast_slider)

layout.addWidget(label)
layout.addLayout(controls_layout)

window.setLayout(layout)
window.show()

sys.exit(app.exec())
