"""autoauthor/sources/watcha_pedia.py — 왓챠피디아 HOT 랭킹 (Optional)
비공식 내부 API 활용. 요청 간격 3초+, 캐시 1시간, 차단 시 graceful skip.
"""
import aiohttp
import time
from bs4 import BeautifulSoup
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class WatchaPediaSource(BaseTrendSource):
    name = "watcha_pedia"
    is_optional = True

    BASE_URL = "https://pedia.watcha.com/ko-KR"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
        "Referer": "https://pedia.watcha.com/",
    }

    _cache: list[TrendItem] = []
    _cache_ts: float = 0
    CACHE_TTL = 3600

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        if self._cache and (time.time() - self._cache_ts < self.CACHE_TTL):
            return self._cache

        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(self.BASE_URL, headers=self.HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    if r.status != 200:
                        raise SourceUnavailableError(f"왓챠피디아 HTTP {r.status}")
                    html = await r.text()
        except aiohttp.ClientError as e:
            raise SourceUnavailableError(f"왓챠피디아 연결 오류: {e}")

        results = self._parse(html)
        self._cache = results
        self._cache_ts = time.time()
        return results

    async def fetch_keywords(self, title: str) -> list[str]:
        return []  # 왓챠피디아 키워드는 TMDB + 구글 자동완성으로 대체

    def _parse(self, html: str) -> list[TrendItem]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        seen = set()

        for link in soup.select("a[href*='/ko-KR/contents/']"):
            href = link.get("href", "")
            cid = href.split("/contents/")[-1] if "/contents/" in href else None
            if not cid or cid in seen:
                continue
            seen.add(cid)

            img = link.find("img")
            title = img.get("alt", "") if img else link.get_text(strip=True)
            if not title or len(results) >= 10:
                continue

            ctype = "movie" if cid.startswith("m") else "tv"
            results.append(TrendItem(
                title=title, content_type=ctype, source=self.name,
                rank=len(results) + 1,
                score=max(0, 100 - len(results) * 8),
                metadata={"watcha_id": cid, "url": f"https://pedia.watcha.com{href}"},
            ))
        return results
