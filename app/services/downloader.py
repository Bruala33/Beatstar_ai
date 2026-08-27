import io
import os
import re
import tempfile
import logging
from typing import Tuple, Dict, Any, Optional
import yt_dlp
import soundfile as sf
import librosa
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

class AudioDownloader:
    """
    Handles YouTube audio extraction and in-memory/temp buffer decoding using yt-dlp.
    Configured with mobile client bypass headers and cookies.txt fallback to prevent cloud bot blocks.
    """

    @classmethod
    def get_base_ydl_opts(cls) -> Dict[str, Any]:
        """
        Returns base yt-dlp configuration with mobile client bypass (android, ios, mweb)
        and automatic cookies.txt detection to prevent bot-detection blocking.
        """
        opts: Dict[str, Any] = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'mweb'],
                    'player_skip': ['webpage', 'configs']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11; en_US) gzip'
            }
        }

        # Check for optional cookies.txt in workspace root or current directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        cookie_candidates = [
            'cookies.txt',
            os.path.join(os.getcwd(), 'cookies.txt'),
            os.path.join(project_root, 'cookies.txt')
        ]
        for candidate in cookie_candidates:
            if os.path.exists(candidate) and os.path.isfile(candidate):
                opts['cookiefile'] = candidate
                logger.info(f"Found and loaded yt-dlp cookiefile: {candidate}")
                break

        return opts

    @classmethod
    def search_youtube(cls, query: str, max_results: int = 8) -> list:
        """
        Searches YouTube using ytsearch and returns a clean list of video metadata.
        """
        if not query or not query.strip():
            return []
            
        ydl_opts = cls.get_base_ydl_opts()
        ydl_opts.update({
            'extract_flat': True,
            'skip_download': True,
            'noplaylist': True,
        })
        
        search_query = f"ytsearch{max_results}:{query.strip()}"
        logger.info(f"Executing YouTube search: '{query}'")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                entries = info.get('entries', []) if info else []
                
                results = []
                for entry in entries:
                    if not entry:
                        continue
                    video_id = entry.get('id')
                    if not video_id:
                        continue
                        
                    # Extract best thumbnail
                    thumbnails = entry.get('thumbnails', [])
                    thumb_url = ''
                    if thumbnails:
                        thumb_url = thumbnails[-1].get('url', '')
                    elif entry.get('thumbnail'):
                        thumb_url = entry.get('thumbnail')
                    else:
                        thumb_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                    results.append({
                        "id": video_id,
                        "title": entry.get('title', 'Sin título'),
                        "channel": entry.get('uploader') or entry.get('channel') or 'Desconocido',
                        "duration": int(entry.get('duration') or 0),
                        "thumbnail": thumb_url,
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })
                return results
        except Exception as e:
            logger.error(f"Search failed for '{query}': {str(e)}")
            return []

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """
        Extracts YouTube video ID from various URL formats.
        """
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'embed\/([0-9A-Za-z_-]{11})',
            r'shorts\/([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url.strip())
            if match:
                return match.group(1)
        return None

    @classmethod
    def fetch_and_load_audio(
        cls, 
        url: str, 
        target_sr: int = settings.SAMPLE_RATE,
        max_duration: int = settings.MAX_DURATION_SECONDS
    ) -> Tuple[np.ndarray, int, Dict[str, Any]]:
        """
        Downloads audio from YouTube into a temporary memory/file buffer and loads it as a numpy array.
        Returns:
            - y: np.ndarray (audio waveform, mono)
            - sr: int (sampling rate)
            - metadata: dict with video info (id, title, uploader, duration, thumbnail)
        """
        clean_id = cls.extract_video_id(url)
        normalized_url = f"https://www.youtube.com/watch?v={clean_id}" if clean_id else url

        # Create temporary working directory that gets cleaned up automatically
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
            
            ydl_opts = cls.get_base_ydl_opts()
            ydl_opts.update({
                'format': 'bestaudio/best',
                'outtmpl': temp_output_template,
                'noplaylist': True,
                'extract_flat': False,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
            })

            logger.info(f"Extracting audio from URL: {normalized_url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info_dict = ydl.extract_info(normalized_url, download=True)
                except Exception as e:
                    logger.error(f"yt-dlp extraction failed: {str(e)}")
                    raise ValueError(f"No se pudo descargar el audio del vídeo de YouTube: {str(e)}")

            if not info_dict:
                raise ValueError("No se obtuvieron metadatos válidos del vídeo de YouTube.")

            video_id = info_dict.get('id', clean_id or 'unknown')
            title = info_dict.get('title', 'Canción Desconocida')
            uploader = info_dict.get('uploader') or info_dict.get('channel', 'Desconocido')
            duration = info_dict.get('duration', 0)

            if duration and duration > max_duration:
                raise ValueError(
                    f"El vídeo dura {duration}s, superando el límite máximo permitido de {max_duration}s."
                )

            # Locate downloaded audio file in temporary directory
            downloaded_files = os.listdir(temp_dir)
            if not downloaded_files:
                raise FileNotFoundError("El archivo de audio descargado no fue encontrado en memoria.")

            audio_file_path = os.path.join(temp_dir, downloaded_files[0])
            
            # Read and resample audio into mono numpy array via librosa
            logger.info(f"Loading audio file {downloaded_files[0]} at sample rate {target_sr}...")
            y, sr = librosa.load(audio_file_path, sr=target_sr, mono=True)

            metadata = {
                "video_id": video_id,
                "title": title,
                "uploader": uploader,
                "duration": float(duration) if duration else float(len(y) / sr),
                "thumbnail": info_dict.get('thumbnail', '')
            }

            return y, sr, metadata
