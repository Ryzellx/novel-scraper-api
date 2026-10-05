"""RoyalRoad adapter — https://www.royalroad.com"""
import re
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from .base import BaseAdapter
from ..fetcher import fetch
from ..models import SearchResult, NovelDetail, ChapterInfo, ChapterContent

BASE = "https://www.royalroad.com"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def _text(el) -> str:
    return el.get_text(" ", strip=True) if el else ""


class RoyalRoadAdapter(BaseAdapter):
    site = "royalroad"

    def search(self, query: str, limit: int = 10):
        url = f"{BASE}/fictions/search?title={quote_plus(query)}"
        soup = _soup(fetch(url))
        out = []
        for h in soup.select(".fiction-list-item h2 a, h2.fiction-title a"):
            href = h.get("href", "")
            m = re.search(r"/fiction/(\d+)/", href)
            if not m or any(r.id == m.group(1) for r in out):
                continue
            author_el = h.find_parent("div", class_="fiction-list-item")
            author = _text(author_el.select_one(".author")) if author_el else None
            out.append(SearchResult(site=self.site, id=m.group(1), title=_text(h),
                                    author=author or None, url=urljoin(BASE, href)))
            if len(out) >= limit:
                break
        return out

    def _fic_url(self, novel_id: str) -> str:
        return novel_id if novel_id.startswith("http") else f"{BASE}/fiction/{novel_id}"

    def novel(self, novel_id: str) -> NovelDetail:
        url = self._fic_url(novel_id)
        soup = _soup(fetch(url))
        title = _text(soup.select_one("h1.fic-title, .fic-title h1, h1[property='name']"))
        author = _text(soup.select_one(".author a, [itemprop='author'] a, .fic-header a[href*='/profile/']"))
        cover_el = soup.select_one(".cover-art-container img, img.cover, .fic-cover img")
        cover = cover_el.get("src") if cover_el else None
        desc = soup.select_one(".description, [itemprop='description'], .fic-description")
        synopsis = _text(desc)
        genres = [_text(g) for g in soup.select(".tags a, .fiction-tags a, [property='genre']")]
        status = _text(soup.select_one(".fic-status, .status"))
        m = re.search(r"/fiction/(\d+)", url)
        nid = m.group(1) if m else novel_id
        return NovelDetail(site=self.site, id=nid, title=title, author=author or None,
                           cover=cover, synopsis=synopsis or None,
                           genres=[g for g in genres if g], status=status or None, url=url)

    def chapters(self, novel_id: str):
        url = self._fic_url(novel_id)
        soup = _soup(fetch(url))
        m = re.search(r"/fiction/(\d+)", url)
        nid = m.group(1) if m else novel_id
        title = _text(soup.select_one("h1.fic-title"))
        out = []
        for tr in soup.select("#chapters tbody tr"):
            a = tr.select_one("td:first-child a")
            if not a:
                continue
            href = a.get("href", "")
            cm = re.search(r"/chapter/(\d+)", href)
            if not cm or any(c.id == cm.group(1) for c in out):
                continue
            tds = tr.select("td")
            pub = _text(tds[1]) if len(tds) > 1 else None
            out.append(ChapterInfo(site=self.site, novel_id=nid, id=cm.group(1),
                                   title=_text(a), url=urljoin(BASE, href),
                                   published=pub, index=len(out)))
        return out

    def chapter(self, chapter_id: str) -> ChapterContent:
        url = chapter_id if chapter_id.startswith("http") else f"{BASE}/fiction/chapter/{chapter_id}"
        # chapter_id may be "fid/cid" — build proper URL when possible
        soup = _soup(fetch(url))
        title = _text(soup.select_one("h1.fic-title, .chapter-title h1, h1"))
        body = (soup.select_one(".chapter-inner") or soup.select_one("#chapter-content")
                or soup.select_one(".chapter-content"))
        html = str(body) if body else ""
        text = _text(body)
        # prev/next
        prev_id = next_id = None
        for a in soup.select(".nav-buttons a, a.nav-btn, ul.list-inline a"):
            t = _text(a).lower()
            href = a.get("href", "")
            cm = re.search(r"/chapter/(\d+)", href)
            if not cm:
                continue
            if "previous" in t or "prev" in t:
                prev_id = cm.group(1)
            elif "next" in t:
                next_id = cm.group(1)
        cm = re.search(r"/chapter/(\d+)", url)
        cid = cm.group(1) if cm else chapter_id
        # novel link from breadcrumb
        novel_title = novel_id = None
        ba = soup.select_one("a[href*='/fiction/']")
        if ba:
            novel_title = _text(ba)
            mm = re.search(r"/fiction/(\d+)", ba.get("href", ""))
            novel_id = mm.group(1) if mm else None
        return ChapterContent(site=self.site, id=cid, title=title, novel_title=novel_title,
                              novel_id=novel_id, content_html=html, content_text=text,
                              url=url, prev_id=prev_id, next_id=next_id)

    def latest(self, limit: int = 20):
        url = f"{BASE}/fictions/latest-updates"
        soup = _soup(fetch(url))
        out = []
        for h in soup.select(".fiction-list-item h2 a"):
            href = h.get("href", "")
            m = re.search(r"/fiction/(\d+)/", href)
            if not m or any(r.id == m.group(1) for r in out):
                continue
            out.append(SearchResult(site=self.site, id=m.group(1), title=_text(h), url=urljoin(BASE, href)))
            if len(out) >= limit:
                break
        return out
