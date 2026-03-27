"""autoauthor/pipeline.py — 통합 파이프라인 (Copilot / Autopilot)
트렌드 탐지 → 키워드 수집 → 포화도 측정 → 기획안 생성을 한번에 실행.
"""
from typing import Optional, Union
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum

from .config import load_config, AutoAuthorConfig
from .trend_detector import TrendDetector, TrendReport
from .sources import (
    NaverDataLabSource, GoogleTrendsSource, TMDBSource,
    GoogleNewsSource, GoogleSuggestSource, WatchaPediaSource,
    BaseTrendSource,
)
from .ai.engine_chain import create_default_chain
from .planner.content_generator import ContentGenerator
from .db.connection import init_db, get_db
from .db.repository import Repository


class PipelineMode(str, Enum):
    COPILOT = "copilot"    # 단계마다 사용자 확인
    AUTOPILOT = "autopilot"  # 전자동


@dataclass
class PipelineResult:
    mode: str = "autopilot"
    trend_report: Optional[TrendReport] = None
    keywords_by_title: dict = field(default_factory=dict)   # {title: [keywords]}
    analyses_by_title: dict = field(default_factory=dict)    # {title: [analysis_results]}
    plans: list[dict] = field(default_factory=list)
    duration_seconds: float = 0
    errors: list[str] = field(default_factory=list)


