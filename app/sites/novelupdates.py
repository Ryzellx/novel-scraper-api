"""NovelUpdates adapter — https://www.novelupdates.com"""
import re
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base import BaseAdapter
from ..fetcher import fetch
from ..models import SearchResult, NovelDetail, ChapterInfo, ChapterContent

BASE = "https://www.novelupdates.com"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


class NovelUpdatesAdapter(BaseAdapter):
    site = "novelupdates"

    def search(self, query: str, limit: int = 10):
        url = f"{BASE}/series-finder/?sf=1&sh={quote_plus(query)}&sort=srel&order=desc"
        soup = _soup(fetch(url))
        out = []
        for a in soup.select(".search_title a, a[href*='/series/']"):
            href = a.get("href", "")
            m = re.search(r"/series/([^/]+)/?", href)
            if not m or "/series-finder" in href:
                continue
            sid = m.group(1)
            if any(r.id == sid for r in out):
                continue
            out.append(SearchResult(site=self.site, id=sid, title=_text(a), url=urljoin(BASE, href)))
            if len(out) >= limit:
                break
        return out

    def _series_url(self, novel_id: str) -> str:
        return novel_id if novel_id.startswith("http") else f"{BASE}/series/{novel_id}/"

    def novel(self, novel_id: str) -> NovelDetail:
        url = self._series_url(novel_id)
        soup = _soup(fetch(url))
        title = _text(soup.select_one(".seriestitlenu"))
        author = _text(soup.select_one("#showauthors"))
        cover_el = soup.select_one(".seriesimg img")
        cover = cover_el.get("src") if cover_el else None
        desc = soup.select_one("#editdescription")
        synopsis = _text(desc)
        genres = [_text(g) for g in soup.select("#seriesgenre a")]
        tags = [_text(t) for t in soup.select("#showtags a, .seriestag a")]
        status = _text(soup.select_one("#editstatus"))
        m = re.search(r"/series/([^/]+)/?", url)
        nid = m.group(1) if m else novel_id
        return NovelDetail(site=self.site, id=nid, title=title, author=author or None,
                           cover=cover, synopsis=synopsis or None,
                           genres=[g for g in genres if g], tags=[t for t in tags if t],
                           status=status or None, url=url)

    def chapters(self, novel_id: str):
        # NU lists chapter links (often to translator sites); return what exists
        url = self._series_url(novel_id)
        soup = _soup(fetch(url))
        m = re.search(r"/series/([^/]+)/?", url)
        nid = m.group(1) if m else novel_id
        title = _text(soup.select_one(".seriestitlenu"))
        out = []
        for a in soup.select("#myTable a, .l-chapter a, #chapterlist a"):
            href = a.get("href", "")
            if not href or href.startswith("#"):
                continue
            cid = re.sub(r"\W+", "_", href)[-40:]
            if any(c.id == cid for c in out):
                continue
            out.append(ChapterInfo(site=self.site, novel_id=nid, id=cid,
                                   title=_text(a) or href, url=urljoin(BASE, href),
                                   index=len(out)))
        return out

    def chapter(self, chapter_id: str) -> ChapterContent:
        # NU chapters usually link out; fetch whatever URL is given
        url = chapter_id if chapter_id.startswith("http") else f"{BASE}/{chapter_id}"
        soup = _soup(fetch(url))
        title = _text(soup.select_one("h1, .entry-title"))
        body = (soup.select_one("#content .entry-content, .entry-content, #chapter-content, .chapter-inner")
                or soup.select_one("article"))
        html = str(body) if body else ""
        text = _text(body)
        return ChapterContent(site=self.site, id=chapter_id, title=title,
                              content_html=html, content_text=text, url=url)

    def latest(self, limit: int = 20):
        url = f"{BASE}/"
        soup = _soup(fetch(url))
        out = []
        for a in soup.select("a[href*='/series/']"):
            href = a.get("href", "")
            m = re.search(r"/series/([^/]+)/?", href)
            if not m:
                continue
            sid = m.group(1)
            if any(r.id == sid for r in out):
                continue
            out.append(SearchResult(site=self.site, id=sid, title=_text(a), url=urljoin(BASE, href)))
            if len(out) >= limit:
                break
        return out
