"""autoauthor/sources/naver_suggest.py — 네이버 자동완성 비공식 API"""
import aiohttp
import asyncio
from .base import BaseTrendSource, TrendItem, SourceUnavailableError

class NaverSuggestSource(BaseTrendSource):
    name = "naver_suggest"
    is_optional = False
    URL = "https://ac.search.naver.com/nx/ac"

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        """자동완성은 트렌드 탐지보다 키워드 수집에 적합하므로 빈 리스트 반환"""
        return []

    async def fetch_keywords(self, title: str) -> list[str]:
        """네이버 검색 기반 2단계 롱테일 확장 키워드 수집"""
        # 네이버의 특성상 한국 커뮤니티나 정보성 탐색을 더 많이 함을 반영
        suffixes = ["", " 리뷰", " 줄거리", " 결말", " 출연진", " 평점",
                     " 해석", " 실화", " 원작", " 촬영지", " OST", " 논란", " 명대사", " 더쿠", " 디시", " 갤러리"]
        seeds = [f"{title}{s}" for s in suffixes]

        all_kws: set[str] = set()

        # 1단계: 시드 → 자동완성
        for seed in seeds:
            suggestions = await self._suggest(seed)
            for s in suggestions:
                if title.replace(" ", "") in s.replace(" ", ""):
                    all_kws.add(s.strip())
            await asyncio.sleep(0.3)

        # 2단계: 최상위 도출 키워드로 추가 꼬리 확장
        for kw in list(all_kws)[:5]:
            suggestions = await self._suggest(kw)
            for s in suggestions:
                if title.replace(" ", "") in s.replace(" ", ""):
                    all_kws.add(s.strip())
            await asyncio.sleep(0.3)

        return sorted(all_kws)

    async def _suggest(self, query: str) -> list[str]:
        params = {"q": query, "st": 100, "r_format": "json"}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(self.URL, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status != 200:
                        return []
                    data = await r.json(content_type=None)
                    
                    # Naver AC JSON response structure: {'items': [[['검색어1'], ...]]}
                    items = data.get('items', [[]])
                    if len(items) > 0 and isinstance(items[0], list):
                        return [item[0] for item in items[0] if isinstance(item, list) and len(item) > 0]
                    return []
        except Exception:
            return []
