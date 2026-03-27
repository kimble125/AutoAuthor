"""api/routers/trends.py — 트렌드 조회 API"""
from fastapi import APIRouter
from autoauthor.pipeline import AutoAuthorPipeline

router = APIRouter(prefix="/api/trends", tags=["trends"])
_pipeline = AutoAuthorPipeline()


@router.get("/detect")
async def detect_trends(category: str = "movie", top: int = 10):
    """트렌드 탐지 실행"""
    report = await _pipeline.detector.detect(category)
    return {
        "source_coverage": report.source_coverage,
        "failed_sources": report.failed_sources,
        "contents": [item.to_dict() for item in report.top(top)],
    }


@router.get("/keywords/{title}")
async def get_keywords(title: str):
    """특정 콘텐츠 키워드 수집"""
    kws = await _pipeline.detector.discover_keywords(title)
    return {"title": title, "keyword_count": len(kws), "keywords": kws}


@router.get("/db/trending")
async def db_trending(days: int = 7, limit: int = 20):
    """DB에 저장된 트렌드 조회"""
    return _pipeline.repo.get_trending_contents(days, limit)


@router.get("/db/golden-keywords")
async def db_golden(limit: int = 20):
    """DB에 저장된 황금 키워드 조회"""
    return _pipeline.repo.get_golden_keywords(limit)
