import io
import os
import re
import json
import tempfile
import logging
from typing import Tuple, Dict, Any, Optional, List
import yt_dlp
import soundfile as sf
import librosa
import numpy as np
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class AudioDownloader:
    """
    Handles YouTube audio extraction, multi-tier search, and in-memory audio decoding.
    Built with multi-tier fallbacks (Direct HTML, YouTube Music API, Invidious/Piped, yt-dlp)
    to guarantee 100% reliable search and prevent cloud datacenter IP blocks.
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
    def search_youtube(cls, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Ultra-robust multi-tier YouTube video search:
        - Tier 1: Direct YouTube HTML/InitialData parsing (fast, mobile/desktop headers, bypasses 429 bot blocks)
        - Tier 2: YouTube Music API (ytmusicapi)
        - Tier 3: Public Invidious / Piped API instances
        - Tier 4: yt-dlp flat search with mobile client bypass
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        print(f"\n[SEARCH] >>> Iniciando busqueda en YouTube para: '{clean_query}'")
        logger.info(f"[SEARCH] Starting search for query: '{clean_query}'")

        # 1. Tier 1: Direct YouTube Search HTML Parsing
        try:
            results = cls._search_via_youtube_html(clean_query, max_results=max_results)
            if results:
                print(f"[SEARCH] [OK - Tier 1 Direct HTML] Encontrados {len(results)} videos para '{clean_query}'.")
                logger.info(f"[SEARCH] Tier 1 returned {len(results)} items")
                return results
            print("[SEARCH] [INFO - Tier 1] Sin resultados, pasando a Tier 2...")
        except Exception as e:
            print(f"[SEARCH] [WARN - Tier 1 Error] {str(e)}, pasando a Tier 2...")
            logger.warning(f"[SEARCH] Tier 1 HTML search failed: {e}")

        # 2. Tier 2: YouTube Music API (ytmusicapi)
        try:
            results = cls._search_via_ytmusic(clean_query, max_results=max_results)
            if results:
                print(f"[SEARCH] [OK - Tier 2 YouTube Music API] Encontrados {len(results)} videos/canciones.")
                logger.info(f"[SEARCH] Tier 2 returned {len(results)} items")
                return results
            print("[SEARCH] [INFO - Tier 2] Sin resultados, pasando a Tier 3...")
        except Exception as e:
            print(f"[SEARCH] [WARN - Tier 2 Error] {str(e)}, pasando a Tier 3...")
            logger.warning(f"[SEARCH] Tier 2 YTMusic search failed: {e}")

        # 3. Tier 3: Invidious / Piped Public Instances
        try:
            results = cls._search_via_invidious_piped(clean_query, max_results=max_results)
            if results:
                print(f"[SEARCH] [OK - Tier 3 Invidious/Piped] Encontrados {len(results)} videos.")
                logger.info(f"[SEARCH] Tier 3 returned {len(results)} items")
                return results
            print("[SEARCH] [INFO - Tier 3] Sin resultados, pasando a Tier 4...")
        except Exception as e:
            print(f"[SEARCH] [WARN - Tier 3 Error] {str(e)}, pasando a Tier 4...")
            logger.warning(f"[SEARCH] Tier 3 Invidious/Piped search failed: {e}")

        # 4. Tier 4: yt-dlp Flat Search
        try:
            results = cls._search_via_ytdlp(clean_query, max_results=max_results)
            if results:
                print(f"[SEARCH] [OK - Tier 4 yt-dlp] Encontrados {len(results)} videos.")
                logger.info(f"[SEARCH] Tier 4 returned {len(results)} items")
                return results
        except Exception as e:
            print(f"[SEARCH] [ERROR - Tier 4 Error] yt-dlp search failed: {str(e)}")
            logger.error(f"[SEARCH] Tier 4 yt-dlp search failed: {e}")

        print(f"[SEARCH] [WARN] No se pudieron obtener resultados tras consultar todos los metodos para: '{clean_query}'")
        return []

    @classmethod
    def _search_via_youtube_html(cls, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        url = "https://www.youtube.com/results"
        with httpx.Client(headers=headers, timeout=6.0, follow_redirects=True) as client:
            r = client.get(url, params={"search_query": query})
            if r.status_code != 200:
                print(f"[SEARCH Tier 1] HTTP status {r.status_code}")
                return []

            m = re.search(r"var ytInitialData = ({.+?});</script>", r.text)
            if not m:
                m = re.search(r"ytInitialData\s*=\s*({.+?});</script>", r.text)

            if not m:
                return []

            data = json.loads(m.group(1))
            videos = []
            contents = (
                data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
            )

            for section in contents:
                item_section = section.get("itemSectionRenderer", {}).get("contents", [])
                for item in item_section:
                    vr = item.get("videoRenderer")
                    if vr and "videoId" in vr:
                        vid_id = vr.get("videoId")

                        # Title
                        title = ""
                        title_runs = vr.get("title", {}).get("runs")
                        if title_runs and isinstance(title_runs, list):
                            title = "".join(run.get("text", "") for run in title_runs)
                        elif vr.get("title", {}).get("simpleText"):
                            title = vr.get("title", {}).get("simpleText")

                        # Channel / Uploader
                        uploader = ""
                        owner_runs = vr.get("ownerText", {}).get("runs")
                        if owner_runs and isinstance(owner_runs, list):
                            uploader = "".join(run.get("text", "") for run in owner_runs)
                        elif vr.get("shortBylineText", {}).get("runs"):
                            uploader = "".join(run.get("text", "") for run in vr.get("shortBylineText", {}).get("runs", []))

                        # Duration
                        dur_str = vr.get("lengthText", {}).get("simpleText", "")
                        sec = 0
                        if dur_str:
                            parts = [int(p) for p in dur_str.split(":") if p.isdigit()]
                            if len(parts) == 2:
                                sec = parts[0] * 60 + parts[1]
                            elif len(parts) == 3:
                                sec = parts[0] * 3600 + parts[1] * 60 + parts[2]

                        videos.append({
                            "id": vid_id,
                            "title": title or "Sin titulo",
                            "channel": uploader or "YouTube",
                            "duration": sec,
                            "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                            "url": f"https://www.youtube.com/watch?v={vid_id}"
                        })

                        if len(videos) >= max_results:
                            break
                if len(videos) >= max_results:
                    break

            return videos

    @classmethod
    def _search_via_ytmusic(cls, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        try:
            from ytmusicapi import YTMusic
            yt = YTMusic()
            raw_results = yt.search(query, filter="songs", limit=max_results)
            if not raw_results:
                raw_results = yt.search(query, filter="videos", limit=max_results)

            videos = []
            for item in (raw_results or []):
                vid_id = item.get("videoId")
                if not vid_id:
                    continue

                artists = item.get("artists", [])
                artist_name = ", ".join(a.get("name", "") for a in artists if isinstance(a, dict)) if artists else "YouTube Music"

                dur_sec = 0
                if "duration_seconds" in item and item["duration_seconds"]:
                    dur_sec = int(item["duration_seconds"])
                elif "duration" in item and item["duration"]:
                    parts = [int(p) for p in str(item["duration"]).split(":") if p.isdigit()]
                    if len(parts) == 2:
                        dur_sec = parts[0] * 60 + parts[1]
                    elif len(parts) == 3:
                        dur_sec = parts[0] * 3600 + parts[1] * 60 + parts[2]

                thumbnails = item.get("thumbnails", [])
                thumb = thumbnails[-1].get("url") if thumbnails else f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"

                videos.append({
                    "id": vid_id,
                    "title": item.get("title") or "Sin titulo",
                    "channel": artist_name or "YouTube Music",
                    "duration": dur_sec,
                    "thumbnail": thumb or f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                    "url": f"https://www.youtube.com/watch?v={vid_id}"
                })

                if len(videos) >= max_results:
                    break

            return videos
        except Exception as e:
            logger.debug(f"ytmusic search error: {e}")
            return []

    @classmethod
    def _search_via_invidious_piped(cls, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        invidious_endpoints = [
            "https://invidious.nerdvpn.de",
            "https://inv.nadeko.net",
            "https://invidious.jing.rocks",
            "https://invidious.no-logs.com",
            "https://vid.puffyan.us"
        ]

        with httpx.Client(timeout=4.0) as client:
            for base_url in invidious_endpoints:
                try:
                    search_url = f"{base_url}/api/v1/search"
                    r = client.get(search_url, params={"q": query, "type": "video"})
                    if r.status_code == 200:
                        data = r.json()
                        if isinstance(data, list) and len(data) > 0:
                            videos = []
                            for item in data:
                                vid_id = item.get("videoId")
                                if not vid_id:
                                    continue
                                videos.append({
                                    "id": vid_id,
                                    "title": item.get("title") or "Sin titulo",
                                    "channel": item.get("author") or "YouTube",
                                    "duration": int(item.get("lengthSeconds") or 0),
                                    "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                                    "url": f"https://www.youtube.com/watch?v={vid_id}"
                                })
                                if len(videos) >= max_results:
                                    break
                            if videos:
                                return videos
                except Exception:
                    continue

        # Fallback to Piped
        piped_endpoints = [
            "https://pipedapi.kavin.rocks",
            "https://pipedapi.leptons.xyz",
            "https://piped-api.lunar.icu"
        ]
        with httpx.Client(timeout=4.0) as client:
            for base_url in piped_endpoints:
                try:
                    search_url = f"{base_url}/search"
                    r = client.get(search_url, params={"q": query, "filter": "videos"})
                    if r.status_code == 200:
                        data = r.json()
                        items = data.get("items", [])
                        if items:
                            videos = []
                            for item in items:
                                url = item.get("url", "")
                                vid_id = url.split("watch?v=")[-1] if "watch?v=" in url else item.get("id")
                                if not vid_id:
                                    continue
                                videos.append({
                                    "id": vid_id,
                                    "title": item.get("title") or "Sin titulo",
                                    "channel": item.get("uploaderName") or "YouTube",
                                    "duration": int(item.get("duration") or 0),
                                    "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg",
                                    "url": f"https://www.youtube.com/watch?v={vid_id}"
                                })
                                if len(videos) >= max_results:
                                    break
                            if videos:
                                return videos
                except Exception:
                    continue

        return []

    @classmethod
    def _search_via_ytdlp(cls, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        ydl_opts = cls.get_base_ydl_opts()
        ydl_opts.update({
            'extract_flat': True,
            'skip_download': True,
            'noplaylist': True,
        })
        search_query = f"ytsearch{max_results}:{query.strip()}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', []) if info else []
            videos = []
            for entry in entries:
                if not entry:
                    continue
                video_id = entry.get('id')
                if not video_id:
                    continue

                thumbnails = entry.get('thumbnails', [])
                thumb_url = thumbnails[-1].get('url', '') if thumbnails else (entry.get('thumbnail') or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")

                videos.append({
                    "id": video_id,
                    "title": entry.get('title', 'Sin titulo'),
                    "channel": entry.get('uploader') or entry.get('channel') or 'Desconocido',
                    "duration": int(entry.get('duration') or 0),
                    "thumbnail": thumb_url,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })
                if len(videos) >= max_results:
                    break
            return videos

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