class AutoAuthorPipeline:
    def __init__(self, config: Optional[AutoAuthorConfig] = None):
        self.config = config or load_config()
        self._detector: Optional[TrendDetector] = None
        self._generator: Optional[ContentGenerator] = None
        self._repo: Optional[Repository] = None

    def _init_sources(self) -> list[BaseTrendSource]:
        cfg = self.config
        sources: list[BaseTrendSource] = []
        if cfg.naver_client_id:
            sources.append(NaverDataLabSource(cfg.naver_client_id, cfg.naver_client_secret))
        sources.append(GoogleTrendsSource())
        if cfg.tmdb_read_access_token:
            sources.append(TMDBSource(cfg.tmdb_api_key, cfg.tmdb_read_access_token))
        sources.append(GoogleNewsSource())
        sources.append(GoogleSuggestSource())
        if cfg.enable_watcha_pedia:
            sources.append(WatchaPediaSource())
        return sources

    @property
    def detector(self) -> TrendDetector:
        if self._detector is None:
            self._detector = TrendDetector(self._init_sources())
        return self._detector

    @property
    def generator(self) -> ContentGenerator:
        if self._generator is None:
            chain = create_default_chain(
                self.config.gemini_api_key,
                self.config.ollama_base_url,
            )
            self._generator = ContentGenerator(chain)
        return self._generator

    @property
    def repo(self) -> Repository:
        if self._repo is None:
            conn = init_db(self.config.db_path)
            self._repo = Repository(conn)
        return self._repo

    # ── Autopilot 모드 ──
    async def run_autopilot(
        self,
        category: str = "movie",
        top_n: int = 5,
        platforms: Optional[list[str]] = None,
    ) -> PipelineResult:
        """전자동 파이프라인: 트렌드 탐지 → 키워드 → 기획안"""
        start = time.time()
        result = PipelineResult(mode="autopilot")
        platforms = platforms or ["tistory"]

        print("\n" + "=" * 60)
        print("  🚀 AutoAuthor Autopilot 모드")
        print("=" * 60)

        # Step 1: 트렌드 탐지
        print("\n📡 [1/4] 트렌드 탐지 중...")
        try:
            report = await self.detector.detect(category)
            result.trend_report = report
            print(report.summary())
            # DB 저장
            self.repo.save_trend_report(report.ranked_contents[:top_n])
        except Exception as e:
            result.errors.append(f"트렌드 탐지 실패: {e}")
            print(f"  ❌ {e}")
            result.duration_seconds = time.time() - start
            return result

        # Step 2: 키워드 수집 (상위 N개 콘텐츠)
        print(f"\n🔑 [2/4] 상위 {top_n}개 콘텐츠 키워드 수집 중...")
        for item in report.top(top_n):
            try:
                kws = await self.detector.discover_keywords(item.title)
                result.keywords_by_title[item.title] = kws
                print(f"  ✅ '{item.title}' — {len(kws)}개 키워드")
            except Exception as e:
                result.errors.append(f"키워드 수집 실패 ({item.title}): {e}")

        # Step 3: 포화도 측정 (기존 mvforrest_seo_v3 로직 활용)
        print(f"\n📊 [3/4] 포화도 측정 중...")
        for title, kws in result.keywords_by_title.items():
            analyses = await self._analyze_keywords(kws, title)
            result.analyses_by_title[title] = analyses
            golden = [a for a in analyses if a.get("is_golden")]
            print(f"  ✅ '{title}' — 황금 키워드 {len(golden)}개 / 전체 {len(analyses)}개")

        # Step 4: 기획안 생성
        print(f"\n🤖 [4/4] 기획안 생성 중 ({', '.join(platforms)})...")
        for title, analyses in result.analyses_by_title.items():
            try:
                plans = await self.generator.generate_multi_platform(
                    title=title,
                    content_type=category,
                    keywords=analyses,
                    platforms=platforms,
                )
                result.plans.extend(plans)
            except Exception as e:
                result.errors.append(f"기획안 생성 실패 ({title}): {e}")

        result.duration_seconds = round(time.time() - start, 1)

        # ── V6 단일 통합 CSV 추출 로직 (웹 대시보드 연동용) ──
        if result.analyses_by_title:
            self._export_unified_csv(result.analyses_by_title, "autopilot")

        # 요약
        print("\n" + "=" * 60)
        print("  ✅ Autopilot 완료!")
        print(f"  ⏱️ 소요 시간: {result.duration_seconds}초")
        print(f"  📊 트렌드: {len(report.ranked_contents)}개 콘텐츠 탐지")
        print(f"  🔑 키워드: {sum(len(v) for v in result.keywords_by_title.values())}개 수집")
        print(f"  📝 기획안: {len(result.plans)}개 생성")
        if result.errors:
            print(f"  ⚠️ 오류: {len(result.errors)}건")
        print("=" * 60)

        return result

    # ── Copilot 모드 (CLI용) ──
    async def run_copilot(
        self,
        category: str = "movie",
        platforms: Optional[list[str]] = None,
    ) -> PipelineResult:
        """반자동: 각 단계 결과를 보여주고 사용자 입력 대기"""
        start = time.time()
        result = PipelineResult(mode="copilot")
        platforms = platforms or ["tistory"]

        print("\n" + "=" * 60)
        print("  🧑‍✈️ AutoAuthor Copilot 모드")
        print("  (각 단계에서 선택/수정할 수 있습니다)")
        print("=" * 60)

        # Step 1: 트렌드 탐지
        print("\n📡 [1/4] 트렌드 탐지 중...")
        report = await self.detector.detect(category)
        result.trend_report = report
        print(report.summary())

        # 사용자 선택
        print("\n분석할 콘텐츠 번호를 입력하세요 (쉼표 구분, 예: 1,2,3)")
        print("또는 Enter를 눌러 상위 3개를 자동 선택:")
        user_input = input("→ ").strip()

        if user_input:
            indices = [int(x.strip()) - 1 for x in user_input.split(",") if x.strip().isdigit()]
            selected = [report.ranked_contents[i] for i in indices if i < len(report.ranked_contents)]
        else:
            selected = report.top(3)

        selected_titles = [item.title for item in selected]
        print(f"\n  선택: {', '.join(selected_titles)}")

        # Step 2: 키워드 수집
        print(f"\n🔑 [2/4] 키워드 수집 중...")
        for title in selected_titles:
            kws = await self.detector.discover_keywords(title)
            result.keywords_by_title[title] = kws
            print(f"  '{title}': {len(kws)}개")
            for kw in kws[:5]:
                print(f"    - {kw}")
            if len(kws) > 5:
                print(f"    ... 외 {len(kws)-5}개")

        print("\n추가할 키워드가 있으면 입력 (없으면 Enter):")
        extra = input("→ ").strip()
        if extra:
            for title in selected_titles:
                result.keywords_by_title[title].extend(extra.split(","))

        # Step 3: 포화도 측정
        print(f"\n📊 [3/4] 포화도 측정 중...")
        for title, kws in result.keywords_by_title.items():
            analyses = await self._analyze_keywords(kws, title)
            result.analyses_by_title[title] = analyses
            golden = [a for a in analyses if a.get("is_golden")]
            print(f"  '{title}' — 황금: {len(golden)}개")
            for g in golden[:3]:
                print(f"    🏆 {g['keyword']} (점수: {g['score']})")

        # Step 4: 기획안 생성
        print(f"\n🤖 [4/4] 기획안 생성 플랫폼: {platforms}")
        print("변경하려면 입력 (예: tistory,shortform,youtube), 없으면 Enter:")
        pf_input = input("→ ").strip()
        if pf_input:
            platforms = [p.strip() for p in pf_input.split(",")]

        for title, analyses in result.analyses_by_title.items():
            plans = await self.generator.generate_multi_platform(
                title, category, analyses, platforms)
            result.plans.extend(plans)

        result.duration_seconds = round(time.time() - start, 1)

        # ── V6 단일 통합 CSV 추출 로직 (웹 대시보드 연동용) ──
        if result.analyses_by_title:
            self._export_unified_csv(result.analyses_by_title, "copilot")

        print(f"\n✅ Copilot 완료! (기획안 {len(result.plans)}개, {result.duration_seconds}초)")
        return result

    # ── 포화도 측정 (멀티 플랫폼: 네이버 + 유튜브) ──
    async def _analyze_keywords(self, keywords: list[str], content_title: str) -> list[dict]:
        """키워드 포화도 측정 — 네이버/유튜브 병렬 평가
        
        [Naver] 월간검색량(네이버) + 블로그문서량 → 포화율 → 추천(네이버)
        [YouTube] 월간검색량(유튜브) + 유튜브영상수 + 평균조회수 → 포화율 → 추천(유튜브)
        """
        # ─ 시장규모 측정: 시드 키워드 기준 1회씩 호출
        naver_market = await self._measure_naver_ad(content_title)
        yt_market = await self._measure_youtube_market(content_title)
        print(f"    📊 '{content_title}' 월간검색량(네이버): {naver_market:,}회 | 월간검색량(유튜브): {yt_market:,}회")

        results = []
        for kw in keywords[:30]:
            # ─ 네이버: 블로그 누적 문서 수
            blog_docs = await self._measure_naver_blog(kw)
            
            # ─ 유튜브: 영상 수 + 상위 영상 평균 조회수
            yt_videos, yt_avg_views = await self._measure_youtube_supply(kw)
            
            # ─ 추천(네이버): 포화율 기반 (블로그문서량 ÷ 키워드에 대한 수요지표)
            if naver_market > 0:
                naver_ratio = blog_docs / naver_market
                if naver_ratio <= 0.01:
                    naver_stars = "★★★"
                elif naver_ratio <= 0.1:
                    naver_stars = "★★"
                else:
                    naver_stars = "★"
            else:
                # 시장규모 미확인 → 문서량만으로 판단
                if blog_docs <= 1000:
                    naver_stars = "★★★"
                elif blog_docs <= 10000:
                    naver_stars = "★★"
                else:
                    naver_stars = "★"
            
            # ─ 추천(유튜브): 영상수 적고 + 평균조회수 높을 때 황금
            if yt_avg_views > 0 and yt_videos > 0:
                yt_ratio = yt_videos / max(1, yt_avg_views)
                if yt_ratio <= 0.01 and yt_avg_views >= 10000:
                    yt_stars = "★★★"
                elif yt_ratio <= 0.1 and yt_avg_views >= 1000:
                    yt_stars = "★★"
                else:
                    yt_stars = "★"
            else:
                yt_stars = "-"

            results.append({
                "keyword": kw,
                "intent": self._classify_intent(kw),
                # 네이버
                "naver_market": naver_market,
                "blog_docs": blog_docs,
                "naver_stars": naver_stars,
                # 유튜브
                "yt_market": yt_market,
                "yt_videos": yt_videos,
                "yt_avg_views": yt_avg_views,
                "yt_stars": yt_stars,
                # DB 호환용
                "market_size": naver_market,
                "supply_raw": blog_docs,
                "demand_raw": naver_market,
                "blog_competition": blog_docs,
                "stars": naver_stars,
                "score": min(100, int(naver_market / 1000)),
                "saturation_grade": "blue" if naver_stars == "★★★" else ("purple" if naver_stars == "★★" else "red"),
                "is_golden": naver_stars == "★★★",
            })
            await asyncio.sleep(self.config.request_delay)

        results.sort(key=lambda x: x["blog_docs"])
        return results

    async def _measure_naver_ad(self, keyword: str) -> int:
        """네이버 검색광고 API — 시드 키워드의 PC+Mobile 월간 검색량 반환"""
        import time as _time
        import base64
        import hmac as _hmac
        import hashlib
        import aiohttp
        
        # 네이버 검색광고 API는 공백 제거된 키워드만 인식
        keyword = keyword.replace(" ", "")
        
        customer_id = getattr(self.config, "naver_ad_customer_id", "")
        api_key = getattr(self.config, "naver_ad_license", "")
        secret_key = getattr(self.config, "naver_ad_secret", "")
        
        if not (customer_id and api_key and secret_key):
            return 0
            
        timestamp = str(int(_time.time() * 1000))
        method = "GET"
        path = "/keywordstool"
        message = f"{timestamp}.{method}.{path}"
        mac = _hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
        sig = base64.b64encode(mac.digest()).decode("utf-8")
        
        headers = {
            "X-Timestamp": timestamp,
            "X-API-KEY": api_key,
            "X-Customer": str(customer_id),
            "X-Signature": sig
        }
        params = {"hintKeywords": keyword, "showDetail": "1"}
        url = "https://api.naver.com" + path
        
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, headers=headers,
                                 timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status == 200:
                        data = await r.json()
                        items = data.get("keywordList", [])
                        if items:
                            item = items[0]
                            pc = item.get("monthlyPcQcCnt", 0)
                            mobile = item.get("monthlyMobileQcCnt", 0)
                            pc = 5 if isinstance(pc, str) and "<" in pc else int(pc)
                            mobile = 5 if isinstance(mobile, str) and "<" in mobile else int(mobile)
                            return pc + mobile
                    return 0
        except Exception:
            return 0

    async def _measure_youtube_market(self, keyword: str) -> int:
        """유튜브 시장규모 측정 — 시드 키워드 상위 10개 영상 평균 조회수"""
        import aiohttp
        yt_key = getattr(self.config, "youtube_api_key", "")
        if not yt_key:
            return 0
        
        try:
            # 1. 검색으로 상위 영상 ID 수집
            search_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "id", "q": keyword, "type": "video",
                "regionCode": "KR", "maxResults": 10, "key": yt_key
            }
            async with aiohttp.ClientSession() as s:
                async with s.get(search_url, params=params,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return 0
                    data = await r.json()
                    video_ids = [item["id"]["videoId"] for item in data.get("items", [])
                                 if item.get("id", {}).get("videoId")]
                    if not video_ids:
                        return 0

                # 2. 영상 상세 통계에서 조회수 추출
                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {
                    "part": "statistics", "id": ",".join(video_ids), "key": yt_key
                }
                async with s.get(stats_url, params=stats_params,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r2:
                    if r2.status != 200:
                        return 0
                    stats_data = await r2.json()
                    views = []
                    for item in stats_data.get("items", []):
                        vc = item.get("statistics", {}).get("viewCount", "0")
                        views.append(int(vc))
                    return int(sum(views) / len(views)) if views else 0
        except Exception:
            return 0

    async def _measure_youtube_supply(self, keyword: str) -> tuple:
        """유튜브 키워드별 공급 측정 — (영상 수, 상위 5개 평균 조회수) 반환"""
        import aiohttp
        yt_key = getattr(self.config, "youtube_api_key", "")
        if not yt_key:
            return (0, 0)
        
        try:
            search_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "id", "q": keyword, "type": "video",
                "regionCode": "KR", "maxResults": 5, "key": yt_key
            }
            async with aiohttp.ClientSession() as s:
                async with s.get(search_url, params=params,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status != 200:
                        return (0, 0)
                    data = await r.json()
                    total_results = data.get("pageInfo", {}).get("totalResults", 0)
                    video_ids = [item["id"]["videoId"] for item in data.get("items", [])
                                 if item.get("id", {}).get("videoId")]
                    if not video_ids:
                        return (total_results, 0)

                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {
                    "part": "statistics", "id": ",".join(video_ids), "key": yt_key
                }
                async with s.get(stats_url, params=stats_params,
                                 timeout=aiohttp.ClientTimeout(total=10)) as r2:
                    if r2.status != 200:
                        return (total_results, 0)
                    stats_data = await r2.json()
                    views = []
                    for item in stats_data.get("items", []):
                        vc = item.get("statistics", {}).get("viewCount", "0")
                        views.append(int(vc))
                    avg_views = int(sum(views) / len(views)) if views else 0
                    return (total_results, avg_views)
        except Exception:
            return (0, 0)

    # ── 통합 CSV 내보내기 ──
    def _export_unified_csv(self, analyses_by_title: dict, mode: str = "autopilot"):
        import pandas as pd
        import os
        from datetime import datetime
        rows = []
        for t, analyses in analyses_by_title.items():
            for a in analyses:
                rows.append({
                    "콘텐츠명": t,
                    "월간검색량(네이버)": a["naver_market"],
                    "월간검색량(유튜브)": a["yt_market"],
                    "키워드": a["keyword"],
                    "검색의도": a.get("intent", ""),
                    "블로그문서량": a["blog_docs"],
                    "추천(네이버)": a["naver_stars"],
                    "유튜브영상수": a["yt_videos"],
                    "평균조회수(유튜브)": a["yt_avg_views"],
                    "추천(유튜브)": a["yt_stars"],
                })
        if rows:
            os.makedirs("results", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"results/키워드분석_통합_{mode}_{timestamp}.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"  💾 통합 CSV 저장 완료: {csv_path}")
            return csv_path
        return None

    async def _measure_naver_blog(self, keyword: str) -> int:
        """네이버 블로그 문서량 절대수치 반환 (OpenAPI 우선, 실패 시 스크래핑)"""
        import aiohttp
        
        # 1. OpenAPI 활용 (우선)
        if getattr(self.config, "use_naver_openapi", False) and getattr(self.config, "naver_client_id", ""):
            url = "https://openapi.naver.com/v1/search/blog.json"
            headers = {
                "X-Naver-Client-Id": self.config.naver_client_id,
                "X-Naver-Client-Secret": getattr(self.config, "naver_client_secret", ""),
            }
            params = {"query": keyword, "display": 1}
            try:
                async with aiohttp.ClientSession() as s:
                    async with s.get(url, headers=headers, params=params, timeout=5) as r:
                        if r.status == 200:
                            data = await r.json()
                            total = data.get("total", 0)
                            return total
            except Exception:
                pass # OpenAPI 실패 시 스크래핑으로 폴백

        # 2. 스크래핑 폴백 (User-Agent 정상화)
        url = "https://search.naver.com/search.naver"
        params = {"where": "blog", "query": keyword}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(url, params=params, headers=headers, timeout=10) as r:
                    if r.status != 200:
                        return -1
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(await r.text(), "html.parser")
                    items = soup.select(".total_wrap") or soup.select(".api_subject_bx") or soup.select("a.title_link")
                    return len(items)
        except Exception:
            return -1

    @staticmethod
    def _classify_intent(keyword: str) -> str:
        info = ["정리", "요약", "해석", "분석", "의미", "비교", "차이", "실화", "원작", "배경"]
        txn = ["다운", "무료", "보기", "넷플릭스", "왓챠", "쿠팡"]
        for p in info:
            if p in keyword:
                return "정보형"
        for p in txn:
            if p in keyword:
                return "거래형"
        return "탐색형"


# ── CLI 엔트리포인트 ──
async def _cli_main():
    import argparse
    parser = argparse.ArgumentParser(description="AutoAuthor Pipeline")
    parser.add_argument("--mode", choices=["copilot", "autopilot"], default="autopilot")
    parser.add_argument("--category", default="movie")
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--platforms", default="tistory", help="콤마 구분: tistory,shortform,youtube")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",")]
    pipeline = AutoAuthorPipeline()

    if args.mode == "copilot":
        result = await pipeline.run_copilot(args.category, platforms)
    else:
        result = await pipeline.run_autopilot(args.category, args.top, platforms)

    # 기획안 출력
    for plan in result.plans:
        if "error" in plan:
            continue
        print(f"\n{'='*60}")
        print(f"  📝 [{plan['platform_display']}] {plan['title']}")
        print(f"  🤖 Model: {plan['ai_model']}")
        print(f"{'='*60}")
        print(plan["plan_text"][:2000])
        if len(plan["plan_text"]) > 2000:
            print(f"\n  ... ({len(plan['plan_text'])}자 중 2000자 표시)")


if __name__ == "__main__":
    asyncio.run(_cli_main())
