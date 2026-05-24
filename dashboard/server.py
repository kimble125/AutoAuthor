"""Local dashboard server for AutoAuthor.

Serves the static dashboard and exposes small JSON endpoints that call the
existing pipeline. This keeps the portfolio UI useful without adding a separate
frontend framework or database.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from aiohttp import web


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = Path(__file__).resolve().parent
LATEST_PATH = ROOT / "results" / "latest_portfolio.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autoauthor.pipeline import AutoAuthorPipeline  # noqa: E402


def _read_latest() -> dict:
    if not LATEST_PATH.exists():
        return {"mode": "empty", "rows": []}
    return json.loads(LATEST_PATH.read_text(encoding="utf-8"))


def _trend_item_to_dict(item) -> dict:
    return {
        "title": item.title,
        "content_type": item.content_type,
        "source": item.source,
        "rank": item.rank,
        "score": item.score,
        "metadata": item.metadata,
    }


async def latest(_request: web.Request) -> web.Response:
    return web.json_response(_read_latest())


async def trends(request: web.Request) -> web.Response:
    category = request.query.get("category", "drama")
    top = max(1, min(int(request.query.get("top", "8")), 12))
    pipeline = AutoAuthorPipeline()
    report = await pipeline.detector.detect(category)
    return web.json_response({
        "category": category,
        "items": [_trend_item_to_dict(item) for item in report.top(top)],
    })


async def analyze(request: web.Request) -> web.Response:
    body = await request.json()
    raw_titles = body.get("titles") or []
    if isinstance(raw_titles, str):
        raw_titles = [raw_titles]
    titles = [str(title).strip() for title in raw_titles if str(title).strip()][:3]
    if not titles:
        raise web.HTTPBadRequest(text="titles required")

    category = str(body.get("category") or "drama")
    pipeline = AutoAuthorPipeline()
    analyses_by_title = {}

    for title in titles:
        keywords = await pipeline.detector.discover_keywords(title)
        analyses_by_title[title] = await pipeline._analyze_keywords(keywords, title)

    csv_path = pipeline._export_unified_csv(analyses_by_title, "dashboard_drama")
    payload = _read_latest()
    payload["csv_path"] = csv_path
    return web.json_response(payload)


async def index(_request: web.Request) -> web.FileResponse:
    return web.FileResponse(DASHBOARD_DIR / "index.html")


def create_app() -> web.Application:
    app = web.Application(client_max_size=2 * 1024 * 1024)
    app.router.add_get("/", index)
    app.router.add_get("/api/latest", latest)
    app.router.add_get("/api/trends", trends)
    app.router.add_post("/api/analyze", analyze)
    app.router.add_static("/", DASHBOARD_DIR, show_index=False)
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoAuthor dashboard server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    web.run_app(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
