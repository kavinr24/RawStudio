import asyncio
import base64
import os
import sys
import warnings

import cv2
import flet as ft
import numpy as np

from processor import (
    extract_edge_mask,
    get_histogram_image,
    process_image,
    run_extra_effects_pipeline,
)

if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

BG_DARK = "#121212"
BG_PANEL = "#1E1E1E"
BG_HEADER = "#252526"
BG_INPUT = "#2A2A2A"
ACCENT_BLUE = "#007ACC"
TEXT_MAIN = "#CCCCCC"
TEXT_MUTED = "#888888"
BORDER_COLOR = "#333333"

TRANSPARENT_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

controls = {}
original = None
preview = None
_page = None
_picker = None
canvas_image = None
canvas_viewer = None
placeholder = None
histogram_image = None
rotation_angle = 0
_canvas_w = 0.0
_canvas_h = 0.0
_render_busy = False
_render_pending = False

Toggles = ("Flip H", "Flip V", "Grayscale", "Auto Select")

RESET_VALUES = {
    "Exposure": 0,
    "Brightness": 0,
    "Contrast": 100,
    "Highlights": 0,
    "Shadows": 0,
    "Temperature": 0,
    "Tint": 0,
    "Saturation": 100,
    "Shadow Tint": 0,
    "Highlight Tint": 0,
    "Red Scale": 100,
    "Green Scale": 100,
    "Blue Scale": 100,
    "Clarity": 0,
    "Vignette": 0,
    "Blur": 0,
    "Sharpen": 0,
}


def img_to_data_uri(img, png=False):
    if img is None:
        return ""
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    if png:
        ok, buf = cv2.imencode(".png", img)
    else:
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/" + ("png" if png else "jpeg") + ";base64," + base64.b64encode(buf).decode("ascii")


def create_preview(img, max_dim=900):
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        return cv2.resize(
            img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )
    return img.copy()


def current_params(img):
    return dict(
        img=img,
        rotation_angle=rotation_angle,
        flip_h=controls["Flip H"].value,
        flip_v=controls["Flip V"].value,
        exposure=controls["Exposure"].value,
        brightness=controls["Brightness"].value,
        contrast=controls["Contrast"].value / 100.0,
        temperature=controls["Temperature"].value,
        shadows=controls["Shadows"].value,
        saturation=controls["Saturation"].value / 100.0,
        r_scale=controls["Red Scale"].value / 100.0,
        g_scale=controls["Green Scale"].value / 100.0,
        b_scale=controls["Blue Scale"].value / 100.0,
        vignette=controls["Vignette"].value,
        blur=int(controls["Blur"].value),
        sharpen=controls["Sharpen"].value,
        grayscale=controls["Grayscale"].value,
    )


def extra_effects(img):
    return run_extra_effects_pipeline(
        img,
        highlights=controls["Highlights"].value,
        clarity=controls["Clarity"].value,
        tint=controls["Tint"].value,
        shadow_tint=controls["Shadow Tint"].value,
        highlight_tint=controls["Highlight Tint"].value,
    )


def apply_auto_select(processed):
    if processed is None or not controls["Auto Select"].value:
        return processed
    if processed.ndim == 2:
        processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
    mask = extract_edge_mask(processed)
    if mask is None:
        return processed
    m = cv2.resize(mask, (processed.shape[1], processed.shape[0]))
    m3 = np.repeat(m[:, :, np.newaxis], 3, axis=2)
    dimmed = processed.astype(np.float32) * 0.35
    return np.clip(
        processed.astype(np.float32) * m3 + dimmed * (1.0 - m3), 0, 255
    ).astype(np.uint8)


def _compute_processed(img):
    processed = process_image(**current_params(img))
    if processed.ndim == 2:
        processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
    processed = extra_effects(processed)
    return apply_auto_select(processed)


async def apply_adjustments():
    global canvas_image, placeholder, histogram_image, _render_busy, _render_pending
    if original is None or preview is None or canvas_image is None:
        return
    if _render_busy:
        _render_pending = True
        return
    _render_busy = True
    _render_pending = False
    try:
        while True:
            try:
                processed = await asyncio.to_thread(_compute_processed, preview)
                canvas_image.src = await asyncio.to_thread(img_to_data_uri, processed)
                canvas_image.visible = True
                placeholder.visible = False
                histogram_image.src = await asyncio.to_thread(
                    img_to_data_uri, get_histogram_image(processed), True
                )
            except Exception as ex:
                print(f"[RawStudio] render error: {ex!r}")
            finally:
                if _page is not None:
                    _page.update()
            if not _render_pending:
                break
            _render_pending = False
    finally:
        _render_busy = False


async def _on_slider(e, value_text):
    value_text.value = f"{e.control.value:.0f}"
    if _page is not None:
        _page.update(value_text)


async def _on_slider_end(e, value_text):
    value_text.value = f"{e.control.value:.0f}"
    await apply_adjustments()


def _make_slider_change(value_text):
    async def handler(e):
        await _on_slider(e, value_text)

    return handler


def _make_slider_change_end(value_text):
    async def handler(e):
        await _on_slider_end(e, value_text)

    return handler


