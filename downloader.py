import os
import yt_dlp


def get_ffmpeg_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_ffmpeg = os.path.join(base_dir, "assets", "ffmpeg.exe")
    return local_ffmpeg if os.path.exists(local_ffmpeg) else None


def descargar_media(
    url: str,
    modo: str,
    calidad: str,
    formato: str,
    carpeta_destino: str,
    descargar_subtitulos: bool = False,
    permitir_playlist: bool = False,
    on_progress=None,
    on_status=None,
):
    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            descargado = d.get("downloaded_bytes", 0)

            if total:
                porcentaje = descargado / total
                if on_progress:
                    on_progress(porcentaje)
                if on_status:
                    on_status(f"Descargando... {int(porcentaje * 100)}%")
            elif d.get("fragment_index") and d.get("fragment_count"):
                porcentaje = d["fragment_index"] / d["fragment_count"]
                if on_progress:
                    on_progress(porcentaje)
                if on_status:
                    on_status(f"Descargando... {int(porcentaje * 100)}%")
            else:
                if on_progress:
                    on_progress(None)
                if on_status:
                    on_status("Descargando...")
        elif d["status"] == "finished":
            if on_progress:
                on_progress(None)
            if on_status:
                on_status("Procesando archivo final...")

    opciones = {
        "outtmpl": os.path.join(carpeta_destino, "%(title)s.%(ext)s"),
        "progress_hooks": [hook],
        "noplaylist": not permitir_playlist,
    }

    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path:
        opciones["ffmpeg_location"] = ffmpeg_path

    if modo == "audio":
        postprocessor = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": formato,  # "mp3", "m4a", "wav", "opus"
        }
        if formato != "wav":
            postprocessor["preferredquality"] = calidad

        opciones.update({
            "format": "bestaudio/best",
            "postprocessors": [postprocessor],
        })
    else:
        if calidad == "best":
            if formato == "mp4":
                selector_video = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            else:
                selector_video = "bestvideo+bestaudio/best"
        else:
            if formato == "mp4":
                selector_video = (
                    f"bestvideo[height<={calidad}][ext=mp4]+bestaudio[ext=m4a]/"
                    f"best[height<={calidad}][ext=mp4]/best"
                )
            else:
                selector_video = f"bestvideo[height<={calidad}]+bestaudio/best[height<={calidad}]/best"

        opciones["format"] = selector_video
        opciones["merge_output_format"] = formato  # "mp4", "mkv", "webm"

        if descargar_subtitulos:
            opciones.update({
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["es", "en"],
            })

    with yt_dlp.YoutubeDL(opciones) as ydl:
        ydl.download([url])