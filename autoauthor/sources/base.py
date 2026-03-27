"""autoauthor/sources/base.py — 데이터 소스 기본 클래스"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re


@dataclass
class TrendItem:
    """하나의 트렌드 콘텐츠 항목"""
    title: str
    content_type: str = ""       # movie/drama/anime/webtoon/show
    source: str = ""
    rank: int = 0
    score: float = 0.0           # 0~100 정규화
    metadata: dict = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)

    @property
    def normalized_title(self) -> str:
        return re.sub(r'[^가-힣a-zA-Z0-9]', '', self.title).lower()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "content_type": self.content_type,
            "source": self.source,
            "rank": self.rank,
            "score": self.score,
            "metadata": self.metadata,
            "collected_at": self.collected_at.isoformat(),
        }


class SourceUnavailableError(Exception):
    pass


class BaseTrendSource(ABC):
    name: str = "base"
    is_optional: bool = False

    @abstractmethod
    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        pass

    @abstractmethod
    async def fetch_keywords(self, title: str) -> list[str]:
        pass

    async def health_check(self) -> bool:
        try:
            results = await self.fetch_trends("movie")
            return len(results) > 0
        except Exception:
            return False
