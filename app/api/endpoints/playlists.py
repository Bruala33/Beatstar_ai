import os
import re
import json
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import yt_dlp

try:
    from ytmusicapi import YTMusic
    YTMUSIC_AVAILABLE = True
except ImportError:
    YTMUSIC_AVAILABLE = False

router = APIRouter()

# In-memory auth session state
_ytm_client: Optional[Any] = None

def get_ytmusic():
    global _ytm_client
    if not YTMUSIC_AVAILABLE:
        return None
    if _ytm_client is None:
        try:
            _ytm_client = YTMusic()
        except Exception:
            _ytm_client = None
    return _ytm_client

class ImportUrlRequest(BaseModel):
    url: str

@router.get("/ytmusic/status")
async def get_ytmusic_status():
    return {
        "available": YTMUSIC_AVAILABLE,
        "mode": "public"
    }

@router.post("/ytmusic/import_url")
async def import_playlist_by_url(req: ImportUrlRequest):
    """
    Extracts tracks from any YouTube or YouTube Music playlist URL or ID using yt-dlp.
    """
    url_or_id = req.url.strip()
    if not url_or_id:
        raise HTTPException(status_code=400, detail="Por favor proporciona una URL o ID de playlist.")

    playlist_id_match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url_or_id)
    playlist_id = playlist_id_match.group(1) if playlist_id_match else url_or_id

    target_url = f"https://www.youtube.com/playlist?list={playlist_id}" if not url_or_id.startswith("http") else url_or_id

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True
    }

    try:
        def fetch():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(target_url, download=False)

        info = await asyncio.to_thread(fetch)
        if not info:
            raise HTTPException(status_code=404, detail="No se pudo obtener información de la playlist.")

        entries = info.get('entries', [])
        title = info.get('title') or "Playlist Importada"

        tracks = []
        for entry in entries:
            if not entry:
                continue
            vid_id = entry.get('id')
            if not vid_id:
                continue
            tracks.append({
                "id": vid_id,
                "title": entry.get('title') or "Sin título",
                "artists": [entry.get('uploader') or entry.get('channel') or "YouTube"],
                "duration_seconds": int(entry.get('duration') or 0),
                "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
            })

        return {
            "id": playlist_id,
            "title": title,
            "item_count": len(tracks),
            "tracks": tracks
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al importar playlist: {str(e)}")

@router.get("/ytmusic/search")
async def search_ytmusic_playlists(q: str = Query(..., min_length=1)):
    """
    Search for public playlists in YouTube Music.
    """
    yt = get_ytmusic()
    if not yt:
        return []

    try:
        def do_search():
            return yt.search(query=q, filter="playlists", limit=10)
        
        results = await asyncio.to_thread(do_search)
        playlists = []
        for item in results:
            playlists.append({
                "id": item.get("browseId") or item.get("playlistId"),
                "title": item.get("title"),
                "author": item.get("author") or (item.get("artists")[0]["name"] if item.get("artists") else "YouTube"),
                "item_count": item.get("itemCount") or item.get("count"),
                "thumbnail": item.get("thumbnails")[-1]["url"] if item.get("thumbnails") else ""
            })
        return playlists
    except Exception as e:
        return []

@router.get("/ytmusic/{playlist_id}")
async def get_ytmusic_playlist_tracks(playlist_id: str):
    """
    Retrieve tracks from a playlist ID.
    """
    return await import_playlist_by_url(ImportUrlRequest(url=playlist_id))
