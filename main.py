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
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
)


current_image = None


def update_display(img):
    if img is None:
        label.clear()
        return

    if img.ndim == 2:
        # grayscale
        q_img = QImage(
            np.ascontiguousarray(img), img.shape[1], img.shape[0], img.shape[1], QImage.Format.Format_Grayscale8
        )
    else:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

    pixmap = QPixmap.fromImage(q_img)
    label.setPixmap(pixmap.scaled(800, 500, Qt.AspectRatioMode.KeepAspectRatio))


def apply_adjustments():
    global current_image
    if current_image is None:
        return

    brightness = brightness_slider.value()
    contrast = contrast_slider.value() / 100.0
    sat_scale = saturation_slider.value() / 100.0
    blur_val = blur_slider.value()

    adjusted = cv2.convertScaleAbs(current_image, alpha=contrast, beta=brightness)

    if sat_scale != 1.0 and adjusted.ndim == 3:
        hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_scale, 0, 255)
        adjusted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if blur_val > 0:
        ksize = blur_val * 2 + 1
        adjusted = cv2.GaussianBlur(adjusted, (ksize, ksize), 0)

    if grayscale_checkbox.isChecked():
        adjusted = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)

    update_display(adjusted)


def open_file():
    global current_image
    file_path, _ = QFileDialog.getOpenFileName(window, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
    if file_path:
        img = cv2.imread(file_path)
        if img is not None:
            current_image = img.copy()
            brightness_slider.setValue(0)
            contrast_slider.setValue(100)
            saturation_slider.setValue(100)
            blur_slider.setValue(0)
            grayscale_checkbox.setChecked(False)
            update_display(current_image)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("RawStudio")
    window.resize(1100, 650)
    window.setStyleSheet("background-color: #1e1e1e;")

    layout = QVBoxLayout()

    label = QLabel("RawStudio Canvas")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("color: #ffffff; font-size: 16px;")

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

    saturation_slider = QSlider(Qt.Orientation.Horizontal)
    saturation_slider.setRange(0, 200)
    saturation_slider.setValue(100)
    saturation_slider.valueChanged.connect(apply_adjustments)

    blur_slider = QSlider(Qt.Orientation.Horizontal)
    blur_slider.setRange(0, 20)
    blur_slider.setValue(0)
    blur_slider.valueChanged.connect(apply_adjustments)

    grayscale_checkbox = QCheckBox("Grayscale")
    grayscale_checkbox.setStyleSheet("color: #ffffff;")
    grayscale_checkbox.stateChanged.connect(apply_adjustments)

    controls_layout.addWidget(open_button)
    controls_layout.addWidget(QLabel("Brightness:"))
    controls_layout.addWidget(brightness_slider)
    controls_layout.addWidget(QLabel("Contrast:"))
    controls_layout.addWidget(contrast_slider)
    controls_layout.addWidget(QLabel("Saturation:"))
    controls_layout.addWidget(saturation_slider)
    controls_layout.addWidget(QLabel("Blur:"))
    controls_layout.addWidget(blur_slider)
    controls_layout.addWidget(grayscale_checkbox)

    layout.addWidget(label)
    layout.addLayout(controls_layout)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())