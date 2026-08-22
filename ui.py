import sys

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from processor import get_histogram_image, process_image


current_image = None
preview_image = None
processed_preview = None
rotation_angle = 0


def create_sidebar_ui():
    histogram_label = QLabel()
    histogram_label.setFixedSize(256, 120)
    histogram_label.setStyleSheet(
        "background-color: #111111; border: 1px solid #333333;"
    )
    histogram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    tabs = QTabWidget()
    tabs.setStyleSheet(
        "QTabWidget::pane { border: 1px solid #333333; } "
        "QTabBar::tab { background: #252526; color: #cccccc; "
        "padding: 6px 12px; } "
        "QTabBar::tab:selected { background: #333333; color: #ffffff; }"
    )

    basic_tab = QWidget()
    basic_layout = QFormLayout()
    basic_layout.setContentsMargins(10, 10, 10, 10)

    exposure_slider = QSlider(Qt.Orientation.Horizontal)
    exposure_slider.setRange(-100, 100)
    exposure_slider.setValue(0)

    brightness_slider = QSlider(Qt.Orientation.Horizontal)
    brightness_slider.setRange(-100, 100)
    brightness_slider.setValue(0)

    contrast_slider = QSlider(Qt.Orientation.Horizontal)
    contrast_slider.setRange(10, 300)
    contrast_slider.setValue(100)

    saturation_slider = QSlider(Qt.Orientation.Horizontal)
    saturation_slider.setRange(0, 200)
    saturation_slider.setValue(100)

    basic_layout.addRow(QLabel("Exposure:"), exposure_slider)
    basic_layout.addRow(QLabel("Brightness:"), brightness_slider)
    basic_layout.addRow(QLabel("Contrast:"), contrast_slider)
    basic_layout.addRow(QLabel("Saturation:"), saturation_slider)
    basic_tab.setLayout(basic_layout)

    color_tab = QWidget()
    color_layout = QFormLayout()
    color_layout.setContentsMargins(10, 10, 10, 10)

    temperature_slider = QSlider(Qt.Orientation.Horizontal)
    temperature_slider.setRange(-100, 100)
    temperature_slider.setValue(0)

    red_slider = QSlider(Qt.Orientation.Horizontal)
    red_slider.setRange(0, 200)
    red_slider.setValue(100)

    green_slider = QSlider(Qt.Orientation.Horizontal)
    green_slider.setRange(0, 200)
    green_slider.setValue(100)

    blue_slider = QSlider(Qt.Orientation.Horizontal)
    blue_slider.setRange(0, 200)
    blue_slider.setValue(100)

    color_layout.addRow(QLabel("Temperature:"), temperature_slider)
    color_layout.addRow(QLabel("Red:"), red_slider)
    color_layout.addRow(QLabel("Green:"), green_slider)
    color_layout.addRow(QLabel("Blue:"), blue_slider)
    color_tab.setLayout(color_layout)

    effects_tab = QWidget()
    effects_layout = QFormLayout()
    effects_layout.setContentsMargins(10, 10, 10, 10)

    blur_slider = QSlider(Qt.Orientation.Horizontal)
    blur_slider.setRange(0, 20)
    blur_slider.setValue(0)

    sharpen_slider = QSlider(Qt.Orientation.Horizontal)
    sharpen_slider.setRange(0, 10)
    sharpen_slider.setValue(0)

    flip_h_checkbox = QCheckBox("Flip H")
    flip_h_checkbox.setStyleSheet("color: #ffffff;")

    flip_v_checkbox = QCheckBox("Flip V")
    flip_v_checkbox.setStyleSheet("color: #ffffff;")

    grayscale_checkbox = QCheckBox("Grayscale")
    grayscale_checkbox.setStyleSheet("color: #ffffff;")

    rotate_button = QPushButton("Rotate 90°")
    rotate_button.setStyleSheet(
        "background-color: #333333; color: #ffffff; padding: 8px;"
    )

    effects_layout.addRow(QLabel("Blur:"), blur_slider)
    effects_layout.addRow(QLabel("Sharpen:"), sharpen_slider)
    effects_layout.addRow(flip_h_checkbox)
    effects_layout.addRow(flip_v_checkbox)
    effects_layout.addRow(grayscale_checkbox)
    effects_layout.addRow(rotate_button)
    effects_tab.setLayout(effects_layout)

    tabs.addTab(basic_tab, "Basic")
    tabs.addTab(color_tab, "Color")
    tabs.addTab(effects_tab, "Effects")

    open_button = QPushButton("Open Image")
    open_button.setStyleSheet(
        "background-color: #333333; color: #ffffff; padding: 8px;"
    )

    save_button = QPushButton("Save Image")
    save_button.setStyleSheet(
        "background-color: #0e639c; color: #ffffff; padding: 8px;"
    )

    compare_button = QPushButton("Compare (Hold)")
    compare_button.setStyleSheet(
        "background-color: #444444; color: #ffffff; padding: 8px;"
    )

    reset_button = QPushButton("Reset")
    reset_button.setStyleSheet(
        "background-color: #8b0000; color: #ffffff; padding: 8px;"
    )

    action_layout = QHBoxLayout()
    action_layout.addWidget(open_button)
    action_layout.addWidget(save_button)

    action_layout2 = QHBoxLayout()
    action_layout2.addWidget(compare_button)
    action_layout2.addWidget(reset_button)

    sidebar_layout = QVBoxLayout()
    sidebar_layout.addWidget(
        histogram_label, alignment=Qt.AlignmentFlag.AlignCenter
    )
    sidebar_layout.addWidget(tabs)
    sidebar_layout.addLayout(action_layout)
    sidebar_layout.addLayout(action_layout2)

    sidebar_widget = QWidget()
    sidebar_widget.setLayout(sidebar_layout)
    sidebar_widget.setFixedWidth(320)

    return {
        "sidebar": sidebar_widget,
        "histogram_label": histogram_label,
        "exposure": exposure_slider,
        "brightness": brightness_slider,
        "contrast": contrast_slider,
        "saturation": saturation_slider,
        "temperature": temperature_slider,
        "red": red_slider,
        "green": green_slider,
        "blue": blue_slider,
        "blur": blur_slider,
        "sharpen": sharpen_slider,
        "flip_h": flip_h_checkbox,
        "flip_v": flip_v_checkbox,
        "grayscale": grayscale_checkbox,
        "rotate_btn": rotate_button,
        "open_btn": open_button,
        "save_btn": save_button,
        "compare_btn": compare_button,
        "reset_btn": reset_button,
    }


