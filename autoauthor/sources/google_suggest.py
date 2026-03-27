"""autoauthor/sources/google_suggest.py — 구글 자동완성 API (기존 코드 리팩토링)"""
import aiohttp
import asyncio
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class GoogleSuggestSource(BaseTrendSource):
    name = "google_suggest"
    is_optional = False
    URL = "https://suggestqueries.google.com/complete/search"

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        """자동완성은 트렌드 탐지보다 키워드 수집에 적합 → 빈 리스트 반환"""
        return []

    async def fetch_keywords(self, title: str) -> list[str]:
        """2단계 롱테일 확장 키워드 수집"""
        suffixes = ["", " 리뷰", " 줄거리", " 결말", " 출연진", " 평점",
                     " 해석", " 실화", " 원작", " 촬영지", " OST", " 논란", " 명대사"]
        seeds = [f"{title}{s}" for s in suffixes]

        all_kws: set[str] = set()

        # 1단계: 시드 → 자동완성
        for seed in seeds:
            suggestions = await self._suggest(seed)
            for s in suggestions:
                if title.replace(" ", "") in s.replace(" ", ""):
                    all_kws.add(s.strip())
            await asyncio.sleep(0.5)

        # 2단계: 상위 키워드로 추가 확장
        for kw in list(all_kws)[:5]:
            suggestions = await self._suggest(kw)
            for s in suggestions:
                if title.replace(" ", "") in s.replace(" ", ""):
                    all_kws.add(s.strip())
            await asyncio.sleep(0.5)

        return sorted(all_kws)

    async def _suggest(self, query: str) -> list[str]:
        params = {"client": "firefox", "q": query, "hl": "ko", "gl": "KR"}
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AutoAuthor/6.0)"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(self.URL, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return []
                    data = await r.json(content_type=None)
                    return data[1] if len(data) > 1 else []
        except Exception:
            return []
