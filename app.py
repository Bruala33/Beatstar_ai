import os
import re
import glob
import json
import base64
import tempfile
import logging
import requests
import librosa
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("beatstar_strict")

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
app = Flask(__name__, static_folder=static_dir, static_url_path="/static")
CORS(app)

# ─── Instancias de APIs proxy (fallback si la descarga directa fallase) ───────
PIPED_INSTANCES = [
    "https://pipedapi.adminforge.de",
    "https://pipedapi.drgns.space",
    "https://pipedapi.r4fo.com",
    "https://piped-api.lunar.icu",
]

INVIDIOUS_INSTANCES = [
    "https://invidious.nerdvpn.de",
    "https://inv.nadeko.net",
    "https://invidious.private.coffee",
    "https://yewtu.be",
]

def get_cookiefile_path():
    """Detecta automáticamente cookies en variables de entorno o archivos locales."""
    b64_val = os.environ.get("YOUTUBE_COOKIES_BASE64") or os.environ.get("COOKIES_BASE64")
    if b64_val and len(b64_val.strip()) > 20:
        try:
            decoded = base64.b64decode(b64_val.strip()).decode("utf-8", errors="ignore")
            target_path = os.path.join(tempfile.gettempdir(), "render_youtube_cookies.txt")
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(decoded)
            return target_path
        except Exception as e:
            logger.warning(f"Error decodificando YOUTUBE_COOKIES_BASE64: {e}")

    raw_val = os.environ.get("YOUTUBE_COOKIES") or os.environ.get("COOKIES_TXT")
    if raw_val and len(raw_val.strip()) > 20:
        try:
            target_path = os.path.join(tempfile.gettempdir(), "render_youtube_cookies.txt")
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_val.strip())
            return target_path
        except Exception as e:
            logger.warning(f"Error escribiendo YOUTUBE_COOKIES: {e}")

    project_root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        "/etc/secrets/cookies.txt",
        "/etc/secrets/render_youtube_cookies.txt",
        os.path.join(project_root, "cookies.txt"),
        os.path.join(os.getcwd(), "cookies.txt"),
        os.path.join(tempfile.gettempdir(), "cookies.txt"),
        "cookies.txt"
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isfile(c) and os.path.getsize(c) > 0:
            return c

    return None

def extract_video_id(url: str) -> str:
    """Extrae el ID del video de cualquier formato de URL de YouTube"""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'embed\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        m = re.search(pattern, (url or "").strip())
        if m:
            return m.group(1)
    return (url or "").strip()

