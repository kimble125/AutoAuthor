"""autoauthor/sources/tmdb.py — TMDB API v3
메타데이터 + 시드 키워드 자동 생성 + 유사 작품 크로스 키워드
"""
from typing import Optional, Union
import aiohttp
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class TMDBSource(BaseTrendSource):
    name = "tmdb"
    is_optional = False
    BASE = "https://api.themoviedb.org/3"

    def __init__(self, api_key: str, read_access_token: str):
        self.api_key = api_key
        self._headers = {
            "Authorization": f"Bearer {read_access_token}",
            "accept": "application/json",
        }

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        params = params or {}
        params.setdefault("api_key", self.api_key)
        params.setdefault("language", "ko-KR")
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{self.BASE}{path}", headers=self._headers, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    raise SourceUnavailableError(f"TMDB {r.status}: {path}")
                return await r.json()

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        """TMDB 인기 콘텐츠 → 한국(KR) 지역 한정 트렌드로 수정"""
        # 기존의 글로벌 트렌딩이 아닌, 한국 위치(region=KR) 기반 인기차트 호출
        media = "movie" if category in ("movie", "all") else "tv"
        
        # 한국인 대상 최적화: 발매/개봉 관련 지역 필터
        params = {"region": "KR", "page": 1}
        data = await self._get(f"/{media}/popular", params=params)

        results = []
        for idx, item in enumerate(data.get("results", [])[:20]):
            title = item.get("title") or item.get("name") or item.get("original_title", "")
            if not title:
                continue
            
            # 인기도 점수에 한국 가중치 적용 (popularity 값 자체는 글로벌이므로 순위에 기반한 점수 부여)
            score = round(max(10, 100 - (idx * 4)), 1)
            
            results.append(TrendItem(
                title=title,
                content_type=media,
                source=self.name,
                rank=idx + 1,
                score=score,
                metadata={
                    "tmdb_id": item.get("id"),
                    "original_title": item.get("original_title") or item.get("original_name"),
                    "release_date": item.get("release_date") or item.get("first_air_date"),
                    "vote_average": item.get("vote_average"),
                    "genre_ids": item.get("genre_ids", []),
                },
            ))
        return results

    async def fetch_keywords(self, title: str) -> list[str]:
        """작품 메타데이터 → 크로스 키워드 확장"""
        tmdb_id = await self._search(title)
        if not tmdb_id:
            return []

        details = await self._get(f"/movie/{tmdb_id}")
        credits = await self._get(f"/movie/{tmdb_id}/credits")

        kws = []
        # 감독
        for c in credits.get("crew", []):
            if c.get("job") == "Director":
                kws.append(f"{title} {c['name']}")
                kws.append(f"{c['name']} 감독 영화")
        # 주연
        for c in credits.get("cast", [])[:3]:
            kws.append(f"{title} {c['name']}")
        # 장르
        for g in details.get("genres", []):
            kws.append(f"{g['name']} 영화 추천")
        # 원작
        if details.get("original_language") == "en":
            kws.append(f"{title} 원작")
            kws.append(f"{title} 원작 소설")

        return kws

    async def get_similar(self, title: str) -> list[str]:
        """유사 작품 제목 리스트"""
        tmdb_id = await self._search(title)
        if not tmdb_id:
            return []
        data = await self._get(f"/movie/{tmdb_id}/similar")
        return [i.get("title") or i.get("name", "") for i in data.get("results", [])[:10] if i.get("title") or i.get("name")]

    async def _search(self, title: str) -> Optional[int]:
        data = await self._get("/search/movie", {"query": title})
        results = data.get("results", [])
        if not results:
            data = await self._get("/search/tv", {"query": title})
            results = data.get("results", [])
        return results[0]["id"] if results else None
