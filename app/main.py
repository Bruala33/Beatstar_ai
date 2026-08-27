import os
import time
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import numpy as np

from app.config import settings
from app.models.beatmap import (
    GenerateBeatmapRequest,
    BeatmapResponse,
    BeatstarNote,
    BeatmapMetadata
)
from app.services.downloader import AudioDownloader
from app.services.audio_analyzer import AudioAnalyzer
from app.services.beatmap_generator import BeatmapGenerator
from app.api.endpoints.playlists import router as playlists_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("beatstar_api")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API para generar beatmaps estilo Beatstar a partir de URLs de YouTube usando Librosa y yt-dlp."
)

app.include_router(playlists_router, prefix="/api/v1/playlists", tags=["Playlists"])

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

downloader = AudioDownloader()
analyzer = AudioAnalyzer(sr=settings.SAMPLE_RATE, hop_length=settings.HOP_LENGTH)


@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Verifica el estado del servidor y los parámetros de configuración.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "sample_rate": settings.SAMPLE_RATE,
        "num_lanes": settings.NUM_LANES
    }


@app.get("/api/search", tags=["Search"], summary="Busca vídeos en YouTube con yt-dlp")
@app.get("/api/v1/search", tags=["Search"], summary="Busca vídeos en YouTube con yt-dlp")
async def search_videos(q: str):
    """
    Busca vídeos en YouTube usando ytsearch8 y devuelve metadatos estructurados.
    """
    if not q or not q.strip():
        return []
    try:
        results = downloader.search_youtube(query=q.strip(), max_results=8)
        return results
    except Exception as e:
        logger.exception(f"Error executing YouTube search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar en YouTube: {str(e)}"
        )



@app.post(
    "/api/v1/beatmap/generate",
    response_model=BeatmapResponse,
    tags=["Beatmap Generation"],
    summary="Genera un beatmap estilo Beatstar desde una URL de YouTube"
)
async def generate_beatmap(request: GenerateBeatmapRequest):
    """
    Procesa una URL de YouTube:
    1. Descarga el audio temporalmente en memoria con yt-dlp.
    2. Analiza transitorios, separación de frecuencias (bajos, medios, altos) y notas sostenidas con librosa.
    3. Genera un beatmap de 3 carriles con notas 'tap', 'hold' y 'swipe'.
    4. Devuelve el JSON con el beatmap completo y el ID del vídeo.
    """
    start_time = time.time()
    logger.info(f"Received beatmap request for URL: {request.url} (Difficulty: {request.difficulty})")

    video_id = downloader.extract_video_id(request.url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL de YouTube inválida. Proporciona una URL completa o el ID del vídeo."
        )

    try:
        # Step 1: Download / Extract audio waveform into memory
        y, sr, meta = downloader.fetch_and_load_audio(
            url=request.url,
            target_sr=settings.SAMPLE_RATE,
            max_duration=settings.MAX_DURATION_SECONDS
        )

        # Step 2: Analyze acoustic features with Librosa
        analysis = analyzer.analyze(
            y=y,
            onset_sensitivity=request.onset_sensitivity or 1.0
        )

        # Step 3: Generate 3-lane Beatstar beatmap
        beatmap = BeatmapGenerator.generate(
            analysis=analysis,
            metadata=meta,
            difficulty=request.difficulty,
            snap_to_grid=request.snap_to_grid
        )

        elapsed = round(time.time() - start_time, 2)
        logger.info(
            f"Beatmap generated successfully in {elapsed}s for video '{meta.get('title')}'. "
            f"Total notes: {beatmap.metadata.total_notes}"
        )
        return beatmap

    except ValueError as ve:
        logger.warning(f"Validation error processing audio: {str(ve)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        logger.exception(f"Unexpected error generating beatmap: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno procesando el audio: {str(e)}"
        )


@app.get(
    "/api/v1/beatmap/sample",
    response_model=BeatmapResponse,
    tags=["Beatmap Generation"],
    summary="Genera un beatmap de prueba con audio sintético para testing rápido"
)
async def generate_sample_beatmap(difficulty: str = "normal"):
    """
    Genera un beatmap de prueba a partir de una pista sintética (kick, snare, bassline, synth melody)
    sin requerir conexión a YouTube.
    """
    sr = settings.SAMPLE_RATE
    duration = 15.0  # 15 seconds
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    
    # Create synthetic musical tracks:
    # 1. Kick on every 0.5s (120 BPM)
    kick = np.zeros_like(t)
    for beat_t in np.arange(0, duration, 0.5):
        idx = int(beat_t * sr)
        burst_len = min(int(0.1 * sr), len(t) - idx)
        decay = np.exp(-np.linspace(0, 10, burst_len))
        kick[idx:idx+burst_len] += np.sin(2 * np.pi * 60 * np.linspace(0, 0.1, burst_len)) * decay

    # 2. Melody synth with sustained notes (holds)
    melody = np.zeros_like(t)
    for start_t, dur, freq in [(1.0, 1.2, 440.0), (3.0, 1.0, 523.25), (5.0, 1.5, 659.25), (8.0, 0.8, 587.33)]:
        idx = int(start_t * sr)
        m_len = min(int(dur * sr), len(t) - idx)
        env = np.ones(m_len)
        melody[idx:idx+m_len] += np.sin(2 * np.pi * freq * np.linspace(0, dur, m_len)) * 0.7 * env

    # Combined synthetic audio
    y = kick + melody
    # Normalize
    y = y / (np.max(np.abs(y)) + 1e-6)

    meta = {
        "video_id": "sample_demo_120bpm",
        "title": "Beatstar Demo Track (120 BPM Synth & Percussion)",
        "uploader": "AudioSynth Lab",
        "duration": duration,
        "thumbnail": ""
    }

    analysis = analyzer.analyze(y=y, onset_sensitivity=1.0)
    beatmap = BeatmapGenerator.generate(
        analysis=analysis,
        metadata=meta,
        difficulty=difficulty, # type: ignore
        snap_to_grid=True
    )
    return beatmap


@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
async def serve_ui():
    """
    Sirve la interfaz web interactiva para probar el generador de beatmaps.
    """
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Beatstar Beatmap API</h1><p>Visita <a href='/docs'>/docs</a> para la documentación OpenAPI.</p>")
