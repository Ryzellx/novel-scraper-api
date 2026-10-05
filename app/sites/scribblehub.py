"""ScribbleHub adapter — https://www.scribblehub.com"""
import re
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base import BaseAdapter
from ..fetcher import fetch
from ..models import SearchResult, NovelDetail, ChapterInfo, ChapterContent

BASE = "https://www.scribblehub.com"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


class ScribbleHubAdapter(BaseAdapter):
    site = "scribblehub"

    # ---------- search ----------
    def search(self, query: str, limit: int = 10):
        url = f"{BASE}/?s={quote_plus(query)}&post_type=fictionposts"
        soup = _soup(fetch(url))
        out = []
        # WP search results
        for a in soup.select(".search_main_box .search_title a, .fic_row a.fic_title, a[href*='/series/']"):
            href = a.get("href", "")
            m = re.search(r"/series/(\d+)/", href)
            if not m:
                continue
            nid = m.group(1)
            if any(r.id == nid for r in out):
                continue
            out.append(SearchResult(
                site=self.site, id=nid, title=_text(a),
                url=urljoin(BASE, href),
            ))
            if len(out) >= limit:
                break
        # fallback: generic result links
        if not out:
            for h in soup.select("h2 a, h3 a"):
                href = h.get("href", "")
                m = re.search(r"/series/(\d+)/", href)
                if m and not any(r.id == m.group(1) for r in out):
                    out.append(SearchResult(site=self.site, id=m.group(1), title=_text(h), url=urljoin(BASE, href)))
                    if len(out) >= limit:
                        break
        return out

    # ---------- novel ----------
    def _series_url(self, novel_id: str) -> str:
        if novel_id.startswith("http"):
            return novel_id
        return f"{BASE}/series/{novel_id}/"

    def novel(self, novel_id: str) -> NovelDetail:
        url = self._series_url(novel_id)
        soup = _soup(fetch(url))
        title = _text(soup.select_one(".fic_title")) or _text(soup.select_one("h1"))
        author = _text(soup.select_one(".auth_name_fic")) or _text(soup.select_one("[rel=author]"))
        cover_el = soup.select_one(".fic_image img")
        cover = cover_el.get("src") if cover_el else None
        desc = soup.select_one(".wi_fic_desc") or soup.select_one(".fic_desc") or soup.select_one("#content .entry-content")
        synopsis = _text(desc)
        genres = [_text(g) for g in soup.select(".fic_genre a, .genre a")]
        status = _text(soup.select_one(".fic_status"))
        m = re.search(r"/series/(\d+)/", url)
        nid = m.group(1) if m else novel_id
        return NovelDetail(site=self.site, id=nid, title=title, author=author or None,
                           cover=cover, synopsis=synopsis or None,
                           genres=[g for g in genres if g], status=status or None, url=url)

    # ---------- chapters ----------
    def chapters(self, novel_id: str):
        url = self._series_url(novel_id)
        soup = _soup(fetch(url))
        m = re.search(r"/series/(\d+)/", url)
        nid = m.group(1) if m else novel_id
        title = _text(soup.select_one(".fic_title"))
        out = []
        rows = soup.select("#myTable tbody tr, table.toc tbody tr, ol.toc_ol li")
        if not rows:
            rows = soup.select("a[href*='/read/']")
        for i, r in enumerate(rows):
            a = r.select_one("a") if r.name != "a" else r
            if not a:
                continue
            href = a.get("href", "")
            cm = re.search(r"/chapter/(\d+)", href)
            if not cm:
                continue
            cid = cm.group(1)
            if any(c.id == cid for c in out):
                continue
            tds = r.select("td")
            pub = _text(tds[-1]) if tds else None
            out.append(ChapterInfo(site=self.site, novel_id=nid, id=cid,
                                   title=_text(a), url=urljoin(BASE, href),
                                   published=pub, index=len(out)))
        return out

    # ---------- chapter content ----------
    def chapter(self, chapter_id: str) -> ChapterContent:
        url = chapter_id if chapter_id.startswith("http") else f"{BASE}/read/{chapter_id}/"
        soup = _soup(fetch(url))
        title = _text(soup.select_one(".chapter-title, h1.fic_title, .chp_title"))
        novel_a = soup.select_one(".fic_title a, a[href*='/series/']")
        novel_title = _text(novel_a) if novel_a else None
        novel_id = None
        if novel_a:
            mm = re.search(r"/series/(\d+)/", novel_a.get("href", ""))
            novel_id = mm.group(1) if mm else None
        body = (soup.select_one("#chp_raw") or soup.select_one(".chp_raw")
                or soup.select_one("#content .entry-content") or soup.select_one(".chapter-content"))
        html = str(body) if body else ""
        text = _text(body)
        # prev/next
        prev_id = next_id = None
        for a in soup.select("a"):
            t = _text(a).lower()
            href = a.get("href", "")
            ccm = re.search(r"/chapter/(\d+)", href)
            if not ccm:
                continue
            if "prev" in t:
                prev_id = ccm.group(1)
            elif "next" in t:
                next_id = ccm.group(1)
        cm = re.search(r"/chapter/(\d+)", url)
        cid = cm.group(1) if cm else chapter_id
        return ChapterContent(site=self.site, id=cid, title=title, novel_title=novel_title,
                              novel_id=novel_id, content_html=html, content_text=text,
                              url=url, prev_id=prev_id, next_id=next_id)