# ─── Método 1: yt-dlp con emulación móvil InnerTube y player_skip ─────────────
def download_via_ytdlp(url: str, output_prefix: str) -> str:
    if not HAS_YTDLP:
        raise Exception("yt-dlp no está instalado")

    cookiefile = get_cookiefile_path()

    opts_list = [
        # 1. Android mobile client (sin tocar webpage para evitar bot check en datacenter)
        {
            'format': 'ba/b',
            'outtmpl': f'{output_prefix}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                    'player_skip': ['webpage', 'configs']
                }
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        },
        # 2. iOS + Android combinados
        {
            'format': 'ba/b',
            'outtmpl': f'{output_prefix}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android', 'mweb'],
                    'player_skip': ['webpage', 'configs']
                }
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        },
        # 3. Formato estándar
        {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_prefix}.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
        }
    ]

    last_err = None
    for idx, ydl_opts in enumerate(opts_list, 1):
        if cookiefile:
            ydl_opts['cookiefile'] = cookiefile
        logger.info(f"yt-dlp intento {idx}/{len(opts_list)} (cookies={'SI' if cookiefile else 'NO'})...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            files = glob.glob(f"{output_prefix}.*")
            if files:
                logger.info(f"yt-dlp: descarga exitosa en intento {idx}: {files[0]}")
                return files[0]
        except Exception as e:
            last_err = e
            logger.warning(f"yt-dlp intento {idx} falló: {e}")

    raise Exception(f"yt-dlp: todos los intentos fallaron: {last_err}")

# ─── Método 2: Piped API (proxy público sin bloqueo de IP) ────────────────────
def download_via_piped(video_id: str, output_prefix: str) -> str:
    """Descarga audio usando instancias de Piped API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    last_err = None
    for instance in PIPED_INSTANCES:
        api_url = f"{instance}/streams/{video_id}"
        logger.info(f"Piped: intentando {instance}...")
        try:
            resp = requests.get(api_url, headers=headers, timeout=10)
            if resp.status_code != 200 or not resp.text.strip().startswith('{'):
                logger.warning(f"Piped {instance}: HTTP {resp.status_code}")
                continue

            data = resp.json()
            audio_streams = data.get("audioStreams", [])
            if not audio_streams:
                logger.warning(f"Piped {instance}: sin audio streams")
                continue

            audio_streams.sort(key=lambda s: s.get("bitrate", 0), reverse=True)
            stream_url = audio_streams[0].get("url")
            if not stream_url:
                continue

            logger.info(f"Piped: descargando stream desde {instance}...")
            audio_resp = requests.get(stream_url, headers=headers, timeout=60, stream=True)
            if audio_resp.status_code != 200:
                continue

            mime = audio_streams[0].get("mimeType", "audio/webm")
            ext = "webm" if "webm" in mime else "mp4" if "mp4" in mime else "ogg"
            out_file = f"{output_prefix}.{ext}"

            with open(out_file, "wb") as f:
                for chunk in audio_resp.iter_content(chunk_size=16384):
                    f.write(chunk)

            if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
                logger.info(f"Piped: descarga exitosa: {out_file}")
                return out_file

        except Exception as e:
            last_err = e
            logger.warning(f"Piped {instance} error: {e}")

    raise Exception(f"Piped: todas las instancias fallaron: {last_err}")

# ─── Método 3: Invidious API ──────────────────────────────────────────────────
def download_via_invidious(video_id: str, output_prefix: str) -> str:
    """Descarga audio usando instancias públicas de Invidious API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    last_err = None
    for instance in INVIDIOUS_INSTANCES:
        api_url = f"{instance}/api/v1/videos/{video_id}"
        logger.info(f"Invidious: intentando {instance}...")
        try:
            resp = requests.get(api_url, headers=headers, timeout=10)
            if resp.status_code != 200 or not resp.text.strip().startswith('{'):
                continue

            data = resp.json()
            adaptive = data.get("adaptiveFormats", [])
            audio_formats = [f for f in adaptive if f.get("type", "").startswith("audio/")]
            if not audio_formats:
                continue

            audio_formats.sort(key=lambda f: int(f.get("bitrate", "0")), reverse=True)
            stream_url = audio_formats[0].get("url")
            if not stream_url:
                continue

            audio_resp = requests.get(stream_url, headers=headers, timeout=60, stream=True)
            if audio_resp.status_code != 200:
                continue

            mime = audio_formats[0].get("type", "audio/webm")
            ext = "webm" if "webm" in mime else "mp4" if "mp4" in mime else "ogg"
            out_file = f"{output_prefix}.{ext}"

            with open(out_file, "wb") as f:
                for chunk in audio_resp.iter_content(chunk_size=16384):
                    f.write(chunk)

            if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
                logger.info(f"Invidious: descarga exitosa: {out_file}")
                return out_file

        except Exception as e:
            last_err = e
            logger.warning(f"Invidious {instance} error: {e}")

    raise Exception(f"Invidious: todas las instancias fallaron: {last_err}")

# ─── Coordinador de descarga ──────────────────────────────────────────────────
def download_youtube_audio_strict(url: str, output_prefix: str = "audio_temp") -> str:
    """Descarga audio intentando yt-dlp (InnerTube Android directo) -> Piped -> Invidious"""
    for f in glob.glob(f"{output_prefix}.*"):
        try:
            os.remove(f)
        except Exception:
            pass

    video_id = extract_video_id(url)
    errors = []

    # 1. yt-dlp con player_client=['android'] y player_skip=['webpage','configs']
    try:
        return download_via_ytdlp(url, output_prefix)
    except Exception as e:
        errors.append(f"yt-dlp: {e}")
        logger.warning(f"yt-dlp falló, probando Piped API: {e}")

    # 2. Piped API
    try:
        return download_via_piped(video_id, output_prefix)
    except Exception as e:
        errors.append(f"Piped: {e}")
        logger.warning(f"Piped falló, probando Invidious: {e}")

    # 3. Invidious API
    try:
        return download_via_invidious(video_id, output_prefix)
    except Exception as e:
        errors.append(f"Invidious: {e}")

    raise Exception(f"Fallo en descarga de audio (todos los métodos): {' | '.join(errors)}")

# ─── Rutas API ────────────────────────────────────────────────────────────────
@app.route('/api/process', methods=['POST'])
def process():
    url = (request.json or {}).get('url')
    if not url:
        return jsonify({'error': 'URL requerida'}), 400

    try:
        audio_file = download_youtube_audio_strict(url, output_prefix="audio_temp_process")

        logger.info(f"Cargando {audio_file} con Librosa para análisis real...")
        y, sr = librosa.load(audio_file, sr=16000, duration=120)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.45, wait=8)
        times = librosa.frames_to_time(peaks, sr=sr)

        notes = [{'time': float(round(t, 3)), 'lane': int(i % 3)} for i, t in enumerate(times)]
        return jsonify({'status': 'ok', 'notes': notes, 'duration': float(librosa.get_duration(y=y, sr=sr))})

    except Exception as e:
        logger.exception(f"Error en /api/process: {e}")
        return jsonify({'error': f"Error en análisis de audio real: {str(e)}"}), 500

