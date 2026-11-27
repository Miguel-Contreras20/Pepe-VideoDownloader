import json
import os
import threading
import flet as ft
from downloader import descargar_media

CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".pepe_downloader_config.json")
CARPETA_DEFAULT = os.path.join(os.path.expanduser("~"), "Downloads")
VERSION= "0.3.1"


def cargar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"carpeta_descargas": CARPETA_DEFAULT}


def guardar_config(data: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def detectar_plataforma(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    if "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "instagram"
    return "desconocida"


def main(page: ft.Page):
    page.title = "Pepe Video Downloader"
    page.window.width = 620
    page.window.height = 760
    page.window.resizable = False
    page.window.maximizable = False
    page.padding = 24
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.ico")
    if os.path.exists(icon_path):
        page.window.icon = icon_path

    config = cargar_config()
    carpeta_actual = config.get("carpeta_descargas", CARPETA_DEFAULT)
    if not os.path.exists(carpeta_actual):
        carpeta_actual = CARPETA_DEFAULT

    plataforma_actual = "desconocida"

    # --- Controles ---
    badge_plataforma = ft.Container(
        content=ft.Text("Esperando enlace", size=12, weight=ft.FontWeight.W_500),
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=12,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
    )

    url_input = ft.TextField(
        label="Enlace de YouTube o Instagram",
        hint_text="Pega aquí la URL...",
        expand=True,
        autofocus=True,
    )

    modo_selector = ft.RadioGroup(
        value="video",
        content=ft.Row(
            [
                ft.Radio(value="video", label="Video"),
                ft.Radio(value="audio", label="Solo Audio"),
            ],
            spacing=20,
        ),
    )

    calidad_dropdown = ft.Dropdown(
        label="Calidad",
        value="best",
        expand=True,
        options=[
            ft.dropdown.Option("best", "Mejor disponible"),
            ft.dropdown.Option("1080", "1080p (Full HD)"),
            ft.dropdown.Option("720", "720p (HD)"),
            ft.dropdown.Option("480", "480p (SD)"),
        ],
    )

    formato_dropdown = ft.Dropdown(
        label="Formato",
        value="mp4",
        width=200,
        options=[
            ft.dropdown.Option("mp4", "MP4 (Universal)"),
            ft.dropdown.Option("mkv", "MKV"),
            ft.dropdown.Option("webm", "WEBM"),
        ],
    )

    chk_subtitulos = ft.Checkbox(label="Descargar subtítulos (ES/EN)", value=False)
    chk_playlist = ft.Checkbox(label="Permitir lista de reproducción completa", value=False)
    nota_plataforma = ft.Text("", size=12, color=ft.Colors.ORANGE_400, visible=False)

    texto_carpeta = ft.Text(
        carpeta_actual,
        size=12,
        expand=True,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    # --- Panel de progreso siempre visible ---
    icono_estado = ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=ft.Colors.BLUE_400)
    estado_texto = ft.Text("Listo para descargar.", size=13, weight=ft.FontWeight.W_500, expand=True)
    barra_progreso = ft.ProgressBar(value=0, height=10, border_radius=5, color=ft.Colors.BLUE_400)

    # --- Lógica de interfaz ---
    def actualizar_opciones_ui():
        es_audio = modo_selector.value == "audio"
        es_instagram = plataforma_actual == "instagram"

        if es_audio:
            formato_dropdown.options = [
                ft.dropdown.Option("mp3", "MP3 (Estándar)"),
                ft.dropdown.Option("m4a", "M4A (Ligero)"),
                ft.dropdown.Option("opus", "OPUS (WhatsApp)"),
                ft.dropdown.Option("wav", "WAV (Sin pérdida)"),
            ]
            if formato_dropdown.value not in ("mp3", "m4a", "opus", "wav"):
                formato_dropdown.value = "mp3"

            calidad_dropdown.options = [
                ft.dropdown.Option("320", "320 kbps (Alta)"),
                ft.dropdown.Option("192", "192 kbps (Estándar)"),
                ft.dropdown.Option("128", "128 kbps (Ligera)"),
            ]
            if calidad_dropdown.value not in ("320", "192", "128"):
                calidad_dropdown.value = "192"

            # WAV no usa compresión de kbps
            calidad_dropdown.disabled = formato_dropdown.value == "wav"
            chk_subtitulos.disabled = True
            chk_subtitulos.value = False
        else:
            formato_dropdown.options = [
                ft.dropdown.Option("mp4", "MP4 (Universal)"),
                ft.dropdown.Option("mkv", "MKV"),
                ft.dropdown.Option("webm", "WEBM"),
            ]
            if formato_dropdown.value not in ("mp4", "mkv", "webm"):
                formato_dropdown.value = "mp4"

            calidad_dropdown.options = [
                ft.dropdown.Option("best", "Mejor disponible"),
                ft.dropdown.Option("1080", "1080p (Full HD)"),
                ft.dropdown.Option("720", "720p (HD)"),
                ft.dropdown.Option("480", "480p (SD)"),
            ]
            if calidad_dropdown.value not in ("best", "1080", "720", "480"):
                calidad_dropdown.value = "best"

            if es_instagram:
                calidad_dropdown.value = "best"
                calidad_dropdown.disabled = True
                chk_subtitulos.disabled = True
                chk_subtitulos.value = False
            else:
                calidad_dropdown.disabled = False
                chk_subtitulos.disabled = False

        if es_instagram:
            chk_playlist.disabled = True
            chk_playlist.value = False
            nota_plataforma.value = "Instagram detectado: resolución manual, subtítulos y playlists desactivados."
            nota_plataforma.visible = True
        else:
            chk_playlist.disabled = False
            nota_plataforma.visible = False

        page.update()

    def al_cambiar_url(e):
        nonlocal plataforma_actual
        plataforma_actual = detectar_plataforma(url_input.value.strip())

        if plataforma_actual == "youtube":
            badge_plataforma.content.value = "YouTube"
            badge_plataforma.bgcolor = ft.Colors.RED_900
        elif plataforma_actual == "instagram":
            badge_plataforma.content.value = "Instagram"
            badge_plataforma.bgcolor = ft.Colors.PURPLE_900
        else:
            badge_plataforma.content.value = "Esperando enlace"
            badge_plataforma.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST

        actualizar_opciones_ui()

    def limpiar_url(e):
        url_input.value = ""
        al_cambiar_url(None)

    async def cambiar_carpeta(e):
        nonlocal carpeta_actual
        ruta = await ft.FilePicker().get_directory_path(dialog_title="Elegir carpeta de descargas")
        if ruta:
            carpeta_actual = ruta
            texto_carpeta.value = carpeta_actual
            config["carpeta_descargas"] = carpeta_actual
            guardar_config(config)
            page.update()

    def abrir_carpeta(e):
        if os.path.exists(carpeta_actual):
            os.startfile(carpeta_actual)

    def actualizar_progreso(valor):
        barra_progreso.value = valor
        page.update()

    def actualizar_estado(mensaje: str, tipo: str = "info"):
        estado_texto.value = mensaje
        if tipo == "cargando":
            icono_estado.name = ft.Icons.DOWNLOADING
            icono_estado.color = ft.Colors.BLUE_400
            barra_progreso.color = ft.Colors.BLUE_400
        elif tipo == "exito":
            icono_estado.name = ft.Icons.CHECK_CIRCLE
            icono_estado.color = ft.Colors.GREEN_400
            barra_progreso.color = ft.Colors.GREEN_400
            barra_progreso.value = 1.0
        elif tipo == "error":
            icono_estado.name = ft.Icons.ERROR_OUTLINE
            icono_estado.color = ft.Colors.RED_400
            barra_progreso.color = ft.Colors.RED_400
            barra_progreso.value = 0
        else:
            icono_estado.name = ft.Icons.INFO_OUTLINE
            icono_estado.color = ft.Colors.BLUE_400
            barra_progreso.color = ft.Colors.BLUE_400
        page.update()

    def iniciar_descarga(e):
        url = url_input.value.strip()
        if not url:
            actualizar_estado("Pega un enlace primero.", "error")
            return

        btn_descargar.disabled = True
        btn_descargar.content = "Descargando..."
        barra_progreso.value = None
        actualizar_estado("Conectando y analizando enlace...", "cargando")

        def tarea():
            try:
                descargar_media(
                    url=url,
                    modo=modo_selector.value,
                    calidad=calidad_dropdown.value,
                    formato=formato_dropdown.value,
                    carpeta_destino=carpeta_actual,
                    descargar_subtitulos=chk_subtitulos.value,
                    permitir_playlist=chk_playlist.value,
                    on_progress=actualizar_progreso,
                    on_status=lambda msg: actualizar_estado(msg, "cargando"),
                )
                actualizar_estado("¡Listo! Descarga completada.", "exito")
            except Exception as ex:
                actualizar_estado(f"Error: {ex}", "error")
            finally:
                btn_descargar.disabled = False
                btn_descargar.content = "Descargar"
                page.update()

        threading.Thread(target=tarea, daemon=True).start()

    url_input.on_change = al_cambiar_url
    modo_selector.on_change = lambda e: actualizar_opciones_ui()
    formato_dropdown.on_select = lambda e: actualizar_opciones_ui()

    btn_descargar = ft.Button(
        content="Descargar",
        icon=ft.Icons.DOWNLOAD,
        on_click=iniciar_descarga,
        width=float("inf"),
        height=45,
    )

    # --- Estructura visual ---
    page.add(
        ft.Column(
            [
                # Encabezado
                ft.Row(
                    [
                        ft.Text("Pepe Downloader", size=22, weight=ft.FontWeight.BOLD),
                        badge_plataforma,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                # Sección URL
                ft.Row(
                    [
                        url_input,
                        ft.IconButton(
                            icon=ft.Icons.CLEAR,
                            tooltip="Limpiar enlace",
                            on_click=limpiar_url,
                        ),
                    ]
                ),
                # Sección Formato y Opciones
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Formato y calidad", weight=ft.FontWeight.BOLD),
                            modo_selector,
                            ft.Row([calidad_dropdown, formato_dropdown], spacing=12),
                            chk_subtitulos,
                            chk_playlist,
                            nota_plataforma,
                        ],
                        spacing=8,
                    ),
                    padding=14,
                    border_radius=10,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                ),
                # Sección Carpeta de destino
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("Carpeta de destino", weight=ft.FontWeight.BOLD),
                            ft.Row(
                                [
                                    ft.Icon(ft.Icons.FOLDER, size=18),
                                    texto_carpeta,
                                    ft.IconButton(
                                        icon=ft.Icons.EDIT_LOCATION_ALT,
                                        tooltip="Cambiar carpeta",
                                        on_click=cambiar_carpeta,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.FOLDER_OPEN,
                                        tooltip="Abrir carpeta en Windows",
                                        on_click=abrir_carpeta,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=14,
                    border_radius=10,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                ),
                # Botón de descarga
                btn_descargar,
                # Panel de estado y progreso siempre visible
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [icono_estado, estado_texto],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            barra_progreso,
                        ],
                        spacing=8,
                    ),
                    padding=14,
                    border_radius=10,
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                ),
            ],
            spacing=14,
        )
    )


ft.run(main)