import sys

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QHBoxLayout,
    QFileDialog,
)

from processor import process_image, get_histogram_image
from ui import create_sidebar_ui

current_image = None
preview_image = None
processed_preview = None
rotation_angle = 0


def create_preview(img, max_dim=1280):
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img.copy()


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
        hh, hw, hch = hist_rgb.shape
        q_hist = QImage(
            hist_rgb.data, hw, hh, hch * hw, QImage.Format.Format_RGB888
        )
        controls["histogram_label"].setPixmap(QPixmap.fromImage(q_hist))


def open_file():
    global current_image, preview_image
    file_path, _ = QFileDialog.getOpenFileName(
        None, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
    )
    if file_path:
        img = cv2.imread(file_path)
        if img is not None:
            current_image = img
            preview_image = create_preview(current_image)
            reset_controls()


def save_file():
    global current_image, rotation_angle
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
            flip_h=controls["flip_h"].isChecked(),
            flip_v=controls["flip_v"].isChecked(),
            exposure=controls["exposure"].value(),
            brightness=controls["brightness"].value(),
            contrast=controls["contrast"].value() / 100.0,
            temperature=controls["temperature"].value(),
            saturation=controls["saturation"].value() / 100.0,
            r_scale=controls["red"].value() / 100.0,
            g_scale=controls["green"].value() / 100.0,
            b_scale=controls["blue"].value() / 100.0,
            aspect_ratio=controls["aspect_combo"].currentText(),
            vignette=controls["vignette"].value(),
            blur=controls["blur"].value(),
            sharpen=controls["sharpen"].value(),
            grayscale=controls["grayscale"].isChecked(),
        )
        if full_res_output is not None:
            cv2.imwrite(file_path, full_res_output)


def reset_controls():
    global rotation_angle
    rotation_angle = 0
    controls["exposure"].setValue(0)
    controls["brightness"].setValue(0)
    controls["contrast"].setValue(100)
    controls["temperature"].setValue(0)
    controls["saturation"].setValue(100)
    controls["red"].setValue(100)
    controls["green"].setValue(100)
    controls["blue"].setValue(100)
    controls["aspect_combo"].setCurrentIndex(0)
    controls["vignette"].setValue(0)
    controls["blur"].setValue(0)
    controls["sharpen"].setValue(0)
    controls["flip_h"].setChecked(False)
    controls["flip_v"].setChecked(False)
    controls["grayscale"].setChecked(False)
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
    global preview_image, processed_preview, rotation_angle
    if preview_image is None:
        return

    processed_preview = process_image(
        img=preview_image,
        rotation_angle=rotation_angle,
        flip_h=controls["flip_h"].isChecked(),
        flip_v=controls["flip_v"].isChecked(),
        exposure=controls["exposure"].value(),
        brightness=controls["brightness"].value(),
        contrast=controls["contrast"].value() / 100.0,
        temperature=controls["temperature"].value(),
        saturation=controls["saturation"].value() / 100.0,
        r_scale=controls["red"].value() / 100.0,
        g_scale=controls["green"].value() / 100.0,
        b_scale=controls["blue"].value() / 100.0,
        aspect_ratio=controls["aspect_combo"].currentText(),
        vignette=controls["vignette"].value(),
        blur=controls["blur"].value(),
        sharpen=controls["sharpen"].value(),
        grayscale=controls["grayscale"].isChecked(),
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

controls = create_sidebar_ui()

controls["exposure"].valueChanged.connect(apply_adjustments)
controls["brightness"].valueChanged.connect(apply_adjustments)
controls["contrast"].valueChanged.connect(apply_adjustments)
controls["saturation"].valueChanged.connect(apply_adjustments)
controls["aspect_combo"].currentIndexChanged.connect(apply_adjustments)
controls["temperature"].valueChanged.connect(apply_adjustments)
controls["red"].valueChanged.connect(apply_adjustments)
controls["green"].valueChanged.connect(apply_adjustments)
controls["blue"].valueChanged.connect(apply_adjustments)
controls["vignette"].valueChanged.connect(apply_adjustments)
controls["blur"].valueChanged.connect(apply_adjustments)
controls["sharpen"].valueChanged.connect(apply_adjustments)
controls["flip_h"].stateChanged.connect(apply_adjustments)
controls["flip_v"].stateChanged.connect(apply_adjustments)
controls["grayscale"].stateChanged.connect(apply_adjustments)

controls["open_btn"].clicked.connect(open_file)
controls["save_btn"].clicked.connect(save_file)
controls["rotate_btn"].clicked.connect(rotate_image)
controls["compare_btn"].pressed.connect(start_compare)
controls["compare_btn"].released.connect(stop_compare)
controls["reset_btn"].clicked.connect(reset_controls)

main_layout.addWidget(label, stretch=1)
main_layout.addWidget(controls["sidebar"])

window.setLayout(main_layout)
window.show()

sys.exit(app.exec())
