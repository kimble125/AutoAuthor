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
    KakaoSource, BaseTrendSource,
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
        self._kakao: Optional[KakaoSource] = None
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
    def kakao(self) -> KakaoSource:
        if self._kakao is None:
            self._kakao = KakaoSource(self.config.kakao_api_key)
        return self._kakao

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
        """키워드 포화도 측정 — 네이버 기반 1차 필터링 후 유튜브 지연 평가 (Lazy Evaluation)"""
        from .sources.google_trends import GoogleTrendsSource
        pt_source = GoogleTrendsSource()
        
        # ─ 시장규모 및 가중치 측정 (시드 키워드 단위)
        base_naver_market = await self._measure_naver_ad(content_title)
        google_trend_weight = await pt_source.get_keyword_recency_score(content_title)
        
        total_demand = int(base_naver_market * (1 + (google_trend_weight / 100.0)))
        print(f"    📊 '{content_title}' 기반수요(네이버): {base_naver_market:,}회 | 구글트렌드가중치: {google_trend_weight}% | 통합수요(가중치): {total_demand:,}회")

        # 1차 평가: 네이버/카카오 문서량 
        temp_results = []
        for kw in keywords[:30]:
            blog_docs = await self._measure_naver_blog(kw)
            kakao_docs = await self.kakao.get_blog_count(kw)
            
            if total_demand > 0:
                naver_ratio = blog_docs / total_demand
                if naver_ratio <= 0.005:
                    naver_stars = "★★★"
                elif naver_ratio <= 0.02:
                    naver_stars = "★★"
                else:
                    naver_stars = "★"
            else:
                if blog_docs <= 200:
                    naver_stars = "★★★"
                elif blog_docs <= 1000:
                    naver_stars = "★★"
                else:
                    naver_stars = "★"

            if total_demand > 0:
                kakao_ratio = kakao_docs / total_demand
                if kakao_ratio <= 0.002:
                    kakao_stars = "★★★"
                elif kakao_ratio <= 0.01:
                    kakao_stars = "★★"
                else:
                    kakao_stars = "★"
            else:
                if kakao_docs <= 100:
                    kakao_stars = "★★★"
                elif kakao_docs <= 500:
                    kakao_stars = "★★"
                else:
                    kakao_stars = "★"

            temp_results.append({
                "keyword": kw,
                "intent": self._classify_intent(kw),
                "google_trend_pct": google_trend_weight,
                "total_demand": total_demand,
                "naver_docs": blog_docs,
                "naver_stars": naver_stars,
                "kakao_docs": kakao_docs,
                "kakao_stars": kakao_stars,
            })
            import asyncio
            await asyncio.sleep(self.config.request_delay)

        # 1차 정렬 (블로그 문서량 기준 오름차순 - 가장 블루오션인 키워드 우선)
        temp_results.sort(key=lambda x: x["naver_docs"])

        # 2차 평가: 상위 5개 키워드만 유튜브 데이터 수집 (Lazy Evaluation)
        MAX_YOUTUBE_QUERIES = 5
        quota_exceeded = False
        
        for i, res in enumerate(temp_results):
            if i < MAX_YOUTUBE_QUERIES and not quota_exceeded:
                yt_data = await self._measure_youtube_metrics(res["keyword"])
                
                if yt_data.get("quota_exceeded"):
                    quota_exceeded = True
                    yt_stars = "- (할당량 초과)"
                    recent_vids = 0
                else:
                    recent_vids = yt_data.get("recent_videos", 0)
                    if total_demand > 0:
                        yt_ratio = recent_vids / max(1, (total_demand / 1000.0))
                        if yt_ratio <= 0.5:
                            yt_stars = "★★★"
                        elif yt_ratio <= 1.5:
                            yt_stars = "★★"
                        else:
                            yt_stars = "★"
                    else:
                        if recent_vids <= 3:
                            yt_stars = "★★★"
                        elif recent_vids <= 10:
                            yt_stars = "★★"
                        else:
                            yt_stars = "★"
                            
                res.update({
                    "yt_total_videos": yt_data.get("total_videos", 0),
                    "yt_total_avg_views": yt_data.get("total_avg_views", 0),
                    "yt_recent_videos": recent_vids,
                    "yt_recent_avg_views": yt_data.get("recent_avg_views", 0),
                    "yt_stars": yt_stars,
                    "is_golden": res["naver_stars"] == "★★★" or yt_stars == "★★★"
                })
                # 유튜브 API 딜레이 추가
                import asyncio
                await asyncio.sleep(self.config.request_delay)
            else:
                # 할당량 초과 또는 상위 5위 밖 키워드는 스킵
                res.update({
                    "yt_total_videos": 0,
                    "yt_total_avg_views": 0,
                    "yt_recent_videos": 0,
                    "yt_recent_avg_views": 0,
                    "yt_stars": "- (조회 생략)" if not quota_exceeded else "- (할당량 초과)",
                    "is_golden": res["naver_stars"] == "★★★"
                })

        return temp_results

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

    async def _measure_youtube_metrics(self, keyword: str) -> dict:
        """유튜브 투-트랙 지표 동시 수집 (에버그린 / 트렌디 30일)"""
        import aiohttp
        from datetime import datetime, timedelta, timezone
        yt_key = getattr(self.config, "youtube_api_key", "")
        if not yt_key:
            return {"total_videos": 0, "total_avg_views": 0, "recent_videos": 0, "recent_avg_views": 0}
        
        async def fetch_metrics(session, params):
            try:
                search_url = "https://www.googleapis.com/youtube/v3/search"
                async with session.get(search_url, params=params, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    if r.status != 200:
                        if r.status == 403:
                            print("    ❌ YouTube API 할당량(Quota) 초과! (이후 유튜브 지표는 0으로 처리됩니다)")
                            return -1, -1
                        return 0, 0
                    data = await r.json()
                    total_res = data.get("pageInfo", {}).get("totalResults", 0)
                    video_ids = [item["id"]["videoId"] for item in data.get("items", []) if item.get("id", {}).get("videoId")]
                    if not video_ids:
                        return total_res, 0
                
                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": yt_key}
                async with session.get(stats_url, params=stats_params, timeout=aiohttp.ClientTimeout(total=8)) as r2:
                    if r2.status != 200:
                        return total_res, 0
                    stats_data = await r2.json()
                    views = [int(item.get("statistics", {}).get("viewCount", "0")) for item in stats_data.get("items", [])]
                    avg_views = int(sum(views) / len(views)) if views else 0
                    return total_res, avg_views
            except Exception:
                return 0, 0

        try:
            async with aiohttp.ClientSession() as s:
                # 1. Total (Evergreen)
                params_total = {"part": "id", "q": keyword, "type": "video", "regionCode": "KR", "maxResults": 5, "key": yt_key}
                
                # 2. Recent 30 days (Trendy)
                thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
                params_recent = {"part": "id", "q": keyword, "type": "video", "regionCode": "KR", "maxResults": 5, "publishedAfter": thirty_days_ago, "order": "relevance", "key": yt_key}
                
                total_res, ts_res = await asyncio.gather(
                    fetch_metrics(s, params_total),
                    fetch_metrics(s, params_recent)
                )
                
                if total_res[0] == -1 or ts_res[0] == -1:
                    return {"quota_exceeded": True}
                
                return {
                    "total_videos": total_res[0],
                    "total_avg_views": total_res[1],
                    "recent_videos": ts_res[0],
                    "recent_avg_views": ts_res[1],
                }
        except Exception as e:
            return {"total_videos": 0, "total_avg_views": 0, "recent_videos": 0, "recent_avg_views": 0}

    def _export_unified_csv(self, analyses_by_title: dict, mode: str = "autopilot"):
        import pandas as pd
        import os
        from datetime import datetime
        rows = []
        for t, analyses in analyses_by_title.items():
            for a in analyses:
                rows.append({
                    "콘텐츠명(주제)": t,
                    "구글_트렌드(%)": a["google_trend_pct"],
                    "통합검색수요(전체)": a["total_demand"],
                    "하위_키워드": a["keyword"],
                    "총문서량(네이버)": a["naver_docs"],
                    "추천도(네이버)": a["naver_stars"],
                    "총문서량(다음)": a["kakao_docs"],
                    "추천도(티스토리)": a["kakao_stars"],
                    "총영상수(유튜브)": a["yt_total_videos"],
                    "평균조회수(유튜브)": a["yt_total_avg_views"],
                    "최근30일_영상수(유튜브)": a["yt_recent_videos"],
                    "최근30일_조회수(유튜브)": a["yt_recent_avg_views"],
                    "추천도(유튜브)": a["yt_stars"],
                })
        if rows:
            os.makedirs("results", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = f"results/키워드분석_통합_{mode}_{timestamp}.csv"
            pd.DataFrame(rows).to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"  💾 통합 CSV 저장 완료: {csv_path}")
            return csv_path
        return None

    def _export_plans(self, plans: list[dict], mode: str = "autopilot"):
        import os
        import re
        from datetime import datetime
        os.makedirs("results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_files = []
        
        for plan in plans:
            if "error" in plan or not plan.get("plan_text"):
                continue
            
            title_safe = re.sub(r'[^\w가-힣]', '_', plan["title"])
            platform = plan["platform"]
            filename = f"results/기획안_{title_safe}_{platform}_{timestamp}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# [{plan.get('platform_display', platform)}] {plan['title']}\n")
                f.write(f"- 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"- AI 모델: {plan.get('ai_model', 'N/A')}\n\n")
                f.write(plan["plan_text"])
            
            saved_files.append(filename)
            
        if saved_files:
            print(f"  💾 기획안 파일 {len(saved_files)}개 저장 완료 (results/)")
        return saved_files

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
    parser.add_argument("--platforms", default="tistory", help="콤마 구분: tistory,naver,youtube,instagram,facebook,shortform,thread")
    parser.add_argument("--titles", help="수동 분석할 타이틀 목록 (콤마 구분, 예: '마션,인터스텔라')")
    args = parser.parse_args()

    platforms = [p.strip() for p in args.platforms.split(",")]
    pipeline = AutoAuthorPipeline()

    if args.titles:
        titles = [t.strip() for t in args.titles.split(",")]
        # 수동 타이틀 지정 시 트렌드 탐지를 스킵하고 바로 3단계 파이프라인 수행
        print("\n" + "=" * 60)
        print("  🚀 AutoAuthor 수동 지정 키워드 분석 모드")
        print(f"  타겟 시드: {titles}")
        print("=" * 60)
        
        from .pipeline import PipelineResult
        import time
        result = PipelineResult(mode="manual_test")
        start = time.time()
        
        for title in titles:
            try:
                kws = await pipeline.detector.discover_keywords(title)
                result.keywords_by_title[title] = kws
            except Exception as e:
                result.errors.append(f"키워드 수집 실패 ({title}): {e}")

        for title, kws in result.keywords_by_title.items():
            if kws:
                analyses = await pipeline._analyze_keywords(kws, title)
                result.analyses_by_title[title] = analyses

        for title, analyses in result.analyses_by_title.items():
            if analyses:
                plans = await pipeline.generator.generate_multi_platform(title, args.category, analyses, platforms)
                result.plans.extend(plans)
        
        # 연계 콘텐츠(Synergy) 기획 추가 (여러 작품일 경우)
        if len(titles) >= 2:
            print(f"\n🔗 [Synergy] {len(titles)}개 작품 연계 기획안 생성 중...")
            try:
                synergy_plans = await pipeline.generator.generate_synergy_plan(
                    titles=titles,
                    category=args.category,
                    analyses_by_title=result.analyses_by_title,
                    platforms=platforms
                )
                result.plans.extend(synergy_plans)
            except Exception as e:
                print(f"  ⚠️ 연계 기획안 생성 실패: {e}")

        if result.plans:
            pipeline._export_plans(result.plans, "수동분석")
            
        if result.analyses_by_title:
            pipeline._export_unified_csv(result.analyses_by_title, "수동분석")
        
    elif args.mode == "copilot":
        result = await pipeline.run_copilot(args.category, platforms)
        if result.plans:
            pipeline._export_plans(result.plans, "copilot")
    else:
        result = await pipeline.run_autopilot(args.category, args.top, platforms)
        if result.plans:
            pipeline._export_plans(result.plans, "autopilot")

    # 기획안 출력
    for plan in result.plans:
        if "error" in plan:
            continue
        print(f"\n{'='*60}")
        print(f"  📝 [{plan.get('platform_display', plan['platform'])}] {plan['title']}")
        print(f"  🤖 Model: {plan.get('ai_model', 'N/A')}")
        print(f"{'='*60}")
        print(plan["plan_text"][:2000])
        if len(plan["plan_text"]) > 2000:
            print(f"\n  ... ({len(plan['plan_text'])}자 중 2000자 표시)")


if __name__ == "__main__":
    asyncio.run(_cli_main())
