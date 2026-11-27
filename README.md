# Pepe Video Downloader

Descargador de escritorio para Windows construido con **Python**, **Flet** y **yt-dlp**, con control explícito de formatos/calidades, soporte local para **FFmpeg** y una interfaz compacta de ventana fija.

> **Versión actual:** `v0.1.3`

---

## Características

* **Selector de formato y calidad:** Configura descargas de video (`MP4`, `MKV`, `WEBM`) y audio (`MP3`, `M4A`, `WAV`, `OPUS`, ideal para compatibilidad en apps de mensajería) tanto para YouTube como para Instagram.
* **Interfaz de ventana fija:** Diseño sin scroll con indicadores visuales de estado y barra de progreso persistente durante la descarga y el procesamiento.
* **FFmpeg local:** Detecta automáticamente el binario en `assets/ffmpeg.exe` (o en las rutas del ejecutable/proyecto) sin depender de una instalación global en el sistema.
* **Identidad visual personalizada:** Ícono configurado para la ventana y la barra de tareas de Windows.

---

## Estructura del proyecto

```text
Pepe-VideoDownloader/
├── assets/
│   ├── ffmpeg.exe      # Binario local (ignorado en Git por tamaño)
│   └── icon.ico        # Ícono de la aplicación
├── downloader.py       # Lógica de descarga y postprocesamiento con yt-dlp / FFmpeg
├── main.py             # Interfaz gráfica y control de estados con Flet
├── .gitignore          # Exclusiones de entorno, caché y binarios pesados
└── README.md
