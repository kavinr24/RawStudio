import flet as ft

icons = ft.icons.Icons

BG_DARK = "#121212"
BG_PANEL = "#1E1E1E"
BG_HEADER = "#252526"
BG_INPUT = "#2A2A2A"
ACCENT_BLUE = "#007ACC"
TEXT_MAIN = "#CCCCCC"
TEXT_MUTED = "#888888"
BORDER_COLOR = "#333333"


def slider_row(label, value, lo=-100, hi=100):
    return ft.Column(
        spacing=2,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, color=TEXT_MAIN, size=11),
                    ft.Text(f"{value:.0f}", color=TEXT_MUTED, size=11),
                ],
            ),
            ft.Slider(
                min=lo,
                max=hi,
                value=value,
                active_color=ACCENT_BLUE,
                inactive_color=BG_INPUT,
            ),
        ],
    )


def main(page: ft.Page):
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
                    controls=[
                        ft.Icon(icons.CAMERA_OUTLINED, size=18, color=ACCENT_BLUE),
                        ft.Text("RawStudio", weight=ft.FontWeight.BOLD, color="#FFFFFF", size=14),
                        ft.Text("IMG", color=TEXT_MUTED, size=12),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.TextButton("Open", icon=icons.FOLDER_OPEN, style=ft.ButtonStyle(color=TEXT_MAIN)),
                        ft.Button("Save", icon=icons.FILE_DOWNLOAD, style=ft.ButtonStyle(color="#FFFFFF", bgcolor=ACCENT_BLUE, shape=ft.RoundedRectangleBorder(radius=4))),
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
                ft.IconButton(icon=icons.CROP, icon_color=TEXT_MAIN, tooltip="Crop", selected_icon_color=ACCENT_BLUE),
                ft.IconButton(icon=icons.COLOR_LENS, icon_color=TEXT_MAIN, tooltip="Color"),
                ft.IconButton(icon=icons.AUTO_FIX_HIGH, icon_color=TEXT_MAIN, tooltip="Auto Tune"),
                ft.Divider(color=BORDER_COLOR, height=1),
                ft.IconButton(icon=icons.ZOOM_IN, icon_color=TEXT_MAIN, tooltip="Zoom In"),
                ft.IconButton(icon=icons.ZOOM_OUT, icon_color=TEXT_MAIN, tooltip="Zoom Out"),
            ],
        ),
    )

    canvas_container = ft.Container(
        expand=True,
        bgcolor=BG_DARK,
        alignment=ft.Alignment.CENTER,
        content=ft.Stack(
            controls=[
                ft.Container(
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Icon(icons.IMAGE, size=120, color="#222222"),
                            ft.Text("No image loaded", color=TEXT_MUTED, size=14),
                        ],
                    ),
                ),
            ],
        ),
    )

    light_group = ft.ExpansionTile(
        title=ft.Text("Light", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
        expanded=True,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row("Exposure", 0),
            slider_row("Contrast", 0),
            slider_row("Highlights", 0),
            slider_row("Shadows", 0),
        ],
    )

    color_group = ft.ExpansionTile(
        title=ft.Text("Color", size=12, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
        expanded=False,
        controls_padding=ft.Padding.symmetric(horizontal=10),
        controls=[
            slider_row("Temperature", 5500, 2000, 10000),
            slider_row("Tint", 0),
            slider_row("Saturation", 0),
        ],
    )

    right_panel = ft.Container(
        width=300,
        bgcolor=BG_PANEL,
        border=ft.Border.only(left=ft.BorderSide(1, BORDER_COLOR)),
        padding=10,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[light_group, color_group],
        ),
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[
                header_bar,
                ft.Row(
                    expand=True,
                    spacing=0,
                    controls=[left_toolbar, canvas_container, right_panel],
                ),
            ],
        )
    )


ft.run(main)