def slider_row(label, value, lo=-100, hi=100):
    value_text = ft.Text(f"{value:.0f}", color=TEXT_MUTED, size=11)
    slider = ft.Slider(
        min=lo,
        max=hi,
        value=value,
        active_color=ACCENT_BLUE,
        inactive_color=BG_INPUT,
        on_change=_make_slider_change(value_text),
        on_change_end=_make_slider_change_end(value_text),
    )
    controls[label] = slider
    return ft.Column(
        spacing=2,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, color=TEXT_MAIN, size=11),
                    value_text,
                ],
            ),
            slider,
        ],
    )


def toggle_row(label):
    async def on_toggle(e):
        await apply_adjustments()

    switch = ft.Switch(
        label=label,
        value=False,
        active_color=ACCENT_BLUE,
        label_text_style=ft.TextStyle(color=TEXT_MAIN, size=11),
        tooltip="Auto select the main subject"
        if label == "Auto Select"
        else None,
        on_change=on_toggle,
    )
    controls[label] = switch
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        content=switch,
    )


def _fit_image_box():
    global canvas_image, canvas_viewer
    img = preview if preview is not None else original
    if img is None or canvas_image is None or _canvas_w <= 0 or _canvas_h <= 0:
        return
    h, w = img.shape[:2]
    s = min(_canvas_w / w, _canvas_h / h)
    iw = max(1, int(round(w * s)))
    ih = max(1, int(round(h * s)))
    m = max((_canvas_w - iw) / 2, (_canvas_h - ih) / 2) * 1.1
    canvas_image.width = iw
    canvas_image.height = ih
    to_update = [canvas_image]
    if canvas_viewer is not None:
        canvas_viewer.boundary_margin = ft.Margin.all(m)
        to_update.append(canvas_viewer)
    if _page is not None:
        _page.update(*to_update)


async def _on_canvas_size(e):
    global _canvas_w, _canvas_h
    _canvas_w = e.width or 0
    _canvas_h = e.height or 0
    if canvas_viewer is not None:
        await canvas_viewer.reset()
    _fit_image_box()


async def zoom_in_clicked(e):
    if canvas_viewer is not None:
        await canvas_viewer.zoom(1.25)


async def zoom_out_clicked(e):
    if canvas_viewer is not None:
        await canvas_viewer.zoom(0.8)


async def rotate_clicked(e):
    global rotation_angle
    rotation_angle = (rotation_angle + 90) % 360
    if canvas_viewer is not None:
        await canvas_viewer.reset()
    _fit_image_box()
    await apply_adjustments()


async def reset_clicked(e):
    global rotation_angle
    rotation_angle = 0
    if canvas_viewer is not None:
        await canvas_viewer.reset()
    for label, value in RESET_VALUES.items():
        controls[label].value = value
    for label in Toggles:
        controls[label].value = False
    if _page is not None:
        _page.update()
    await apply_adjustments()


