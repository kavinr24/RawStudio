import asyncio
import base64
import logging
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

_log = logging.getLogger("rawstudio")

MAX_UPLOAD_BYTES = 60 * 1024 * 1024
MAX_PIXELS = 40_000_000

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

PREVIEW_MAX_DIM = 700 if os.environ.get("RENDER") else 900

# Process-wide render limiter so a handful of concurrent sessions can't
# saturate the server CPU with simultaneous photo processing.
_render_slots = asyncio.Semaphore(2)


def img_to_data_uri(img, png=False):
    if img is None:
        return ""
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if png:
        ok, buf = cv2.imencode(".png", img)
    else:
        ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/" + ("png" if png else "jpeg") + ";base64," + base64.b64encode(buf).decode("ascii")


def notify(st, message):
    try:
        st.page.show_dialog(
            ft.SnackBar(
                content=message,
                duration=4000,
            )
        )
    except Exception as ex:
        _log.error("Failed to show notification %r: %r", message, ex)


def create_preview(img, max_dim=PREVIEW_MAX_DIM):
    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        return cv2.resize(
            img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
        )
    return img.copy()


class EditorState:
    def __init__(self, page):
        self.page = page
        self.picker = ft.FilePicker()
        self.controls = {}
        self.original = None
        self.preview = None
        self.canvas_image = None
        self.canvas_viewer = None
        self.placeholder = None
        self.histogram_image = None
        self.rotation_angle = 0
        self.canvas_w = 0.0
        self.canvas_h = 0.0
        self.render_busy = False
        self.render_pending = False

    def current_params(self, img):
        return dict(
            img=img,
            rotation_angle=self.rotation_angle,
            flip_h=self.controls["Flip H"].value,
            flip_v=self.controls["Flip V"].value,
            exposure=self.controls["Exposure"].value,
            brightness=self.controls["Brightness"].value,
            contrast=self.controls["Contrast"].value / 100.0,
            temperature=self.controls["Temperature"].value,
            shadows=self.controls["Shadows"].value,
            saturation=self.controls["Saturation"].value / 100.0,
            r_scale=self.controls["Red Scale"].value / 100.0,
            g_scale=self.controls["Green Scale"].value / 100.0,
            b_scale=self.controls["Blue Scale"].value / 100.0,
            vignette=self.controls["Vignette"].value,
            blur=int(self.controls["Blur"].value),
            sharpen=self.controls["Sharpen"].value,
            grayscale=self.controls["Grayscale"].value,
        )

    def extra_effects(self, img):
        return run_extra_effects_pipeline(
            img,
            highlights=self.controls["Highlights"].value,
            clarity=self.controls["Clarity"].value,
            tint=self.controls["Tint"].value,
            shadow_tint=self.controls["Shadow Tint"].value,
            highlight_tint=self.controls["Highlight Tint"].value,
        )

    def apply_auto_select(self, processed):
        if processed is None or not self.controls["Auto Select"].value:
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

    def compute_processed(self, img):
        processed = process_image(**self.current_params(img))
        if processed.ndim == 2:
            processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        processed = self.extra_effects(processed)
        return self.apply_auto_select(processed)

    async def _render_with_slot(self, img):
        async with _render_slots:
            return await asyncio.to_thread(self.compute_processed, img)

    async def apply_adjustments(self):
        if self.original is None or self.preview is None or self.canvas_image is None:
            return
        if self.render_busy:
            self.render_pending = True
            return
        self.render_busy = True
        self.render_pending = False
        try:
            while True:
                try:
                    processed = await self._render_with_slot(self.preview)
                    self.canvas_image.src = await asyncio.to_thread(
                        img_to_data_uri, processed
                    )
                    self.canvas_image.visible = True
                    self.placeholder.visible = False
                    self.histogram_image.src = await asyncio.to_thread(
                        img_to_data_uri, get_histogram_image(processed), True
                    )
                except Exception:
                    _log.exception("Render failed")
                    notify(self, "Render error, please retry.")
                finally:
                    self.page.update()
                if not self.render_pending:
                    break
                self.render_pending = False
        finally:
            self.render_busy = False

    def fit_image_box(self):
        img = self.preview if self.preview is not None else self.original
        if img is None or self.canvas_image is None or self.canvas_w <= 0 or self.canvas_h <= 0:
            return
        h, w = img.shape[:2]
        s = min(self.canvas_w / w, self.canvas_h / h)
        iw = max(1, int(round(w * s)))
        ih = max(1, int(round(h * s)))
        m = max((self.canvas_w - iw) / 2, (self.canvas_h - ih) / 2) * 1.1
        self.canvas_image.width = iw
        self.canvas_image.height = ih
        to_update = [self.canvas_image]
        if self.canvas_viewer is not None:
            self.canvas_viewer.boundary_margin = ft.Margin.all(m)
            to_update.append(self.canvas_viewer)
        self.page.update(*to_update)


async def _on_slider(e, value_text):
    st = e.page.data
    value_text.value = f"{e.control.value:.0f}"
    st.page.update(value_text)


async def _on_slider_end(e, value_text):
    value_text.value = f"{e.control.value:.0f}"
    await e.page.data.apply_adjustments()


def _make_slider_change(value_text):
    async def handler(e):
        await _on_slider(e, value_text)

    return handler


def _make_slider_change_end(value_text):
    async def handler(e):
        await _on_slider_end(e, value_text)

    return handler


def slider_row(st, label, value, lo=-100, hi=100):
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
    st.controls[label] = slider
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