@app.route('/api/v1/beatmap/generate', methods=['POST'])
def generate_beatmap():
    body = request.json or {}
    url = body.get('url')
    difficulty = body.get('difficulty', 'normal')
    if not url:
        return jsonify({'detail': 'URL requerida'}), 400

    video_id = extract_video_id(url)

    try:
        audio_file = download_youtube_audio_strict(url, output_prefix=f"audio_temp_{video_id}")

        logger.info(f"Analizando transitorios reales con Librosa para {video_id}...")
        y, sr = librosa.load(audio_file, sr=16000, duration=180)
        dur_total = float(librosa.get_duration(y=y, sr=sr))

        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
        if bpm < 50: bpm = 120.0
        elif bpm > 190: bpm = bpm / 2.0

        delta_map = {"easy": 0.50, "normal": 0.38, "hard": 0.28, "expert": 0.22}
        delta = delta_map.get(difficulty, 0.38)

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=delta, wait=8)
        times = librosa.frames_to_time(peaks, sr=sr)

        notes_list = []
        lanes = [[], [], []]
        for i, t in enumerate(times):
            time_ms = int(t * 1000)
            lane = int(i % 3)
            note_obj = {
                "id": i + 1,
                "lane": lane,
                "type": "tap",
                "timestamp_ms": time_ms,
                "duration_ms": None,
                "end_timestamp_ms": None,
                "direction": None,
                "frequency_band": ["bass", "mid", "high"][lane],
                "energy": 0.85
            }
            notes_list.append(note_obj)
            lanes[lane].append(note_obj)

        metadata = {
            "video_id": video_id,
            "title": f"YouTube Track ({video_id})",
            "uploader": "YouTube",
            "duration_seconds": dur_total,
            "bpm": round(bpm, 1),
            "total_notes": len(notes_list),
            "tap_count": len(notes_list),
            "hold_count": 0,
            "swipe_count": 0,
            "difficulty": difficulty,
            "density_notes_per_second": round(len(notes_list) / max(dur_total, 1), 2)
        }

        return jsonify({
            "video_id": video_id,
            "metadata": metadata,
            "notes": notes_list,
            "lanes": lanes
        })

    except Exception as e:
        logger.exception(f"Error estricto en generate_beatmap: {e}")
        return jsonify({'detail': f"Error en análisis de audio real: {str(e)}"}), 500

@app.route('/api/search', methods=['GET'])
@app.route('/api/v1/search', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
        }
        res = requests.get("https://www.youtube.com/results", params={"search_query": q}, headers=headers, timeout=6)
        if res.status_code != 200:
            return jsonify([])

        m = re.search(r"var ytInitialData = ({.+?});</script>", res.text) or re.search(r"ytInitialData\s*=\s*({.+?});</script>", res.text)
        if not m:
            return jsonify([])

        data = json.loads(m.group(1))
        videos = []
        sections = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        for sec in sections:
            items = sec.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                vr = item.get("videoRenderer")
                if vr and "videoId" in vr:
                    vid_id = vr.get("videoId")
                    title = "".join(r.get("text", "") for r in vr.get("title", {}).get("runs", [])) if vr.get("title", {}).get("runs") else (vr.get("title", {}).get("simpleText") or "Sin título")
                    uploader = "".join(r.get("text", "") for r in vr.get("ownerText", {}).get("runs", [])) if vr.get("ownerText", {}).get("runs") else "YouTube"
                    dur_str = vr.get("lengthText", {}).get("simpleText", "")
                    sec_count = 0
                    if dur_str:
                        parts = [int(p) for p in dur_str.split(":") if p.isdigit()]
                        if len(parts) == 2: sec_count = parts[0] * 60 + parts[1]
                        elif len(parts) == 3: sec_count = parts[0] * 3600 + parts[1] * 60 + parts[2]

                    videos.append({
                        "id": vid_id,
                        "title": title,
                        "channel": uploader,
                        "duration": sec_count,
                        "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                        "url": f"https://www.youtube.com/watch?v={vid_id}"
                    })
                    if len(videos) >= 10:
                        break
            if len(videos) >= 10:
                break
        return jsonify(videos)
    except Exception as e:
        logger.warning(f"Error en búsqueda: {e}")
        return jsonify([])

@app.route('/api/v1/playlists/ytmusic/search', methods=['GET'])
def search_ytmusic_playlists():
    return jsonify([])

@app.route('/api/v1/playlists/ytmusic/import_url', methods=['POST'])
def import_playlist():
    return jsonify({"title": "Playlist", "item_count": 0, "tracks": []})

@app.route('/api/v1/health', methods=['GET'])
def health():
    cookie_loaded = get_cookiefile_path() is not None
    return jsonify({
        "status": "healthy",
        "service": "Beatstar Beatmap Generator API",
        "engine": "Flask + Librosa Strict (yt-dlp InnerTube + Proxies)",
        "cookies_loaded": cookie_loaded
    })

@app.route('/', methods=['GET'])
def index():
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return send_from_directory(static_dir, "index.html")
    return "<h1>Beatstar AI API</h1><p>Flask + Strict Librosa</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
