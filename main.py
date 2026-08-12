import sys

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

current_image = None
processed_image = None
rotation_angle = 0


def update_display(img):
    if img is None:
        return
    if len(img.shape) == 2:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    else:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    h, w, ch = rgb_img.shape
    bytes_per_line = ch * w
    q_img = QImage(
        rgb_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
    )
    pixmap = QPixmap.fromImage(q_img)
    label.setPixmap(
        pixmap.scaled(800, 500, Qt.AspectRatioMode.KeepAspectRatio)
    )


def open_file():
    global current_image
    file_path, _ = QFileDialog.getOpenFileName(
        None, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
    )
    if file_path:
        img = cv2.imread(file_path)
        if img is not None:
            current_image = img
            reset_controls()


def save_file():
    global processed_image
    if processed_image is None:
        return
    file_path, _ = QFileDialog.getSaveFileName(
        None,
        "Save Image",
        "",
        "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;Bitmap (*.bmp)",
    )
    if file_path:
        cv2.imwrite(file_path, processed_image)


def reset_controls():
    global rotation_angle
    rotation_angle = 0
    brightness_slider.setValue(0)
    contrast_slider.setValue(100)
    saturation_slider.setValue(100)
    blur_slider.setValue(0)
    sharpen_slider.setValue(0)
    grayscale_checkbox.setChecked(False)
    apply_adjustments()


def rotate_image():
    global rotation_angle
    rotation_angle = (rotation_angle + 90) % 360
    apply_adjustments()


def apply_adjustments():
    global current_image, processed_image
    if current_image is None:
        return

    brightness = brightness_slider.value()
    contrast = contrast_slider.value() / 100.0
    sat_scale = saturation_slider.value() / 100.0
    blur_val = blur_slider.value()
    sharpen_val = sharpen_slider.value()

    adjusted = current_image.copy()

    if rotation_angle == 90:
        adjusted = cv2.rotate(adjusted, cv2.ROTATE_90_CLOCKWISE)
    elif rotation_angle == 180:
        adjusted = cv2.rotate(adjusted, cv2.ROTATE_180)
    elif rotation_angle == 270:
        adjusted = cv2.rotate(adjusted, cv2.ROTATE_90_COUNTERCLOCKWISE)

    adjusted = cv2.convertScaleAbs(
        adjusted, alpha=contrast, beta=brightness
    )

    if sat_scale != 1.0:
        hsv = cv2.cvtColor(adjusted, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat_scale, 0, 255)
        adjusted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if blur_val > 0:
        ksize = blur_val * 2 + 1
        adjusted = cv2.GaussianBlur(adjusted, (ksize, ksize), 0)

    if sharpen_val > 0:
        blurred = cv2.GaussianBlur(adjusted, (0, 0), 3)
        strength = sharpen_val * 0.2
        adjusted = cv2.addWeighted(
            adjusted, 1.0 + strength, blurred, -strength, 0
        )

    if grayscale_checkbox.isChecked():
        adjusted = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)

    processed_image = adjusted
    update_display(processed_image)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("RawStudio")
    window.resize(1300, 650)
    window.setStyleSheet("background-color: #1e1e1e;")
    layout = QVBoxLayout()

    label = QLabel("RawStudio Canvas")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet("color: #ffffff; font-size: 16px;")

    controls_layout = QHBoxLayout()

    open_button = QPushButton("Open Image")
    open_button.setStyleSheet(
        "background-color: #333333; color: #ffffff; padding: 8px;"
    )
    open_button.clicked.connect(open_file)

    save_button = QPushButton("Save Image")
    save_button.setStyleSheet(
        "background-color: #0e639c; color: #ffffff; padding: 8px;"
    )
    save_button.clicked.connect(save_file)

    rotate_button = QPushButton("Rotate 90°")
    rotate_button.setStyleSheet(
        "background-color: #333333; color: #ffffff; padding: 8px;"
    )
    rotate_button.clicked.connect(rotate_image)

    reset_button = QPushButton("Reset")
    reset_button.setStyleSheet(
        "background-color: #8b0000; color: #ffffff; padding: 8px;"
    )
    reset_button.clicked.connect(reset_controls)

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

    sharpen_slider = QSlider(Qt.Orientation.Horizontal)
    sharpen_slider.setRange(0, 10)
    sharpen_slider.setValue(0)
    sharpen_slider.valueChanged.connect(apply_adjustments)

    grayscale_checkbox = QCheckBox("Grayscale")
    grayscale_checkbox.setStyleSheet("color: #ffffff;")
    grayscale_checkbox.stateChanged.connect(apply_adjustments)

    controls_layout.addWidget(open_button)
    controls_layout.addWidget(save_button)
    controls_layout.addWidget(rotate_button)
    controls_layout.addWidget(reset_button)
    controls_layout.addWidget(QLabel("Brightness:"))
    controls_layout.addWidget(brightness_slider)
    controls_layout.addWidget(QLabel("Contrast:"))
    controls_layout.addWidget(contrast_slider)
    controls_layout.addWidget(QLabel("Saturation:"))
    controls_layout.addWidget(saturation_slider)
    controls_layout.addWidget(QLabel("Blur:"))
    controls_layout.addWidget(blur_slider)
    controls_layout.addWidget(QLabel("Sharpen:"))
    controls_layout.addWidget(sharpen_slider)
    controls_layout.addWidget(grayscale_checkbox)

    layout.addWidget(label)
    layout.addLayout(controls_layout)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())
