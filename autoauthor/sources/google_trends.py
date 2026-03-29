"""autoauthor/sources/google_trends.py — Google Trends (pytrends / pytrends-modern)
한국 설정: hl='ko', tz=-540, geo='KR'
"""
import asyncio
from .base import BaseTrendSource, TrendItem, SourceUnavailableError


class GoogleTrendsSource(BaseTrendSource):
    name = "google_trends"
    is_optional = False

    def __init__(self):
        self._pytrends = None

    def _get_client(self):
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq
                self._pytrends = TrendReq(hl='ko', tz=-540)
            except ImportError:
                raise ImportError("pip install pytrends 또는 pip install pytrends-modern[all]")
        return self._pytrends

    async def fetch_trends(self, category: str = "movie") -> list[TrendItem]:
        """실시간 급상승 검색어 중 콘텐츠 관련 항목 추출"""
        try:
            pt = self._get_client()
            import time
            for attempt in range(3):
                try:
                    trending = await asyncio.to_thread(pt.realtime_trending_searches, pn='KR')
                    break
                except Exception as e:
                    if '429' in str(e) and attempt < 2:
                        time.sleep(2 * (attempt + 1))
                        continue
                    raise e
        except Exception as e:
            if '404' in str(e) or '400' in str(e):
                print(f"  ⚠️ Google Trends realtime 오류: {e} (지원 안됨)")
                return []
            raise SourceUnavailableError(f"Google Trends trending_searches 오류: {e}")

        results = []
        content_signals = {
            "영화", "드라마", "넷플릭스", "티빙", "쿠팡플레이", "웨이브",
            "왓챠", "디즈니", "시즌", "개봉", "방영", "출연", "감독",
            "웹툰", "애니", "배우", "OST", "관객", "시청률", "예고편",
        }

        for idx, row in trending.iterrows():
            kw = str(row[0]) if not isinstance(row[0], str) else row[0]
            is_content = any(s in kw for s in content_signals) or len(kw) >= 4
            if is_content:
                results.append(TrendItem(
                    title=kw,
                    content_type=category,
                    source=self.name,
                    rank=idx + 1,
                    score=max(0, 100 - idx * 2.5),
                    metadata={"type": "realtime_trending"},
                ))
        return results

    async def fetch_keywords(self, title: str) -> list[str]:
        """related_queries: top + rising"""
        try:
            pt = self._get_client()
            import time
            for attempt in range(3):
                try:
                    await asyncio.to_thread(pt.build_payload, [title], geo='KR', timeframe='now 7-d')
                    related = await asyncio.to_thread(pt.related_queries)
                    break
                except Exception as e:
                    if '429' in str(e) and attempt < 2:
                        time.sleep(2 * (attempt + 1))
                        continue
                    raise e
        except Exception as e:
            print(f"  ⚠️ Google Trends related_queries 오류: {e}")
            return []

        keywords = []
        if title in related:
            for qtype in ('top', 'rising'):
                df = related[title].get(qtype)
                if df is not None and not df.empty:
                    keywords.extend(df['query'].tolist()[:10])
        return list(dict.fromkeys(keywords))

    async def get_interest_over_time(self, keywords: list[str]) -> dict:
        """여러 키워드의 검색량 추이 비교 (상대 비교)"""
        try:
            pt = self._get_client()
            await asyncio.to_thread(pt.build_payload, keywords[:5], geo='KR', timeframe='today 3-m')
            df = await asyncio.to_thread(pt.interest_over_time)
            if df.empty:
                return {}
            return {col: df[col].tolist() for col in df.columns if col != 'isPartial'}
        except Exception:
            return {}

    async def get_keyword_recency_score(self, keyword: str) -> int:
        """단일 키워드의 최근 30일 대비 현재 화제성 가중치 추출 (0~100)
        개별 키워드의 30일 간 자체 최대 검색량을 100으로 두고, 가장 최근 3일의 평균 점수를 반환함.
        """
        try:
            pt = self._get_client()
            import time
            for attempt in range(2):
                try:
                    await asyncio.to_thread(pt.build_payload, [keyword], geo='KR', timeframe='today 1-m')
                    df = await asyncio.to_thread(pt.interest_over_time)
                    if df.empty or keyword not in df.columns:
                        return 0
                        
                    # 마지막 3개 데이터(주로 최근 3일)의 평균값
                    recent_data = df[keyword].tail(3)
                    if len(recent_data) > 0:
                        score = int(recent_data.mean())
                        return max(0, min(100, score))
                    return 0
                except Exception as e:
                    if '429' in str(e):
                        time.sleep(2)
                        continue
                    break
        except Exception:
            pass
        return 0
