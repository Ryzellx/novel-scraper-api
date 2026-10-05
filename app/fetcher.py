"""HTTP fetcher with browser-like headers, retries, and in-memory cache."""
import os
# sanitize broken no_proxy (IPv6 brackets crash httpx) — see AGENTS.md
os.environ["no_proxy"] = os.environ["NO_PROXY"] = "localhost,127.0.0.1"
import time
import hashlib
import httpx
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

_cache: dict = {}
CACHE_TTL = 600  # 10 minutes

# politeness: min delay between requests to the same domain
_last_hit: dict = {}
POLITE_DELAY = 1.0


def _key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _polite_wait(url: str):
    from urllib.parse import urlparse
    dom = urlparse(url).netloc
    now = time.time()
    last = _last_hit.get(dom, 0)
    wait = POLITE_DELAY - (now - last)
    if wait > 0:
        time.sleep(wait)
    _last_hit[dom] = time.time()


def fetch(url: str, timeout: int = 25, use_cache: bool = True) -> str:
    """Fetch a URL, return HTML text. Raises RuntimeError on block/failure."""
    if use_cache:
        k = _key(url)
        hit = _cache.get(k)
        if hit and time.time() - hit["ts"] < CACHE_TTL:
            return hit["html"]

    _polite_wait(url)
    last_err = None
    for attempt in range(2):
        try:
            with httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True, http2=False) as c:
                r = c.get(url)
                if r.status_code == 403:
                    body = r.text[:300].lower()
                    if "cloudflare" in body or "attention required" in body or "just a moment" in body:
                        raise RuntimeError("BLOCKED_BY_CLOUDFLARE")
                    raise RuntimeError(f"HTTP_403_FORBIDDEN")
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP_{r.status_code}")
                html = r.text
                if use_cache:
                    _cache[_key(url)] = {"ts": time.time(), "html": html}
                    if len(_cache) > 500:
                        _cache.pop(next(iter(_cache)))
                return html
        except RuntimeError:
            raise
        except Exception as e:
            last_err = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"FETCH_FAILED: {last_err}")


def clear_cache():
    _cache.clear()
