"""autoauthor/trend_detector.py — 트렌드 탐지 오케스트레이터
모든 데이터 소스를 통합하여 화제 콘텐츠를 자동 탐지합니다.
"""
from typing import Optional, Union
import asyncio
from dataclasses import dataclass, field
from .sources.base import BaseTrendSource, TrendItem, SourceUnavailableError


SOURCE_WEIGHTS = {
    "naver_datalab": 1.5,
    "google_trends": 1.3,
    "tmdb": 1.0,
    "google_news": 1.2,
    "google_suggest": 0.8,
    "watcha_pedia": 1.4,
}


@dataclass
class TrendReport:
    ranked_contents: list[TrendItem] = field(default_factory=list)
    source_results: dict = field(default_factory=dict)
    source_coverage: str = ""
    failed_sources: list[str] = field(default_factory=list)

    def top(self, n: int = 10) -> list[TrendItem]:
        return self.ranked_contents[:n]

    def to_seed_keywords(self) -> list[str]:
        return [item.title for item in self.ranked_contents[:20]]

    def summary(self) -> str:
        lines = [f"📊 트렌드 탐지 결과 ({self.source_coverage})"]
        if self.failed_sources:
            lines.append(f"  ⚠️ 실패: {', '.join(self.failed_sources)}")
        for item in self.top(10):
            srcs = ", ".join(item.metadata.get("sources", []))
            lines.append(f"  {item.rank:2d}. {item.title} (점수: {item.score:.1f}) [{srcs}]")
        return "\n".join(lines)


class TrendDetector:
    def __init__(self, sources: list[BaseTrendSource]):
        self.sources = sources

    async def detect(self, category: str = "movie") -> TrendReport:
        """모든 소스에서 병렬 수집 → 통합 순위"""
        # 1단계: TMDB로 시드 키워드 수집 (다른 소스에 주입)
        tmdb_seeds = await self._get_tmdb_seeds(category)

        # 2단계: 모든 소스 병렬 호출
        tasks = []
        for src in self.sources:
            if src.name == "naver_datalab" and tmdb_seeds:
                tasks.append(self._safe_fetch(src, category, seed_titles=tmdb_seeds))
            else:
                tasks.append(self._safe_fetch(src, category))

        results = await asyncio.gather(*tasks)

        source_results = {}
        failed = []
        for src, result in zip(self.sources, results):
            if isinstance(result, list):
                source_results[src.name] = result
            else:
                failed.append(src.name)

        ranked = self._merge(source_results)
        total = len(self.sources)
        ok = total - len(failed)

        return TrendReport(
            ranked_contents=ranked,
            source_results=source_results,
            source_coverage=f"{ok}/{total} 소스 수집 성공",
            failed_sources=failed,
        )

    async def discover_keywords(self, title: str, max_per_source: int = 15) -> list[str]:
        """특정 콘텐츠에 대해 모든 소스에서 키워드 수집"""
        tasks = [src.fetch_keywords(title) for src in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_kws = []
        for r in results:
            if isinstance(r, list):
                all_kws.extend(r[:max_per_source])
        return list(dict.fromkeys(all_kws))  # 중복 제거, 순서 유지

    async def _get_tmdb_seeds(self, category: str) -> list[str]:
        """TMDB에서 시드 키워드 추출 (Naver DataLab에 주입용)"""
        for src in self.sources:
            if src.name == "tmdb":
                try:
                    items = await src.fetch_trends(category)
                    return [i.title for i in items[:15]]
                except Exception:
                    pass
        return []

    async def _safe_fetch(self, src: BaseTrendSource, category: str, **kwargs) -> Union[list[TrendItem], str]:
        """타임아웃 + 에러 핸들링"""
        try:
            if kwargs.get("seed_titles") and hasattr(src, 'fetch_trends'):
                # NaverDataLab은 seed_titles 인자를 받음
                import inspect
                sig = inspect.signature(src.fetch_trends)
                if "seed_titles" in sig.parameters:
                    return await asyncio.wait_for(
                        src.fetch_trends(category, **kwargs), timeout=30)
            return await asyncio.wait_for(src.fetch_trends(category), timeout=30)
        except asyncio.TimeoutError:
            msg = f"{src.name} 타임아웃"
        except SourceUnavailableError as e:
            msg = str(e)
        except Exception as e:
            msg = f"{src.name}: {e}"

        if src.is_optional:
            print(f"  ⚠️ {msg} (optional, skip)")
            return msg  # 문자열 = 실패
        else:
            print(f"  ❌ {msg} (core)")
            return msg

    def _merge(self, source_results: dict[str, list[TrendItem]]) -> list[TrendItem]:
        merged: dict[str, TrendItem] = {}

        for src_name, items in source_results.items():
            w = SOURCE_WEIGHTS.get(src_name, 1.0)
            for item in items:
                key = item.normalized_title
                if not key:
                    continue
                if key in merged:
                    merged[key].score += item.score * w
                    merged[key].metadata.setdefault("sources", []).append(src_name)
                    # 메타데이터 병합
                    for k, v in item.metadata.items():
                        if k != "sources" and k not in merged[key].metadata:
                            merged[key].metadata[k] = v
                else:
                    item.score *= w
                    item.metadata["sources"] = [src_name]
                    merged[key] = item

        # 다중 소스 보너스
        for item in merged.values():
            n = len(set(item.metadata.get("sources", [])))
            if n >= 3:
                item.score *= 1.3
            elif n >= 2:
                item.score *= 1.15
            item.score = round(item.score, 1)

        result = sorted(merged.values(), key=lambda x: x.score, reverse=True)
        for i, item in enumerate(result):
            item.rank = i + 1
        return result


# ── CLI 엔트리포인트 ──
async def _main():
    from .config import load_config
    from .sources import (
        NaverDataLabSource, GoogleTrendsSource, TMDBSource,
        GoogleNewsSource, GoogleSuggestSource, WatchaPediaSource,
    )

    cfg = load_config()
    sources: list[BaseTrendSource] = []

    # Core
    if cfg.naver_client_id:
        sources.append(NaverDataLabSource(cfg.naver_client_id, cfg.naver_client_secret))
    sources.append(GoogleTrendsSource())
    if cfg.tmdb_read_access_token:
        sources.append(TMDBSource(cfg.tmdb_api_key, cfg.tmdb_read_access_token))
    sources.append(GoogleNewsSource())
    sources.append(GoogleSuggestSource())

    # Optional
    if cfg.enable_watcha_pedia:
        sources.append(WatchaPediaSource())

    detector = TrendDetector(sources)

    print("=" * 60)
    print("  AutoAuthor V6 — 트렌드 자동 탐지")
    print("=" * 60)

    report = await detector.detect(category="movie")
    print(report.summary())

    # 상위 3개 콘텐츠 키워드 탐색
    for item in report.top(3):
        print(f"\n🔑 '{item.title}' 연관 키워드:")
        kws = await detector.discover_keywords(item.title)
        for kw in kws[:10]:
            print(f"    - {kw}")

    return report


if __name__ == "__main__":
    asyncio.run(_main())
