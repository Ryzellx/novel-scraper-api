"""Base adapter interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import SearchResult, NovelDetail, ChapterInfo, ChapterContent


class BaseAdapter(ABC):
    site: str = ""

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[SearchResult]: ...

    @abstractmethod
    def novel(self, novel_id: str) -> NovelDetail: ...

    @abstractmethod
    def chapters(self, novel_id: str) -> List[ChapterInfo]: ...

    @abstractmethod
    def chapter(self, chapter_id: str) -> ChapterContent: ...

    def latest(self, limit: int = 20) -> List[SearchResult]:
        raise NotImplementedError("latest not implemented for " + self.site)
