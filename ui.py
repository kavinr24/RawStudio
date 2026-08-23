from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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


def create_sidebar_ui():
    histogram_label = QLabel()
    histogram_label.setFixedSize(256, 120)
    histogram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    histogram_label.setStyleSheet(
        "background-color: #111111; border: 1px solid #333333;"
    )

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

    aspect_combo = QComboBox()
    aspect_combo.addItems(["Original", "1:1", "4:3", "16:9"])

    basic_layout.addRow(QLabel("Exposure:"), exposure_slider)
    basic_layout.addRow(QLabel("Brightness:"), brightness_slider)
    basic_layout.addRow(QLabel("Contrast:"), contrast_slider)
    basic_layout.addRow(QLabel("Saturation:"), saturation_slider)
    basic_layout.addRow(QLabel("Crop Ratio:"), aspect_combo)
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

    vignette_slider = QSlider(Qt.Orientation.Horizontal)
    vignette_slider.setRange(0, 100)
    vignette_slider.setValue(0)

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

    rotate_button = QPushButton("Rotate 90\N{DEGREE SIGN}")
    rotate_button.setStyleSheet(
        "background-color: #333333; color: #ffffff; padding: 8px;"
    )

    effects_layout.addRow(QLabel("Vignette:"), vignette_slider)
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
    sidebar_layout.addWidget(histogram_label, alignment=Qt.AlignmentFlag.AlignCenter)
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
        "aspect_combo": aspect_combo,
        "temperature": temperature_slider,
        "red": red_slider,
        "green": green_slider,
        "blue": blue_slider,
        "vignette": vignette_slider,
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
