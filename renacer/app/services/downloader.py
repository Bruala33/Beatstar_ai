import os
import re
import json
import logging
from typing import Dict, Any, Optional, List
import yt_dlp
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class AudioDownloader:
    """
    Handles YouTube search and metadata extraction for playlists and video lookups.
    Configured with cookies.txt detection and robust multi-tier search.
    """

    @classmethod
    def get_base_ydl_opts(cls) -> Dict[str, Any]:
        """
        Returns base yt-dlp configuration with automatic cookies.txt detection.
        """
        opts: Dict[str, Any] = {
            'format': 'ba/b/bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
        }

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
        Multi-tier YouTube search:
        - Tier 1: Direct YouTube HTML/InitialData parsing
        - Tier 2: YouTube Music API (ytmusicapi)
        - Tier 3: Invidious / Piped
        - Tier 4: yt-dlp flat search
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return []

        try:
            results = cls._search_via_youtube_html(clean_query, max_results=max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Tier 1 HTML search failed: {e}")

        try:
            results = cls._search_via_ytmusic(clean_query, max_results=max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"Tier 2 YTMusic search failed: {e}")

        try:
            results = cls._search_via_ytdlp(clean_query, max_results=max_results)
            if results:
                return results
        except Exception as e:
            logger.error(f"Tier 4 yt-dlp search failed: {e}")

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

                        title = ""
                        title_runs = vr.get("title", {}).get("runs")
                        if title_runs and isinstance(title_runs, list):
                            title = "".join(run.get("text", "") for run in title_runs)
                        elif vr.get("title", {}).get("simpleText"):
                            title = vr.get("title", {}).get("simpleText")

                        uploader = ""
                        owner_runs = vr.get("ownerText", {}).get("runs")
                        if owner_runs and isinstance(owner_runs, list):
                            uploader = "".join(run.get("text", "") for run in owner_runs)
                        elif vr.get("shortBylineText", {}).get("runs"):
                            uploader = "".join(run.get("text", "") for run in vr.get("shortBylineText", {}).get("runs", []))

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
