import os
import ssl
import urllib.request
import urllib.parse
import logging
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.services.community_aggregator import CommunityAggregator
from app.api.endpoints.playlists import router as playlists_router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("beatstar_api")

app = FastAPI(
    title="Beatstar Community Rhythm Engine",
    version="3.0.0",
    description="Motor rítmico web fijo a 3 carriles con agregador multifuente de mapas comunitarios (osu! Mania, Quaver, Clone Hero)."
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

# SSL context for outbound proxy requests
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


@app.get("/api/v1/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Verifica el estado del servidor y los parámetros de configuración.
    """
    return {
        "status": "healthy",
        "service": "Beatstar Community Rhythm Engine",
        "version": "3.0.0",
        "num_lanes": 3,
        "sources": ["osu! Mania", "Quaver", "Clone Hero"]
    }


@app.get("/api/search", tags=["Search"], summary="Búsqueda unificada comunitaria")
@app.get("/api/v1/search", tags=["Search"], summary="Búsqueda unificada comunitaria")
@app.get("/api/v1/search/community", tags=["Search"], summary="Búsqueda unificada en osu! Mania, Quaver y Clone Hero")
async def search_community_beatmaps(q: str = Query(..., min_length=1)):
    """
    Consulta en paralelo las bases de datos de mapas comunitarios:
    - osu! Mania (Mino / Catboy / Nerinyan)
    - Quaver (Quaver API)
    - Clone Hero (Chorus Encore)
    """
    if not q or not q.strip():
        return []
    try:
        results = await CommunityAggregator.aggregate_search(query=q.strip())
        return results
    except Exception as e:
        logger.exception(f"Error executing community search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al buscar mapas comunitarios: {str(e)}"
        )


@app.get("/api/v1/download/proxy", tags=["Download Proxy"], summary="Proxy de descarga para evitar problemas de CORS")
async def proxy_download(url: str = Query(..., description="URL directa del archivo a descargar (.osz, .qp, .zip)")):
    """
    Descarga y retransmite paquetes de beatmaps (.osz, .qp, .zip) al navegador cliente,
    garantizando compatibilidad total con JSZip y evitando restricciones de CORS.
    """
    target_url = urllib.parse.unquote(url).strip()
    if not target_url or not target_url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL de descarga inválida.")

    # List of fallback domains for osu beatmaps if primary fails
    fallback_urls = []
    if "catboy.best/d/" in target_url:
        set_id = target_url.split("catboy.best/d/")[-1].split("?")[0]
        fallback_urls = [
            target_url,
            f"https://osu.direct/d/{set_id}",
            f"https://api.nerinyan.moe/d/{set_id}",
            f"https://beatconnect.io/b/{set_id}"
        ]
    elif "api.nerinyan.moe/d/" in target_url:
        set_id = target_url.split("api.nerinyan.moe/d/")[-1].split("?")[0]
        fallback_urls = [
            target_url,
            f"https://catboy.best/d/{set_id}",
            f"https://osu.direct/d/{set_id}",
            f"https://beatconnect.io/b/{set_id}"
        ]
    else:
        fallback_urls = [target_url]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    last_error = None
    for try_url in fallback_urls:
        try:
            req = urllib.request.Request(try_url, headers=headers)
            resp = urllib.request.urlopen(req, context=ssl_ctx, timeout=25)
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            data = resp.read()

            if len(data) > 500 and resp.status == 200:
                # Determine file extension/name
                filename = "beatmap.zip"
                if ".osz" in try_url or "osu" in content_type:
                    filename = "beatmap.osz"
                elif ".qp" in try_url:
                    filename = "beatmap.qp"

                return Response(
                    content=data,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f'attachment; filename="{filename}"',
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "public, max-age=86400"
                    }
                )
        except Exception as e:
            last_error = e
            logger.warning(f"Proxy download attempt failed for {try_url}: {e}")
            continue

    raise HTTPException(
        status_code=502,
        detail=f"No se pudo descargar el paquete desde el servidor remoto: {str(last_error)}"
    )


@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
async def serve_ui():
    """
    Sirve la interfaz web interactiva del juego de ritmo Beatstar.
    """
    html_path = os.path.join(static_dir, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Beatstar Community Rhythm Player</h1><p>Visita <a href='/docs'>/docs</a> para la API.</p>")
