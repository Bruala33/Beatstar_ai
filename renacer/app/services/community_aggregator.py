import urllib.request
import urllib.parse
import json
import ssl
import asyncio
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("community_aggregator")

# SSL context for external requests
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

class CommunityAggregator:
    """
    Agregador multifuente de mapas de ritmo comunitarios humanos:
    - osu! Mania (Mino / Catboy / Nerinyan)
    - Quaver (Quaver API)
    - Clone Hero (Chorus Encore)
    """

    @staticmethod
    def _fetch_sync(url: str, method: str = "GET", body: Optional[Dict[str, Any]] = None, timeout: int = 6) -> Optional[Any]:
        try:
            headers = DEFAULT_HEADERS.copy()
            data_bytes = None
            if body is not None:
                headers["Content-Type"] = "application/json"
                data_bytes = json.dumps(body).encode("utf-8")

            req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=timeout) as resp:
                if resp.status in (200, 201):
                    raw = resp.read().decode("utf-8", errors="ignore")
                    return json.loads(raw)
        except Exception as e:
            logger.debug(f"Error fetching {url}: {str(e)}")
            return None

    @classmethod
    async def search_osu_mania(cls, query: str) -> List[Dict[str, Any]]:
        """
        Consulta la API de osu! Mania (Catboy/Mino mirror) filtrada a modo Mania (mode=3).
        """
        encoded = urllib.parse.quote(query)
        url = f"https://catboy.best/api/v2/search?q={encoded}&mode=3"
        
        data = await asyncio.to_thread(cls._fetch_sync, url)
        if not data or not isinstance(data, list):
            return []

        results = []
        for item in data[:12]:
            try:
                set_id = item.get("id")
                title = item.get("title") or "Sin título"
                artist = item.get("artist") or "Desconocido"
                creator = item.get("creator") or (item.get("user", {}).get("username") if isinstance(item.get("user"), dict) else "osu! Mapper")
                
                # Covers / Banner
                covers = item.get("covers") or {}
                thumbnail = covers.get("card") or covers.get("cover") or f"https://assets.ppy.sh/beatmaps/{set_id}/covers/card.jpg"

                # Difficulties
                diffs = []
                beatmaps = item.get("beatmaps") or []
                for b in beatmaps:
                    if b.get("mode") == 3 or b.get("mode_int") == 3 or str(b.get("mode")) == "mania":
                        rating = round(float(b.get("difficulty_rating") or 0.0), 1)
                        diff_name = b.get("version") or f"Key {b.get('cs', 4)}"
                        keys = int(b.get("cs") or 4)
                        diffs.append({
                            "id": str(b.get("id")),
                            "name": diff_name,
                            "stars": rating,
                            "keys": keys,
                            "label": f"{diff_name} ({rating}★)"
                        })

                if not diffs and beatmaps:
                    for b in beatmaps:
                        rating = round(float(b.get("difficulty_rating") or 0.0), 1)
                        diff_name = b.get("version") or "Normal"
                        keys = int(b.get("cs") or 4)
                        diffs.append({
                            "id": str(b.get("id")),
                            "name": diff_name,
                            "stars": rating,
                            "keys": keys,
                            "label": f"{diff_name} ({rating}★)"
                        })

                diffs.sort(key=lambda d: d["stars"])

                if diffs:
                    results.append({
                        "id": f"osu_{set_id}",
                        "source": "osu",
                        "source_name": "osu! Mania",
                        "source_badge": "osu! Mania",
                        "source_color": "#ff007f",
                        "title": title,
                        "artist": artist,
                        "creator": creator,
                        "thumbnail": thumbnail,
                        "download_url": f"/api/v1/download/proxy?url={urllib.parse.quote(f'https://catboy.best/d/{set_id}', safe='')}",
                        "direct_download_url": f"https://catboy.best/d/{set_id}",
                        "fallback_download_url": f"https://api.nerinyan.moe/d/{set_id}",
                        "bpm": item.get("bpm") or 120,
                        "difficulties": diffs
                    })
            except Exception as ex:
                logger.debug(f"Error parsing osu item: {ex}")
                continue

        return results

    @classmethod
    async def search_quaver(cls, query: str) -> List[Dict[str, Any]]:
        """
        Consulta la API de Quaver filtrada a modo 4K (mode=1).
        """
        encoded = urllib.parse.quote(query)
        url = f"https://api.quavergame.com/v1/mapsets/maps/search?search={encoded}&mode=1"

        data = await asyncio.to_thread(cls._fetch_sync, url)
        if not data or not isinstance(data, dict):
            return []

        mapsets = data.get("mapsets") or []
        results = []

        for item in mapsets[:10]:
            try:
                set_id = item.get("id")
                title = item.get("title") or "Sin título"
                artist = item.get("artist") or "Desconocido"
                creator = item.get("creator_username") or "Quaver Charter"
                thumbnail = f"https://cdn.quavergame.com/mapsets/{set_id}.jpg"

                diffs = []
                maps = item.get("maps") or []
                for m in maps:
                    rating = round(float(m.get("difficulty_rating") or 0.0), 1)
                    diff_name = m.get("difficulty_name") or "Standard"
                    diffs.append({
                        "id": str(m.get("id")),
                        "name": diff_name,
                        "stars": rating,
                        "keys": 4 if m.get("game_mode") == 1 else 7,
                        "label": f"{diff_name} ({rating}★)"
                    })

                diffs.sort(key=lambda d: d["stars"])

                if diffs:
                    results.append({
                        "id": f"quaver_{set_id}",
                        "source": "quaver",
                        "source_name": "Quaver",
                        "source_badge": "Quaver",
                        "source_color": "#00f2fe",
                        "title": title,
                        "artist": artist,
                        "creator": creator,
                        "thumbnail": thumbnail,
                        "download_url": f"/api/v1/download/proxy?url={urllib.parse.quote(f'https://api.quavergame.com/d/web/mapset/{set_id}', safe='')}",
                        "direct_download_url": f"https://api.quavergame.com/d/web/mapset/{set_id}",
                        "bpm": item.get("bpm") or 120,
                        "difficulties": diffs
                    })
            except Exception as ex:
                logger.debug(f"Error parsing quaver item: {ex}")
                continue

        return results

    @classmethod
    async def search_clone_hero(cls, query: str) -> List[Dict[str, Any]]:
        """
        Consulta la API de Chorus Encore para mapas de Clone Hero (.chart / .mid / .zip).
        """
        url = "https://api.enchor.us/search"
        body = {
            "search": query,
            "page": 1,
            "source": "website"
        }

        data = await asyncio.to_thread(cls._fetch_sync, url, "POST", body)
        if not data or not isinstance(data, dict):
            return []

        items = data.get("data") or []
        results = []

        for item in items[:10]:
            try:
                chart_id = item.get("chartId") or item.get("songId")
                name = item.get("name") or "Sin título"
                artist = item.get("artist") or "Desconocido"
                charter = item.get("charter") or "Clone Hero Charter"
                drive_id = item.get("driveFileId") or item.get("parentFolderId")

                diffs = []
                diff_guitar = item.get("diff_guitar")
                if diff_guitar is not None and diff_guitar >= 0:
                    diffs.append({
                        "id": "expert",
                        "name": "Expert Single",
                        "stars": float(diff_guitar) if diff_guitar > 0 else 3.0,
                        "keys": 5,
                        "label": f"Expert ({diff_guitar}★)" if diff_guitar > 0 else "Expert"
                    })
                
                notes_data = item.get("notesData") or {}
                note_counts = notes_data.get("noteCounts") or []
                for nc in note_counts:
                    d_name = nc.get("difficulty") or "Normal"
                    if not any(d["name"].lower() == d_name.lower() for d in diffs):
                        diffs.append({
                            "id": d_name.lower(),
                            "name": d_name.capitalize(),
                            "stars": 3.0,
                            "keys": 5,
                            "label": d_name.capitalize()
                        })

                if not diffs:
                    diffs.append({
                        "id": "expert",
                        "name": "Expert",
                        "stars": 3.5,
                        "keys": 5,
                        "label": "Expert 3.5★"
                    })

                download_target = f"https://drive.google.com/uc?id={drive_id}&export=download" if drive_id else ""
                thumbnail = "https://i.ytimg.com/vi/placeholder/hqdefault.jpg"
                if item.get("albumArtMd5"):
                    thumbnail = f"https://api.enchor.us/albumart/{item.get('albumArtMd5')}"

                results.append({
                    "id": f"clonehero_{chart_id or drive_id}",
                    "source": "clonehero",
                    "source_name": "Clone Hero",
                    "source_badge": "Clone Hero",
                    "source_color": "#b142ff",
                    "title": name,
                    "artist": artist,
                    "creator": charter,
                    "thumbnail": thumbnail,
                    "download_url": f"/api/v1/download/proxy?url={urllib.parse.quote(download_target, safe='')}" if download_target else "",
                    "direct_download_url": download_target,
                    "bpm": 120,
                    "difficulties": diffs
                })
            except Exception as ex:
                logger.debug(f"Error parsing clone hero item: {ex}")
                continue

        return results

    @classmethod
    async def aggregate_search(cls, query: str) -> List[Dict[str, Any]]:
        """
        Ejecuta búsquedas paralelas cruzadas en osu! Mania, Quaver y Clone Hero.
        """
        clean_q = query.strip()
        if not clean_q:
            return []

        osu_task = asyncio.create_task(cls.search_osu_mania(clean_q))
        quaver_task = asyncio.create_task(cls.search_quaver(clean_q))
        ch_task = asyncio.create_task(cls.search_clone_hero(clean_q))

        osu_res, quaver_res, ch_res = await asyncio.gather(
            osu_task, quaver_task, ch_task, return_exceptions=True
        )

        all_results = []
        if isinstance(osu_res, list):
            all_results.extend(osu_res)
        if isinstance(quaver_res, list):
            all_results.extend(quaver_res)
        if isinstance(ch_res, list):
            all_results.extend(ch_res)

        return all_results
