"""autoauthor/sources/google_news_rss.py — Google News RSS (공개, 인증 불필요)"""
import aiohttp
import asyncio
import xml.etree.ElementTree as ET
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class GoogleNewsSource(BaseTrendSource):
    name = "google_news"
    is_optional = False
    RSS_URL = "https://news.google.com/rss/search"

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        queries = {
            "movie": ["한국 영화 개봉 2026", "넷플릭스 영화 신작", "박스오피스 순위"],
            "drama": ["한국 드라마 신작", "넷플릭스 드라마 2026"],
            "all": ["한국 영화 개봉", "넷플릭스 신작", "한국 드라마"],
        }
        all_items = []
        for q in queries.get(category, queries["all"]):
            items = await self._fetch_rss(q)
            all_items.extend(items)
            await asyncio.sleep(0.5)
        return self._deduplicate(all_items)

    async def fetch_keywords(self, title: str) -> list[str]:
        """뉴스 기사 제목은 형태소 분석 없이 키워드로 쓰기엔 너무 길고 불용어가 많아 (의미 없음)
        키워드 수집 단계에서는 빈 리스트를 반환하도록 수정 (트렌드 탐지에만 활용).
        """
        return []

    async def _fetch_rss(self, query: str) -> list[TrendItem]:
        params = {"q": query, "hl": "ko", "gl": "KR", "ceid": "KR:ko"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(self.RSS_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    text = await r.text()
        except Exception as e:
            raise SourceUnavailableError(f"Google News RSS 오류: {e}")

        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return []

        items = []
        for idx, el in enumerate(root.findall(".//item")[:20]):
            title = el.findtext("title", "")
            pub = el.findtext("pubDate", "")
            src = el.findtext("source", "")
            items.append(TrendItem(
                title=title, source=self.name, rank=idx + 1,
                score=max(0, 80 - idx * 3),
                metadata={"pub_date": pub, "news_source": src},
            ))
        return items

    @staticmethod
    def _deduplicate(items: list[TrendItem]) -> list[TrendItem]:
        seen: dict[str, TrendItem] = {}
        for item in items:
            key = item.normalized_title
            if key in seen:
                seen[key].score += item.score * 0.3
            else:
                seen[key] = item
        result = list(seen.values())
        result.sort(key=lambda x: x.score, reverse=True)
        return result
