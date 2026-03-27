"""autoauthor/sources/naver_datalab.py — 네이버 DataLab 검색어 트렌드 API
POST https://openapi.naver.com/v1/datalab/search
제한: 25,000 calls/day, 5 keyword groups/req, 20 keywords/group
"""
from typing import Optional, Union
import aiohttp
import asyncio
from datetime import datetime, timedelta
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class NaverDataLabSource(BaseTrendSource):
    name = "naver_datalab"
    is_optional = False

    API_URL = "https://openapi.naver.com/v1/datalab/search"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
            "Content-Type": "application/json",
        }

    async def fetch_trends(self, category: str = "movie", seed_titles: Optional[list[str]] = None) -> list[TrendItem]:
        """시드 키워드 목록의 검색량 추이를 비교하여 급상승 콘텐츠 탐지.
        seed_titles가 없으면 TrendDetector에서 TMDB 결과를 주입받아야 함."""
        if not seed_titles:
            return []

        results = []
        for batch in _chunk(seed_titles, 5):
            groups = [{"groupName": t, "keywords": [t]} for t in batch]
            items = await self._call_api(groups)
            results.extend(items)
            await asyncio.sleep(0.3)

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    async def fetch_keywords(self, title: str) -> list[str]:
        """작품명 + 접미사 조합의 검색량 확인 → 수요 있는 키워드 반환"""
        suffixes = ["", " 리뷰", " 줄거리", " 결말", " 평점", " 해석", " 실화", " 원작", " 출연진"]
        groups = [{"groupName": f"{title}{s}", "keywords": [f"{title}{s}"]} for s in suffixes]

        keywords_with_demand = []
        for batch in _chunk(groups, 5):
            items = await self._call_api(batch)
            for item in items:
                if item.score > 5:
                    keywords_with_demand.append(item.title)
            await asyncio.sleep(0.3)

        return keywords_with_demand

    async def _call_api(self, keyword_groups: list[dict]) -> list[TrendItem]:
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        body = {
            "startDate": start,
            "endDate": end,
            "timeUnit": "date",
            "keywordGroups": keyword_groups,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.API_URL, json=body, headers=self._headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise SourceUnavailableError(f"Naver DataLab HTTP {resp.status}: {text[:200]}")
                    data = await resp.json()
        except aiohttp.ClientError as e:
            raise SourceUnavailableError(f"Naver DataLab 연결 오류: {e}")

        results = []
        for group in data.get("results", []):
            title = group.get("title", "")
            ratios = [d["ratio"] for d in group.get("data", []) if "ratio" in d]
            if not ratios:
                continue

            # 최근 7일 vs 이전 23일 → 급상승률 계산
            if len(ratios) >= 14:
                recent = sum(ratios[-7:]) / 7
                prev = sum(ratios[:-7]) / max(len(ratios) - 7, 1)
                surge = recent / max(prev, 0.01)
                score = min(100, recent * min(surge, 5))
            else:
                score = sum(ratios) / max(len(ratios), 1)

            results.append(TrendItem(
                title=title,
                source=self.name,
                score=round(score, 1),
                metadata={"daily_ratios_7d": ratios[-7:], "surge_ratio": round(surge if len(ratios) >= 14 else 1.0, 2)},
            ))

        return results

    async def health_check(self) -> bool:
        try:
            items = await self._call_api([{"groupName": "테스트", "keywords": ["네이버"]}])
            return True
        except Exception:
            return False


def _chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]