def update_display(img):
    if img is None:
        return

    if len(img.shape) == 2:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    else:
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    height, width, channels = rgb_img.shape
    bytes_per_line = channels * width
    q_img = QImage(
        rgb_img.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888,
    )
    pixmap = QPixmap.fromImage(q_img)
    label.setPixmap(
        pixmap.scaled(
            800,
            500,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    )

    hist_img = get_histogram_image(img)
    if hist_img is not None:
        hist_rgb = cv2.cvtColor(hist_img, cv2.COLOR_BGR2RGB)
        hist_height, hist_width, hist_channels = hist_rgb.shape
        q_hist = QImage(
            hist_rgb.data,
            hist_width,
            hist_height,
            hist_channels * hist_width,
            QImage.Format.Format_RGB888,
        )
        histogram_label.setPixmap(QPixmap.fromImage(q_hist))


def create_preview(img, max_dim=1280):
    if img is None:
        return None

    height, width = img.shape[:2]
    if max(height, width) > max_dim:
        scale = max_dim / float(max(height, width))
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(
            img, (new_width, new_height), interpolation=cv2.INTER_AREA
        )
    return img.copy()


def open_file():
    global current_image, preview_image

    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Open Image",
        "",
        "Image Files (*.png *.jpg *.jpeg *.bmp)",
    )
    if file_path:
        img = cv2.imread(file_path)
        if img is not None:
            current_image = img
            preview_image = create_preview(current_image)
            reset_controls()


