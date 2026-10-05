"""Pydantic models for the Novel Scraper API."""
from pydantic import BaseModel, Field
from typing import Optional, List


class SearchResult(BaseModel):
    site: str
    id: str = Field(description="Site-specific novel ID or slug")
    title: str
    author: Optional[str] = None
    cover: Optional[str] = None
    url: str
    extra: dict = {}


class NovelDetail(BaseModel):
    site: str
    id: str
    title: str
    author: Optional[str] = None
    cover: Optional[str] = None
    synopsis: Optional[str] = None
    genres: List[str] = []
    tags: List[str] = []
    status: Optional[str] = None
    url: str
    extra: dict = {}


class ChapterInfo(BaseModel):
    site: str
    novel_id: str
    id: str = Field(description="Site-specific chapter ID")
    title: str
    url: str
    published: Optional[str] = None
    index: Optional[int] = None


class ChapterContent(BaseModel):
    site: str
    id: str
    title: str
    novel_title: Optional[str] = None
    novel_id: Optional[str] = None
    content_html: str
    content_text: str
    url: str
    prev_id: Optional[str] = None
    next_id: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    site: str
    results: List[SearchResult]


class ChaptersResponse(BaseModel):
    site: str
    novel_id: str
    novel_title: Optional[str] = None
    total: int
    chapters: List[ChapterInfo]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
