import flet as ft

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


def thumbnail_item(filename, active=False):
    return ft.Container(
        width=85,
        height=55,
        bgcolor=BG_INPUT,
        border_radius=4,
        border=ft.Border.all(2, ACCENT_BLUE if active else BORDER_COLOR),
        padding=4,
        content=ft.Column(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(
                    ft.Icons.IMAGE_OUTLINED,
                    color=ACCENT_BLUE if active else TEXT_MUTED,
                    size=20,
                ),
                ft.Text(
                    filename,
                    size=9,
                    color=TEXT_MAIN if active else TEXT_MUTED,
                    no_wrap=True,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
        ),
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
                        ft.Text("IMG_0042.CR2", color=TEXT_MUTED, size=12),
                    ],
                ),
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.TextButton(
                            "Open",
                            icon=ft.Icons.FOLDER_OPEN,
                            style=ft.ButtonStyle(color=TEXT_MAIN),
                        ),
                        ft.Button(
                            "Save",
                            icon=ft.Icons.FILE_DOWNLOAD,
                            style=ft.ButtonStyle(
                                color="#FFFFFF",
                                bgcolor=ACCENT_BLUE,
                                shape=ft.RoundedRectangleBorder(radius=4),
                            ),
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
                ft.IconButton(
                    icon=ft.Icons.CROP,
                    icon_color=TEXT_MAIN,
                    tooltip="Crop",
                    selected_icon_color=ACCENT_BLUE,
                ),
                ft.IconButton(
                    icon=ft.Icons.COLOR_LENS,
                    icon_color=TEXT_MAIN,
                    tooltip="Color",
                ),
                ft.Divider(color=BORDER_COLOR, height=1),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_IN,
                    icon_color=TEXT_MAIN,
                    tooltip="Zoom In",
                ),
                ft.IconButton(
                    icon=ft.Icons.ZOOM_OUT,
                    icon_color=TEXT_MAIN,
                    tooltip="Zoom Out",
                ),
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
                            ft.Icon(ft.Icons.IMAGE, size=120, color="#222222"),
                            ft.Text(
                                "No image loaded", color=TEXT_MUTED, size=14
                            ),
                        ],
                    ),
                ),
                ft.Container(
                    alignment=ft.Alignment.TOP_LEFT,
                    padding=12,
                    content=ft.Container(
                        bgcolor="#AA000000",
                        padding=ft.Padding.all(6),
                        border_radius=4,
                        content=ft.Text(
                            "ISO 100  f/2.8  1/1000s  85mm",
                            color="#FFFFFF",
                            size=10,
                        ),
                    ),
                ),
            ],
        ),
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
                ft.Row(
                    expand=True,
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=[
                        ft.Container(
                            width=10,
                            height=25,
                            bgcolor="#44FFFFFF",
                            border_radius=2,
                        ),
                        ft.Container(
                            width=10,
                            height=45,
                            bgcolor="#66FFFFFF",
                            border_radius=2,
                        ),
                        ft.Container(
                            width=10,
                            height=70,
                            bgcolor="#88FFFFFF",
                            border_radius=2,
                        ),
                        ft.Container(
                            width=10,
                            height=40,
                            bgcolor="#AAFFFFFF",
                            border_radius=2,
                        ),
                        ft.Container(
                            width=10,
                            height=55,
                            bgcolor="#CCFFFFFF",
                            border_radius=2,
                        ),
                        ft.Container(
                            width=10,
                            height=30,
                            bgcolor="#EEFFFFFF",
                            border_radius=2,
                        ),
                        ft.Container(
                            width=10,
                            height=15,
                            bgcolor="#FFFFFF",
                            border_radius=2,
                        ),
                    ],
                ),
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
            slider_row("Contrast", 0),
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
            slider_row("Temperature", 5500, 2000, 10000),
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
            controls=[
                histogram_card,
                light_group,
                color_group,
            ],
        ),
    )

    bottom_filmstrip = ft.Container(
        height=75,
        bgcolor=BG_HEADER,
        border=ft.Border.only(top=ft.BorderSide(1, BORDER_COLOR)),
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        content=ft.Row(
            scroll=ft.ScrollMode.AUTO,
            spacing=8,
            controls=[
                thumbnail_item("IMG_001.CR2"),
                thumbnail_item("IMG_002.CR2", active=True),
                thumbnail_item("IMG_003.CR2"),
                thumbnail_item("IMG_004.CR2"),
                thumbnail_item("IMG_005.CR2"),
                thumbnail_item("IMG_006.CR2"),
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
        controls=[center_area, bottom_filmstrip],
    )

    page.add(
        ft.Column(
            expand=True,
            spacing=0,
            controls=[header_bar, workspace, status_bar],
        )
    )


ft.run(main)