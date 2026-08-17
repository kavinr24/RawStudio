import sys
import cv2
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

from processor import process_image, get_histogram_image

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

    hist_img = get_histogram_image(img)
    if hist_img is not None:
        hist_rgb = cv2.cvtColor(hist_img, cv2.COLOR_BGR2RGB)
        hh, ww, cc = hist_rgb.shape
        q_hist = QImage(
            hist_rgb.data, ww, hh, cc * ww, QImage.Format.Format_RGB888
        )
        histogram_label.setPixmap(QPixmap.fromImage(q_hist))


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
    exposure_slider.setValue(0)
    brightness_slider.setValue(0)
    contrast_slider.setValue(100)
    temperature_slider.setValue(0)
    saturation_slider.setValue(100)
    red_slider.setValue(100)
    green_slider.setValue(100)
    blue_slider.setValue(100)
    blur_slider.setValue(0)
    sharpen_slider.setValue(0)
    flip_h_checkbox.setChecked(False)
    flip_v_checkbox.setChecked(False)
    grayscale_checkbox.setChecked(False)
    apply_adjustments()


def rotate_image():
    global rotation_angle
    rotation_angle = (rotation_angle + 90) % 360
    apply_adjustments()


def start_compare():
    if current_image is not None:
        update_display(current_image)


def stop_compare():
    if processed_image is not None:
        update_display(processed_image)


def apply_adjustments():
    global current_image, processed_image, rotation_angle
    if current_image is None:
        return

    processed_image = process_image(
        img=current_image,
        rotation_angle=rotation_angle,
        flip_h=flip_h_checkbox.isChecked(),
        flip_v=flip_v_checkbox.isChecked(),
        exposure=exposure_slider.value(),
        brightness=brightness_slider.value(),
        contrast=contrast_slider.value() / 100.0,
        temperature=temperature_slider.value(),
        saturation=saturation_slider.value() / 100.0,
        r_scale=red_slider.value() / 100.0,
        g_scale=green_slider.value() / 100.0,
        b_scale=blue_slider.value() / 100.0,
        blur=blur_slider.value(),
        sharpen=sharpen_slider.value(),
        grayscale=grayscale_checkbox.isChecked(),
    )

    update_display(processed_image)


app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1500, 750)
window.setStyleSheet("background-color: #1e1e1e;")

layout = QVBoxLayout()

main_display_layout = QHBoxLayout()

label = QLabel("RawStudio Canvas")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("color: #ffffff; font-size: 16px;")

histogram_label = QLabel()
histogram_label.setFixedSize(256, 120)
histogram_label.setStyleSheet(
    "background-color: #111111; border: 1px solid #333333;"
)
histogram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

main_display_layout.addWidget(label, stretch=1)
main_display_layout.addWidget(histogram_label, stretch=0)

controls_layout1 = QHBoxLayout()
controls_layout2 = QHBoxLayout()

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

compare_button = QPushButton("Compare (Hold)")
compare_button.setStyleSheet(
    "background-color: #444444; color: #ffffff; padding: 8px;"
)
compare_button.pressed.connect(start_compare)
compare_button.released.connect(stop_compare)

reset_button = QPushButton("Reset")
reset_button.setStyleSheet(
    "background-color: #8b0000; color: #ffffff; padding: 8px;"
)
reset_button.clicked.connect(reset_controls)

exposure_slider = QSlider(Qt.Orientation.Horizontal)
exposure_slider.setRange(-100, 100)
exposure_slider.setValue(0)
exposure_slider.valueChanged.connect(apply_adjustments)

brightness_slider = QSlider(Qt.Orientation.Horizontal)
brightness_slider.setRange(-100, 100)
brightness_slider.setValue(0)
brightness_slider.valueChanged.connect(apply_adjustments)

contrast_slider = QSlider(Qt.Orientation.Horizontal)
contrast_slider.setRange(10, 300)
contrast_slider.setValue(100)
contrast_slider.valueChanged.connect(apply_adjustments)

temperature_slider = QSlider(Qt.Orientation.Horizontal)
temperature_slider.setRange(-100, 100)
temperature_slider.setValue(0)
temperature_slider.valueChanged.connect(apply_adjustments)

saturation_slider = QSlider(Qt.Orientation.Horizontal)
saturation_slider.setRange(0, 200)
saturation_slider.setValue(100)
saturation_slider.valueChanged.connect(apply_adjustments)

red_slider = QSlider(Qt.Orientation.Horizontal)
red_slider.setRange(0, 200)
red_slider.setValue(100)
red_slider.valueChanged.connect(apply_adjustments)

green_slider = QSlider(Qt.Orientation.Horizontal)
green_slider.setRange(0, 200)
green_slider.setValue(100)
green_slider.valueChanged.connect(apply_adjustments)

blue_slider = QSlider(Qt.Orientation.Horizontal)
blue_slider.setRange(0, 200)
blue_slider.setValue(100)
blue_slider.valueChanged.connect(apply_adjustments)

blur_slider = QSlider(Qt.Orientation.Horizontal)
blur_slider.setRange(0, 20)
blur_slider.setValue(0)
blur_slider.valueChanged.connect(apply_adjustments)

sharpen_slider = QSlider(Qt.Orientation.Horizontal)
sharpen_slider.setRange(0, 10)
sharpen_slider.setValue(0)
sharpen_slider.valueChanged.connect(apply_adjustments)

flip_h_checkbox = QCheckBox("Flip H")
flip_h_checkbox.setStyleSheet("color: #ffffff;")
flip_h_checkbox.stateChanged.connect(apply_adjustments)

flip_v_checkbox = QCheckBox("Flip V")
flip_v_checkbox.setStyleSheet("color: #ffffff;")
flip_v_checkbox.stateChanged.connect(apply_adjustments)

grayscale_checkbox = QCheckBox("Grayscale")
grayscale_checkbox.setStyleSheet("color: #ffffff;")
grayscale_checkbox.stateChanged.connect(apply_adjustments)

controls_layout1.addWidget(open_button)
controls_layout1.addWidget(save_button)
controls_layout1.addWidget(rotate_button)
controls_layout1.addWidget(compare_button)
controls_layout1.addWidget(reset_button)
controls_layout1.addWidget(QLabel("Exposure:"))
controls_layout1.addWidget(exposure_slider)
controls_layout1.addWidget(QLabel("Brightness:"))
controls_layout1.addWidget(brightness_slider)
controls_layout1.addWidget(QLabel("Contrast:"))
controls_layout1.addWidget(contrast_slider)
controls_layout1.addWidget(QLabel("Temp:"))
controls_layout1.addWidget(temperature_slider)
controls_layout1.addWidget(QLabel("Saturation:"))
controls_layout1.addWidget(saturation_slider)

controls_layout2.addWidget(QLabel("Red:"))
controls_layout2.addWidget(red_slider)
controls_layout2.addWidget(QLabel("Green:"))
controls_layout2.addWidget(green_slider)
controls_layout2.addWidget(QLabel("Blue:"))
controls_layout2.addWidget(blue_slider)
controls_layout2.addWidget(QLabel("Blur:"))
controls_layout2.addWidget(blur_slider)
controls_layout2.addWidget(QLabel("Sharpen:"))
controls_layout2.addWidget(sharpen_slider)
controls_layout2.addWidget(flip_h_checkbox)
controls_layout2.addWidget(flip_v_checkbox)
controls_layout2.addWidget(grayscale_checkbox)

layout.addLayout(main_display_layout)
layout.addLayout(controls_layout1)
layout.addLayout(controls_layout2)

window.setLayout(layout)
window.show()

sys.exit(app.exec())
