import os
import re
import glob
import json
import base64
import tempfile
import logging
import yt_dlp
import librosa
import numpy as np
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("beatstar_strict")

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
app = Flask(__name__, static_folder=static_dir, static_url_path="/static")
CORS(app)

def get_cookiefile_path():
    """
    Detecta automáticamente cookies en variables de entorno o archivos locales/secretos de Render.
    """
    # 1. Base64 encoded cookies
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

    # 2. Raw text cookies en variable de entorno
    raw_val = os.environ.get("YOUTUBE_COOKIES") or os.environ.get("COOKIES_TXT")
    if raw_val and len(raw_val.strip()) > 20:
        try:
            target_path = os.path.join(tempfile.gettempdir(), "render_youtube_cookies.txt")
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(raw_val.strip())
            return target_path
        except Exception as e:
            logger.warning(f"Error escribiendo YOUTUBE_COOKIES: {e}")

    # 3. Archivos candidatos (Render Secret Files / local)
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

def download_youtube_audio_strict(url: str, output_prefix: str = "audio_temp") -> str:
    # Limpiar archivos temporales previos
    for f in glob.glob(f"{output_prefix}.*"):
        try:
            os.remove(f)
        except Exception:
            pass

    cookiefile = get_cookiefile_path()

    ydl_opts = {
        'format': 'ba/b',
        'outtmpl': f'{output_prefix}.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'android_creator']
            }
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
    }

    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile
        logger.info(f"Usando cookiefile: {cookiefile}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    files = glob.glob(f"{output_prefix}.*")
    if not files:
        raise Exception("Fallo en descarga de audio: no se generó ningún archivo de audio")

    return files[0]

@app.route('/api/process', methods=['POST'])
def process():
    url = (request.json or {}).get('url')
    if not url:
        return jsonify({'error': 'URL requerida'}), 400

    try:
        audio_file = download_youtube_audio_strict(url, output_prefix="audio_temp_process")

        # Detección de ritmo real con Librosa (máximo 120s para memoria de Render)
        logger.info(f"Cargando {audio_file} con Librosa para análisis real...")
        y, sr = librosa.load(audio_file, sr=16000, duration=120)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=10)
        times = librosa.frames_to_time(peaks, sr=sr)

        notes = [{'time': float(round(t, 3)), 'lane': int(i % 3)} for i, t in enumerate(times)]
        return jsonify({'status': 'ok', 'notes': notes, 'duration': float(librosa.get_duration(y=y, sr=sr))})

    except Exception as e:
        logger.exception(f"Error en análisis de audio real: {e}")
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

        # Umbrales según dificultad
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
        "engine": "Flask + Librosa Strict (yt-dlp)",
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
