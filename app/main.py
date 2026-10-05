"""Novel Scraper REST API — multi-site (novelupdates, scribblehub, royalroad)."""
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .models import SearchResponse, NovelDetail, ChaptersResponse, ChapterContent, ErrorResponse
from .sites.scribblehub import ScribbleHubAdapter
from .sites.royalroad import RoyalRoadAdapter
from .sites.novelupdates import NovelUpdatesAdapter
from . import fetcher

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="Novel Scraper API",
    description="Multi-site web novel scraper — NovelUpdates, ScribbleHub, RoyalRoad.",
    version="1.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    {"error": "rate_limited", "detail": "Too many requests, slow down."}, status_code=429))

ADAPTERS = {
    "scribblehub": ScribbleHubAdapter(),
    "royalroad": RoyalRoadAdapter(),
    "novelupdates": NovelUpdatesAdapter(),
}
ALIASES = {"sh": "scribblehub", "rr": "royalroad", "nu": "novelupdates"}


def get_adapter(site: str):
    site = ALIASES.get(site.lower(), site.lower())
    ad = ADAPTERS.get(site)
    if not ad:
        raise HTTPException(400, f"Unknown site '{site}'. Use: {', '.join(ADAPTERS)}")
    return ad


def err(e: Exception):
    msg = str(e)
    if "BLOCKED_BY_CLOUDFLARE" in msg:
        return JSONResponse({"error": "upstream_blocked",
                             "detail": "Target site blocked this server's IP (Cloudflare). Run from a clean IP."},
                            status_code=502)
    return JSONResponse({"error": "scrape_failed", "detail": msg}, status_code=502)


@app.get("/health")
def health():
    return {"ok": True, "sites": list(ADAPTERS)}


@app.get("/api/v1/search", response_model=SearchResponse)
@limiter.limit("30/minute")
def search(request: Request, q: str = Query(..., min_length=2), site: str = "all", limit: int = Query(10, le=30)):
    try:
        sites = list(ADAPTERS) if site == "all" else [get_adapter(site).site]
        results = []
        for s in sites:
            try:
                results.extend(ADAPTERS[s].search(q, limit))
            except Exception as e:
                results.append({"site": s, "id": "", "title": f"ERROR: {e}", "url": ""})
        return {"query": q, "site": site, "results": results[: limit * len(sites)]}
    except HTTPException:
        raise
    except Exception as e:
        return err(e)


@app.get("/api/v1/novel", response_model=NovelDetail)
@limiter.limit("30/minute")
def novel(request: Request, site: str, id: str):
    try:
        return get_adapter(site).novel(id)
    except HTTPException:
        raise
    except Exception as e:
        return err(e)


@app.get("/api/v1/chapters", response_model=ChaptersResponse)
@limiter.limit("20/minute")
def chapters(request: Request, site: str, novel_id: str):
    try:
        ad = get_adapter(site)
        chs = ad.chapters(novel_id)
        title = None
        try:
            title = ad.novel(novel_id).title
        except Exception:
            pass
        return {"site": ad.site, "novel_id": novel_id, "novel_title": title,
                "total": len(chs), "chapters": chs}
    except HTTPException:
        raise
    except Exception as e:
        return err(e)


@app.get("/api/v1/chapter", response_model=ChapterContent)
@limiter.limit("20/minute")
def chapter(request: Request, site: str, id: str):
    try:
        return get_adapter(site).chapter(id)
    except HTTPException:
        raise
    except Exception as e:
        return err(e)


@app.get("/api/v1/latest")
@limiter.limit("15/minute")
def latest(request: Request, site: str = "royalroad", limit: int = Query(20, le=50)):
    try:
        ad = get_adapter(site)
        return {"site": ad.site, "results": ad.latest(limit)}
    except HTTPException:
        raise
    except Exception as e:
        return err(e)


@app.post("/api/v1/cache/clear")
def cache_clear():
    fetcher.clear_cache()
    return {"ok": True}
