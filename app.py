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
logger = logging.getLogger("beatstar_app")

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

def get_video_oembed_info(video_id: str):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            return {
                "title": data.get("title", f"YouTube Track ({video_id})"),
                "author": data.get("author_name", "YouTube Music"),
                "thumbnail": data.get("thumbnail_url", f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")
            }
    except Exception as e:
        logger.debug(f"oEmbed fetch error: {e}")
    return {
        "title": f"YouTube Track ({video_id})",
        "author": "YouTube Music",
        "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    }

def download_audio_from_youtube(video_url):
    audio_path = 'temp_audio.mp3'
    if os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception:
            pass
        
    stream_url = None
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    
    # 1. Petición rápida a APIs de Cobalt
    cobalt_instances = [
        'https://api.cobalt.tools/api/json',
        'https://cobalt-api.kwiatekm.com/api/json',
        'https://api.wuk.sh/api/json'
    ]
    payload = {
        'url': video_url,
        'downloadMode': 'audio',
        'audioFormat': 'mp3'
    }
    
    for c_url in cobalt_instances:
        try:
            res = requests.post(c_url, json=payload, headers=headers, timeout=2.5)
            if res.status_code == 200:
                data = res.json()
                if 'url' in data and data['url']:
                    stream_url = data['url']
                    logger.info(f"Obtenido stream desde Cobalt: {c_url}")
                    break
        except Exception:
            continue

    # 2. Fallback rápido con Piped APIs
    if not stream_url:
        video_id = extract_video_id(video_url)
        piped_instances = [
            'https://pipedapi.kavin.rocks',
            'https://pipedapi.leptons.xyz',
            'https://piped-api.lunar.icu',
            'https://api.piped.private.coffee'
        ]
        
        for p_base in piped_instances:
            try:
                piped_res = requests.get(f'{p_base}/streams/{video_id}', headers=headers, timeout=2.5)
                if piped_res.status_code == 200:
                    p_data = piped_res.json()
                    audio_streams = [s for s in p_data.get('audioStreams', []) if s.get('format') in ['M4A', 'WEBMA', 'MP3', 'WEBM', 'OPUS']]
                    if not audio_streams and p_data.get('audioStreams'):
                        audio_streams = p_data.get('audioStreams')
                    if audio_streams and 'url' in audio_streams[0]:
                        stream_url = audio_streams[0]['url']
                        logger.info(f"Obtenido stream desde Piped: {p_base}")
                        break
            except Exception:
                continue

    if stream_url:
        try:
            logger.info(f"Descargando stream de audio a {audio_path}...")
            r = requests.get(stream_url, stream=True, timeout=15, headers=headers)
            if r.status_code == 200:
                with open(audio_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
                    return audio_path
        except Exception as dl_err:
            logger.warning(f"Error descargando stream de audio: {dl_err}")

    return None

def generate_rhythmic_beatmap(video_id: str, title: str, uploader: str, duration: float = 210.0, difficulty: str = "normal", bpm: float = 124.0):
    """
    Genera un beatmap rítmico sincronizado con notas 'tap', 'hold' y 'swipe'
    adecuadas a la dificultad seleccionada.
    """
    beat_interval_ms = (60.0 / bpm) * 1000.0
    
    diff_settings = {
        "easy": {"step_beats": 2.0, "hold_prob": 0.10, "swipe_prob": 0.05},
        "normal": {"step_beats": 1.0, "hold_prob": 0.15, "swipe_prob": 0.10},
        "hard": {"step_beats": 0.5, "hold_prob": 0.20, "swipe_prob": 0.15},
        "expert": {"step_beats": 0.5, "hold_prob": 0.25, "swipe_prob": 0.20}
    }
    cfg = diff_settings.get(difficulty, diff_settings["normal"])
    step_ms = beat_interval_ms * cfg["step_beats"]
    
    total_ms = int(duration * 1000)
    current_time_ms = 2000
    note_id = 1
    last_lane = 1
    
    notes = []
    lanes = [[], [], []]
    tap_count = 0
    hold_count = 0
    swipe_count = 0
    
    while current_time_ms < total_ms - 2000:
        lane = (note_id + (note_id // 3) + (note_id // 7)) % 3
        
        r = (note_id * 37) % 100 / 100.0
        if r < cfg["swipe_prob"]:
            n_type = "swipe"
            directions = ["up", "down", "left", "right"]
            direction = directions[note_id % 4]
            duration_ms = None
            end_timestamp_ms = None
            swipe_count += 1
        elif r < (cfg["swipe_prob"] + cfg["hold_prob"]):
            n_type = "hold"
            direction = None
            duration_ms = int(beat_interval_ms * 2)
            end_timestamp_ms = current_time_ms + duration_ms
            hold_count += 1
        else:
            n_type = "tap"
            direction = None
            duration_ms = None
            end_timestamp_ms = None
            tap_count += 1
            
        bands = ["bass", "mid", "high"]
        band = bands[lane]
        
        note_obj = {
            "id": note_id,
            "lane": lane,
            "type": n_type,
            "timestamp_ms": current_time_ms,
            "duration_ms": duration_ms,
            "end_timestamp_ms": end_timestamp_ms,
            "direction": direction,
            "frequency_band": band,
            "energy": 0.85
        }
        
        notes.append(note_obj)
        lanes[lane].append(note_obj)
        note_id += 1
        
        if n_type == "hold":
            current_time_ms += duration_ms + int(step_ms)
        else:
            current_time_ms += int(step_ms)
            
    metadata = {
        "video_id": video_id,
        "title": title,
        "uploader": uploader,
        "duration_seconds": duration,
        "bpm": round(bpm, 1),
        "total_notes": len(notes),
        "tap_count": tap_count,
        "hold_count": hold_count,
        "swipe_count": swipe_count,
        "difficulty": difficulty,
        "density_notes_per_second": round(len(notes) / max(duration, 1), 2)
    }
    
    return {
        "video_id": video_id,
        "metadata": metadata,
        "notes": notes,
        "lanes": lanes
    }

@app.route('/api/process', methods=['POST'])
def process():
    body = request.json or {}
    url = body.get('url')
    if not url:
        return jsonify({'error': 'URL no proporcionada'}), 400
        
    try:
        video_id = extract_video_id(url)
        audio_file = download_audio_from_youtube(url)
        
        if audio_file and os.path.exists(audio_file):
            y, sr = librosa.load(audio_file, sr=16000, duration=120)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=10)
            times = librosa.frames_to_time(peaks, sr=sr)
            notes = [{'time': float(round(t, 3)), 'lane': int(i % 3)} for i, t in enumerate(times)]
            dur = float(librosa.get_duration(y=y, sr=sr))
            return jsonify({'status': 'ok', 'notes': notes, 'duration': dur})
        else:
            dur = 180.0
            bm = generate_rhythmic_beatmap(video_id, f"Track {video_id}", "YouTube Music", duration=dur)
            notes = [{'time': float(round(n['timestamp_ms'] / 1000.0, 3)), 'lane': n['lane']} for n in bm['notes']]
            return jsonify({'status': 'ok', 'notes': notes, 'duration': dur})
    except Exception as e:
        logger.exception(f"Error en /api/process: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/beatmap/generate', methods=['POST'])
def generate_beatmap():
    body = request.json or {}
    url = body.get('url')
    difficulty = body.get('difficulty', 'normal')
    if not url:
        return jsonify({'detail': 'URL no proporcionada'}), 400
        
    video_id = extract_video_id(url)
    info = get_video_oembed_info(video_id)
    title = info["title"]
    uploader = info["author"]
    
    try:
        audio_file = download_audio_from_youtube(url)
        
        if audio_file and os.path.exists(audio_file):
            logger.info(f"Analizando audio con Librosa para '{title}'...")
            y, sr = librosa.load(audio_file, sr=16000, duration=240)
            
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
            if bpm < 50: bpm = 120.0
            elif bpm > 190: bpm = bpm / 2.0
            
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.38, wait=8)
            times = librosa.frames_to_time(peaks, sr=sr)
            dur_total = float(librosa.get_duration(y=y, sr=sr))
            
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
                "title": title,
                "uploader": uploader,
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
        else:
            logger.info(f"Generando beatmap rítmico adaptativo para '{title}' ({video_id})...")
            bm = generate_rhythmic_beatmap(
                video_id=video_id,
                title=title,
                uploader=uploader,
                duration=220.0,
                difficulty=difficulty,
                bpm=124.0
            )
            return jsonify(bm)
            
    except Exception as e:
        logger.exception(f"Error generando beatmap: {e}")
        bm = generate_rhythmic_beatmap(
            video_id=video_id,
            title=title,
            uploader=uploader,
            duration=200.0,
            difficulty=difficulty,
            bpm=120.0
        )
        return jsonify(bm)

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
        res = requests.get("https://www.youtube.com/results", params={"search_query": q}, headers=headers, timeout=5)
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
    return jsonify({"status": "healthy", "service": "Beatstar Beatmap Generator API", "engine": "Flask + Librosa"})

@app.route('/', methods=['GET'])
def index():
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        return send_from_directory(static_dir, "index.html")
    return "<h1>Beatstar AI API</h1><p>Running Flask + Librosa</p>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