def toggle_row(st, label):
    async def on_toggle(e):
        await e.page.data.apply_adjustments()

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
    st.controls[label] = switch
    return ft.Container(
        padding=ft.Padding.symmetric(horizontal=10, vertical=0),
        content=switch,
    )


async def _on_canvas_size(e):
    st = e.page.data
    st.canvas_w = e.width or 0
    st.canvas_h = e.height or 0
    if st.canvas_viewer is not None:
        await st.canvas_viewer.reset()
    st.fit_image_box()


async def zoom_in_clicked(e):
    st = e.page.data
    if st.canvas_viewer is not None:
        await st.canvas_viewer.zoom(1.25)


async def zoom_out_clicked(e):
    st = e.page.data
    if st.canvas_viewer is not None:
        await st.canvas_viewer.zoom(0.8)


async def rotate_clicked(e):
    st = e.page.data
    st.rotation_angle = (st.rotation_angle + 90) % 360
    if st.canvas_viewer is not None:
        await st.canvas_viewer.reset()
    st.fit_image_box()
    await st.apply_adjustments()


async def reset_clicked(e):
    st = e.page.data
    st.rotation_angle = 0
    if st.canvas_viewer is not None:
        await st.canvas_viewer.reset()
    for label, value in RESET_VALUES.items():
        st.controls[label].value = value
    for label in Toggles:
        st.controls[label].value = False
    st.page.update()
    await st.apply_adjustments()


async def open_clicked(e):
    st = e.page.data
    files = await st.picker.pick_files(
        dialog_title="Open Image",
        file_type=ft.FilePickerFileType.IMAGE,
        with_data=True,
    )
    if not files or not files[0].bytes:
        return
    if len(files[0].bytes) > MAX_UPLOAD_BYTES:
        _log.warning("Upload too large (%d bytes), skipped", len(files[0].bytes))
        notify(st, "File is too large (max 60 MB).")
        return
    try:
        img = cv2.imdecode(
            np.frombuffer(files[0].bytes, np.uint8), cv2.IMREAD_COLOR
        )
    except cv2.error:
        _log.exception("Image decode failed")
        notify(st, "Could not read that image.")
        return
    if img is None:
        notify(st, "Could not read that image.")
        return
    if img.shape[0] * img.shape[1] > MAX_PIXELS:
        _log.warning(
            "Image too large (%d x %d), skipped", img.shape[1], img.shape[0]
        )
        notify(st, "Image is too large (max 40 megapixels).")
        return
    st.original = img
    st.preview = create_preview(st.original)
    st.fit_image_box()
    await reset_clicked(e)


async def save_clicked(e):
    st = e.page.data
    if st.original is None:
        return
    try:
        processed = await st._render_with_slot(st.original)
        ok, buf = cv2.imencode(".png", processed)
        if not ok:
            _log.error("Could not encode image as PNG")
            notify(st, "Could not encode image.")
            return
        result = await st.picker.save_file(
            dialog_title="Save Image",
            file_name="output.png",
            allowed_extensions=["png", "jpg", "jpeg", "bmp"],
            src_bytes=buf.tobytes(),
        )
        if result and result.path:
            try:
                cv2.imwrite(result.path, processed)
            except Exception:
                _log.exception("Could not write file to %s", result.path)
                notify(st, "Could not save the file.")
    except Exception:
        _log.exception("Save failed")
        notify(st, "Save failed.")


def main(page: ft.Page):
    st = EditorState(page)
    page.data = st

    page.title = "RawStudio"
    page.padding = 0
    page.spacing = 0
    page.window.width = 1280
    page.window.height = 800
    page.window.min_width = 1024
    page.window.min_height = 720

    page.bgcolor = BG_DARK

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

    st.placeholder = placeholder
    st.canvas_image = canvas_image
    st.canvas_viewer = canvas_viewer
    st.histogram_image = histogram_image

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
            slider_row(st, "Exposure", 0),
            slider_row(st, "Brightness", 0),
            slider_row(st, "Contrast", 100, 0, 200),
            slider_row(st, "Highlights", 0),
            slider_row(st, "Shadows", 0),
        ],
    )

    color_group = ft.ExpansionTile(
        title=ft.Text(
            "Color", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row(st, "Temperature", 0, -100, 100),
            slider_row(st, "Tint", 0, -100, 100),
            slider_row(st, "Saturation", 100, 0, 200),
            slider_row(st, "Shadow Tint", 0, -100, 100),
            slider_row(st, "Highlight Tint", 0, -100, 100),
        ],
    )

    channel_group = ft.ExpansionTile(
        title=ft.Text(
            "Channels", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row(st, "Red Scale", 100, 0, 200),
            slider_row(st, "Green Scale", 100, 0, 200),
            slider_row(st, "Blue Scale", 100, 0, 200),
        ],
    )

    effects_group = ft.ExpansionTile(
        title=ft.Text(
            "Effects", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row(st, "Clarity", 0, -100, 100),
            slider_row(st, "Vignette", 0, 0, 100),
            slider_row(st, "Blur", 0, 0, 20),
            slider_row(st, "Sharpen", 0, 0, 100),
        ],
    )

    transform_group = ft.ExpansionTile(
        title=ft.Text(
            "Transform", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN
        ),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            toggle_row(st, "Flip H"),
            toggle_row(st, "Flip V"),
            toggle_row(st, "Grayscale"),
            toggle_row(st, "Auto Select"),
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
            alignment=ft.MainAxisAlignment.END,
            controls=[
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