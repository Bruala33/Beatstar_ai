import os
import re
import json
import logging
import requests
import librosa
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("beatstar_flask")

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
app = Flask(__name__, static_folder=static_dir, static_url_path="/static")
CORS(app)

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

def download_audio_from_youtube(video_url):
    audio_path = 'temp_audio.mp3'
    if os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception:
            pass
        
    stream_url = None
    
    # 1. Petición a la API de Cobalt para resolver el stream sin bloqueo de IP
    cobalt_instances = [
        'https://api.cobalt.tools/api/json',
        'https://cobalt-api.kwiatekm.com/api/json',
        'https://api.wuk.sh/api/json'
    ]
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    payload = {
        'url': video_url,
        'downloadMode': 'audio',
        'audioFormat': 'mp3'
    }
    
    for c_url in cobalt_instances:
        try:
            res = requests.post(c_url, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if 'url' in data and data['url']:
                    stream_url = data['url']
                    logger.info(f"Obtenido stream de audio desde Cobalt: {c_url}")
                    break
        except Exception as ce:
            logger.debug(f"Cobalt instance {c_url} error: {ce}")
            continue

    # 2. Fallback con Piped API si Cobalt no responde o está saturado
    if not stream_url:
        video_id = extract_video_id(video_url)
        piped_instances = [
            'https://pipedapi.kavin.rocks',
            'https://pipedapi.leptons.xyz',
            'https://piped-api.lunar.icu',
            'https://api.piped.private.coffee',
            'https://pipedapi-libre.kavin.rocks',
            'https://api.piped.projectsegfau.lt'
        ]
        
        for p_base in piped_instances:
            try:
                piped_res = requests.get(f'{p_base}/streams/{video_id}', headers=headers, timeout=10)
                if piped_res.status_code == 200:
                    p_data = piped_res.json()
                    audio_streams = [s for s in p_data.get('audioStreams', []) if s.get('format') in ['M4A', 'WEBMA', 'MP3', 'WEBM', 'OPUS']]
                    if not audio_streams and p_data.get('audioStreams'):
                        audio_streams = p_data.get('audioStreams')
                    if audio_streams and 'url' in audio_streams[0]:
                        stream_url = audio_streams[0]['url']
                        logger.info(f"Obtenido stream de audio desde Piped: {p_base}")
                        break
            except Exception as pe:
                logger.debug(f"Piped instance {p_base} error: {pe}")
                continue

    # 3. Fallback con Invidious API
    if not stream_url:
        video_id = extract_video_id(video_url)
        invidious_instances = [
            'https://invidious.nerdvpn.de',
            'https://inv.nadeko.net',
            'https://invidious.private.coffee'
        ]
        for inv_base in invidious_instances:
            try:
                inv_res = requests.get(f'{inv_base}/api/v1/videos/{video_id}', headers=headers, timeout=10)
                if inv_res.status_code == 200:
                    inv_data = inv_res.json()
                    adaptive = inv_data.get('adaptiveFormats', [])
                    audio_streams = [s for s in adaptive if 'audio' in s.get('type', '')]
                    if audio_streams and 'url' in audio_streams[0]:
                        stream_url = audio_streams[0]['url']
                        logger.info(f"Obtenido stream de audio desde Invidious: {inv_base}")
                        break
            except Exception as ie:
                logger.debug(f"Invidious instance {inv_base} error: {ie}")
                continue

    if not stream_url:
        raise Exception("No se pudo obtener el stream de audio de YouTube mediante Cobalt ni Piped.")
        
    # Descargar el stream directo al archivo local
    logger.info(f"Descargando stream de audio a {audio_path}...")
    r = requests.get(stream_url, stream=True, timeout=30, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Error HTTP {r.status_code} al descargar el stream de audio.")
        
    with open(audio_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
            
    return audio_path

@app.route('/api/process', methods=['POST'])
def process():
    body = request.json or {}
    url = body.get('url')
    if not url:
        return jsonify({'error': 'URL no proporcionada'}), 400
        
    try:
        audio_file = download_audio_from_youtube(url)
        
        # Análisis con Librosa optimizado para 512MB RAM
        y, sr = librosa.load(audio_file, sr=16000, duration=120)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=10)
        times = librosa.frames_to_time(peaks, sr=sr)
        
        notes = [{'time': float(round(t, 3)), 'lane': int(i % 3)} for i, t in enumerate(times)]
        return jsonify({'status': 'ok', 'notes': notes, 'duration': float(librosa.get_duration(y=y, sr=sr))})
    except Exception as e:
        logger.exception(f"Error procesando audio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/beatmap/generate', methods=['POST'])
def generate_beatmap_compatibility():
    body = request.json or {}
    url = body.get('url')
    difficulty = body.get('difficulty', 'normal')
    if not url:
        return jsonify({'detail': 'URL no proporcionada'}), 400
        
    try:
        video_id = extract_video_id(url)
        audio_file = download_audio_from_youtube(url)
        
        y, sr = librosa.load(audio_file, sr=16000, duration=180)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
        if bpm < 50: bpm = 120.0
        elif bpm > 190: bpm = bpm / 2.0
        
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.4, wait=8)
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
                "frequency_band": "mid",
                "energy": 0.8
            }
            notes_list.append(note_obj)
            lanes[lane].append(note_obj)
            
        dur_total = float(librosa.get_duration(y=y, sr=sr))
        metadata = {
            "video_id": video_id,
            "title": f"YouTube Track ({video_id})",
            "uploader": "YouTube Music",
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
        logger.exception(f"Error generando beatmap: {e}")
        return jsonify({'detail': str(e)}), 500

@app.route('/api/search', methods=['GET'])
@app.route('/api/v1/search', methods=['GET'])
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
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

@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "engine": "flask-cobalt-piped"})

@app.route('/', methods=['GET'])
def index():
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return send_from_directory(static_dir, "index.html")
    return "<h1>Beatstar AI API</h1><p>Flask + Librosa + Cobalt/Piped Running</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