async def open_clicked(e):
    global original, preview
    files = await _picker.pick_files(
        dialog_title="Open Image",
        file_type=ft.FilePickerFileType.IMAGE,
        with_data=True,
    )
    if files and files[0].bytes:
        arr = np.frombuffer(files[0].bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            original = img
            preview = create_preview(original)
            _fit_image_box()
            await reset_clicked(None)


async def save_clicked(e):
    if original is None:
        return
    path = await _picker.save_file(
        dialog_title="Save Image",
        file_name="output.png",
        allowed_extensions=["png", "jpg", "jpeg", "bmp"],
    )
    if path:
        processed = await asyncio.to_thread(_compute_processed, original)
        cv2.imwrite(path, processed)


def main(page: ft.Page):
    global _page, _picker, canvas_image, canvas_viewer, placeholder, histogram_image
    _page = page

    page.title = "RawStudio"
    page.padding = 0
    page.spacing = 0
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 1024
    page.window.min_height = 720

    page.bgcolor = BG_DARK

    file_picker = ft.FilePicker()
    _picker = file_picker

    header_bar = ft.Container(
        height=40,
        bgcolor=BG_HEADER,
        padding=ft.Padding.symmetric(horizontal=12),
        border=ft.Border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(
                            ft.Icons.CAMERA_OUTLINED,
                            size=18,
                            color=ACCENT_BLUE,
                        ),
                        ft.Text(
                            "RawStudio",
                            weight=ft.FontWeight.BOLD,
                            color="#FFFFFF",
                            size=14,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.TextButton(
                            "Open",
                            icon=ft.Icons.FOLDER_OPEN,
                            style=ft.ButtonStyle(color=TEXT_MAIN),
                            on_click=open_clicked,
                        ),
                        ft.Button(
                            "Save",
                            icon=ft.Icons.FILE_DOWNLOAD,
                            style=ft.ButtonStyle(
                                color="#FFFFFF",
                                bgcolor=ACCENT_BLUE,
                                shape=ft.RoundedRectangleBorder(radius=4),
                            ),
                            on_click=save_clicked,
                        ),
                    ],
                ),
            ],
        ),
    )

    left_toolbar = ft.Container(
        width=44,
        bgcolor=BG_PANEL,
        border=ft.Border.only(right=ft.BorderSide(1, BORDER_COLOR)),
        padding=ft.Padding.symmetric(vertical=8, horizontal=0),
        content=ft.Column(
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            controls=[
                ft.Divider(color=BORDER_COLOR, height=1),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_IN,
                    icon_color=TEXT_MAIN,
                    tooltip="Zoom In",
                    on_click=zoom_in_clicked,
                ),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_OUT,
                    icon_color=TEXT_MAIN,
                    tooltip="Zoom Out",
                    on_click=zoom_out_clicked,
                ),
            ],
        ),
    )

    placeholder = ft.Container(
        alignment=ft.Alignment.CENTER,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Icon(ft.Icons.IMAGE, size=120, color="#222222"),
                ft.Text("No image loaded", color=TEXT_MUTED, size=14),
            ],
        ),
    )

    canvas_image = ft.Image(
        src=TRANSPARENT_PNG,
        fit=ft.BoxFit.CONTAIN,
    )

    canvas_viewer = ft.InteractiveViewer(
        expand=True,
        min_scale=1.0,
        max_scale=8.0,
        constrained=False,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=canvas_image,
    )

    canvas_container = ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        on_size_change=_on_canvas_size,
        content=ft.Stack(
            expand=True,
            controls=[
                placeholder,
                canvas_viewer,
            ],
        ),
    )

    histogram_image = ft.Image(
        src=TRANSPARENT_PNG,
        fit=ft.BoxFit.CONTAIN,
        expand=True,
    )

    histogram_card = ft.Container(
        height=100,
        bgcolor=BG_INPUT,
        border_radius=4,
        padding=8,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("HISTOGRAM", size=9, color=TEXT_MUTED),
                        ft.Text("RGB", size=9, color=TEXT_MUTED),
                    ],
                ),
                histogram_image,
            ],
        ),
    )

    light_group = ft.ExpansionTile(
        title=ft.Text(
            "Light", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=True,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row("Exposure", 0),
            slider_row("Brightness", 0),
            slider_row("Contrast", 100, 0, 200),
            slider_row("Highlights", 0),
            slider_row("Shadows", 0),
        ],
    )

    color_group = ft.ExpansionTile(
        title=ft.Text(
            "Color", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row("Temperature", 0, -100, 100),
            slider_row("Tint", 0, -100, 100),
            slider_row("Saturation", 100, 0, 200),
            slider_row("Shadow Tint", 0, -100, 100),
            slider_row("Highlight Tint", 0, -100, 100),
        ],
    )

    channel_group = ft.ExpansionTile(
        title=ft.Text(
            "Channels", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row("Red Scale", 100, 0, 200),
            slider_row("Green Scale", 100, 0, 200),
            slider_row("Blue Scale", 100, 0, 200),
        ],
    )

    effects_group = ft.ExpansionTile(
        title=ft.Text(
            "Effects", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row("Clarity", 0, -100, 100),
            slider_row("Vignette", 0, 0, 100),
            slider_row("Blur", 0, 0, 20),
            slider_row("Sharpen", 0, 0, 100),
        ],
    )

    transform_group = ft.ExpansionTile(
        title=ft.Text(
            "Transform", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            toggle_row("Flip H"),
            toggle_row("Flip V"),
            toggle_row("Grayscale"),
            toggle_row("Auto Select"),
        ],
    )

    action_row = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
        controls=[
            ft.TextButton(
                "Rotate",
                icon=ft.Icons.ROTATE_RIGHT,
                style=ft.ButtonStyle(color=TEXT_MAIN),
                on_click=rotate_clicked,
            ),
            ft.Button(
                "Reset",
                icon=ft.Icons.RESTART_ALT,
                style=ft.ButtonStyle(
                    color="#FFFFFF",
                    bgcolor="#8B0000",
                    shape=ft.RoundedRectangleBorder(radius=4),
                ),
                on_click=reset_clicked,
            ),
        ],
    )

    right_panel = ft.Container(
        width=320,
        bgcolor=BG_PANEL,
        border=ft.Border.only(left=ft.BorderSide(1, BORDER_COLOR)),
        padding=10,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[
                histogram_card,
                light_group,
                color_group,
                channel_group,
                effects_group,
                transform_group,
                action_row,
            ],
        ),
    )

    status_bar = ft.Container(
        height=20,
        bgcolor=BG_DARK,
        padding=ft.Padding.symmetric(horizontal=12),
        border=ft.Border.only(top=ft.BorderSide(1, BORDER_COLOR)),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("Ready", size=10, color=TEXT_MUTED),
                ft.Text("6000 x 4000", size=10, color=TEXT_MUTED),
            ],
        ),
    )

    center_area = ft.Row(
        expand=True,
        spacing=0,
        controls=[left_toolbar, canvas_container, right_panel],
    )

    workspace = ft.Column(
        expand=True,
        spacing=0,
        controls=[center_area],
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[header_bar, workspace, status_bar],
        )
    )


app = ft.run(main, export_asgi_app=True)

if __name__ == "__main__":
    ft.run(main)