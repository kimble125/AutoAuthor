"""autoauthor/sources/kakao.py — 카카오 REST API (Daum 검색) 연동"""
import aiohttp
import urllib.parse
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class KakaoSource(BaseTrendSource):
    name = "kakao"
    is_optional = True
    
    BASE_URL = "https://dapi.kakao.com/v2/search"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        """카카오는 키워드 수집 및 공급량 측정에 주로 사용 → 빈 리스트 반환"""
        return []

    async def fetch_keywords(self, title: str) -> list[str]:
        """Daum Tip(Q&A)을 활용한 롱테일 키워드 수집 (보조 용도)"""
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {"query": title, "size": 10}
        url = f"{self.BASE_URL}/tip"
        
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return []
                    data = await r.json()
                    # 팁 제목에서 키워드 추출
                    items = data.get("documents", [])
                    return [item["title"].replace("<b>", "").replace("</b>", "").strip() for item in items]
        except Exception:
            return []

    async def get_blog_count(self, keyword: str) -> int:
        """카카오 블로그 검색 결과 총합(Supply) 반환"""
        if not self.api_key:
            return 0
            
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        # 정확한 검색을 위해 따옴표 포함 추천 (사용자 선택)
        params = {"query": keyword, "size": 1}
        url = f"{self.BASE_URL}/blog"
        
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return 0
                    data = await r.json()
                    return data.get("meta", {}).get("total_count", 0)
        except Exception:
            return 0

    async def get_web_count(self, keyword: str) -> int:
        """카카오 웹 검색 결과 총합 반환"""
        if not self.api_key:
            return 0
            
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {"query": keyword, "size": 1}
        url = f"{self.BASE_URL}/web"
        
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return 0
                    data = await r.json()
                    return data.get("meta", {}).get("total_count", 0)
        except Exception:
            return 0
