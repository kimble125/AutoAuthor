"""api/routers/pipeline.py — Autopilot REST + Copilot WebSocket"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from autoauthor.pipeline import AutoAuthorPipeline

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])
_pipeline = AutoAuthorPipeline()


class AutopilotRequest(BaseModel):
    category: str = "movie"
    top_n: int = 3
    platforms: list[str] = ["tistory"]


@router.post("/autopilot")
async def run_autopilot(req: AutopilotRequest):
    """전자동 파이프라인 실행"""
    result = await _pipeline.run_autopilot(
        category=req.category,
        top_n=req.top_n,
        platforms=req.platforms,
    )
    return {
        "mode": "autopilot",
        "duration_seconds": result.duration_seconds,
        "trends_found": len(result.trend_report.ranked_contents) if result.trend_report else 0,
        "keywords_collected": sum(len(v) for v in result.keywords_by_title.values()),
        "plans_generated": len([p for p in result.plans if "error" not in p]),
        "plans": result.plans,
        "errors": result.errors,
    }


@router.websocket("/ws/copilot")
async def copilot_ws(ws: WebSocket):
    """Copilot WebSocket — 단계별 결과 전송 + 사용자 입력 수신"""
    await ws.accept()
    try:
        config = await ws.receive_json()
        category = config.get("category", "movie")
        platforms = config.get("platforms", ["tistory"])

        # Step 1: 트렌드 탐지
        await ws.send_json({"step": "trend_detect", "status": "running"})
        report = await _pipeline.detector.detect(category)
        await ws.send_json({
            "step": "trend_detect",
            "status": "awaiting_input",
            "data": [item.to_dict() for item in report.top(20)],
        })

        selection = await ws.receive_json()
        selected = selection.get("selected", [t.title for t in report.top(3)])

        # Step 2: 키워드 수집
        await ws.send_json({"step": "keyword_collect", "status": "running"})
        kw_map = {}
        for title in selected:
            kws = await _pipeline.detector.discover_keywords(title)
            kw_map[title] = kws
        await ws.send_json({
            "step": "keyword_collect",
            "status": "awaiting_input",
            "data": kw_map,
        })
        kw_confirm = await ws.receive_json()  # 사용자가 수정한 키워드

        # Step 3: 포화도
        await ws.send_json({"step": "saturation", "status": "running"})
        analyses = {}
        for title, kws in kw_map.items():
            analyses[title] = await _pipeline._analyze_keywords(kws[:20], title)
        await ws.send_json({
            "step": "saturation",
            "status": "awaiting_input",
            "data": {t: a[:10] for t, a in analyses.items()},
        })
        await ws.receive_json()  # 확인

        # Step 4: 기획안
        await ws.send_json({"step": "plan_generate", "status": "running"})
        plans = []
        for title, ana in analyses.items():
            p = await _pipeline.generator.generate_multi_platform(title, category, ana, platforms)
            plans.extend(p)
        await ws.send_json({
            "step": "plan_generate",
            "status": "completed",
            "data": plans,
        })

    except WebSocketDisconnect:
        pass