def save_file():
    if current_image is None:
        return

    file_path, _ = QFileDialog.getSaveFileName(
        None,
        "Save Image",
        "",
        "PNG Image (*.png);;JPEG Image (*.jpg *.jpeg);;Bitmap (*.bmp)",
    )
    if file_path:
        full_res_output = process_image(
            img=current_image,
            rotation_angle=rotation_angle,
            flip_h=ctrl["flip_h"].isChecked(),
            flip_v=ctrl["flip_v"].isChecked(),
            exposure=ctrl["exposure"].value(),
            brightness=ctrl["brightness"].value(),
            contrast=ctrl["contrast"].value() / 100.0,
            temperature=ctrl["temperature"].value(),
            saturation=ctrl["saturation"].value() / 100.0,
            r_scale=ctrl["red"].value() / 100.0,
            g_scale=ctrl["green"].value() / 100.0,
            b_scale=ctrl["blue"].value() / 100.0,
            blur=ctrl["blur"].value(),
            sharpen=ctrl["sharpen"].value(),
            grayscale=ctrl["grayscale"].isChecked(),
        )
        cv2.imwrite(file_path, full_res_output)


def reset_controls():
    global rotation_angle

    rotation_angle = 0
    ctrl["exposure"].setValue(0)
    ctrl["brightness"].setValue(0)
    ctrl["contrast"].setValue(100)
    ctrl["temperature"].setValue(0)
    ctrl["saturation"].setValue(100)
    ctrl["red"].setValue(100)
    ctrl["green"].setValue(100)
    ctrl["blue"].setValue(100)
    ctrl["blur"].setValue(0)
    ctrl["sharpen"].setValue(0)
    ctrl["flip_h"].setChecked(False)
    ctrl["flip_v"].setChecked(False)
    ctrl["grayscale"].setChecked(False)
    apply_adjustments()


def rotate_image():
    global rotation_angle

    rotation_angle = (rotation_angle + 90) % 360
    apply_adjustments()


def start_compare():
    if preview_image is not None:
        update_display(preview_image)


def stop_compare():
    if processed_preview is not None:
        update_display(processed_preview)


def apply_adjustments():
    global processed_preview

    if preview_image is None:
        return

    processed_preview = process_image(
        img=preview_image,
        rotation_angle=rotation_angle,
        flip_h=ctrl["flip_h"].isChecked(),
        flip_v=ctrl["flip_v"].isChecked(),
        exposure=ctrl["exposure"].value(),
        brightness=ctrl["brightness"].value(),
        contrast=ctrl["contrast"].value() / 100.0,
        temperature=ctrl["temperature"].value(),
        saturation=ctrl["saturation"].value() / 100.0,
        r_scale=ctrl["red"].value() / 100.0,
        g_scale=ctrl["green"].value() / 100.0,
        b_scale=ctrl["blue"].value() / 100.0,
        blur=ctrl["blur"].value(),
        sharpen=ctrl["sharpen"].value(),
        grayscale=ctrl["grayscale"].isChecked(),
    )
    update_display(processed_preview)


app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("RawStudio")
window.resize(1200, 750)
window.setStyleSheet("background-color: #1e1e1e;")

main_layout = QHBoxLayout()

label = QLabel("RawStudio Canvas")
label.setAlignment(Qt.AlignmentFlag.AlignCenter)
label.setStyleSheet("color: #ffffff; font-size: 16px;")

ctrl = create_sidebar_ui()
histogram_label = ctrl["histogram_label"]

for control_name in (
    "exposure",
    "brightness",
    "contrast",
    "saturation",
    "temperature",
    "red",
    "green",
    "blue",
    "blur",
    "sharpen",
):
    ctrl[control_name].valueChanged.connect(apply_adjustments)

for control_name in ("flip_h", "flip_v", "grayscale"):
    ctrl[control_name].stateChanged.connect(apply_adjustments)

ctrl["rotate_btn"].clicked.connect(rotate_image)
ctrl["open_btn"].clicked.connect(open_file)
ctrl["save_btn"].clicked.connect(save_file)
ctrl["compare_btn"].pressed.connect(start_compare)
ctrl["compare_btn"].released.connect(stop_compare)
ctrl["reset_btn"].clicked.connect(reset_controls)

main_layout.addWidget(label, stretch=1)
main_layout.addWidget(ctrl["sidebar"])

window.setLayout(main_layout)
window.show()

sys.exit(app.exec())
