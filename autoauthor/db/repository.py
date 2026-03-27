"""autoauthor/db/repository.py — CRUD 연산"""
from typing import Optional, Union
import json
import re
import sqlite3
from datetime import datetime
from ..sources.base import TrendItem


def _norm(text: str) -> str:
    return re.sub(r'[^가-힣a-zA-Z0-9]', '', text).lower()


class Repository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ── Contents ──
    def upsert_content(self, title: str, content_type: str = "movie",
                       tmdb_id: Optional[int] = None, metadata: Optional[dict] = None) -> int:
        norm = _norm(title)
        row = self.conn.execute(
            "SELECT id FROM contents WHERE normalized_title = ?", (norm,)
        ).fetchone()
        if row:
            self.conn.execute(
                "UPDATE contents SET updated_at = datetime('now'), tmdb_id = COALESCE(?, tmdb_id) WHERE id = ?",
                (tmdb_id, row["id"]))
            self.conn.commit()
            return row["id"]
        else:
            cur = self.conn.execute(
                "INSERT INTO contents (title, normalized_title, content_type, tmdb_id, metadata) VALUES (?,?,?,?,?)",
                (title, norm, content_type, tmdb_id, json.dumps(metadata or {}, ensure_ascii=False)))
            self.conn.commit()
            return cur.lastrowid

    # ── Trend Snapshots ──
    def save_trend_snapshot(self, content_id: int, source: str, rank: int,
                            score: float, metadata: Optional[dict] = None):
        self.conn.execute(
            "INSERT INTO trend_snapshots (content_id, source, rank, score, metadata) VALUES (?,?,?,?,?)",
            (content_id, source, rank, score, json.dumps(metadata or {}, ensure_ascii=False)))
        self.conn.commit()

    def save_trend_report(self, items: list[TrendItem]):
        """TrendReport의 ranked_contents를 일괄 저장"""
        for item in items:
            cid = self.upsert_content(
                item.title, item.content_type,
                tmdb_id=item.metadata.get("tmdb_id"),
                metadata=item.metadata,
            )
            self.save_trend_snapshot(cid, item.source, item.rank, item.score, item.metadata)

    # ── Keywords ──
    def upsert_keyword(self, keyword: str, content_id: Optional[int] = None,
                       search_intent: str = "exploratory") -> int:
        norm = _norm(keyword)
        row = self.conn.execute(
            "SELECT id FROM keywords WHERE normalized_keyword = ?", (norm,)
        ).fetchone()
        if row:
            return row["id"]
        cur = self.conn.execute(
            "INSERT INTO keywords (keyword, normalized_keyword, content_id, search_intent) VALUES (?,?,?,?)",
            (keyword, norm, content_id, search_intent))
        self.conn.commit()
        return cur.lastrowid

    def save_keyword_analysis(self, keyword_id: int, blog_comp: int, view_comp: int,
                               score: float, saturation: str, trend: str, has_demand: bool):
        self.conn.execute(
            """INSERT INTO keyword_analyses
               (keyword_id, blog_competition, view_competition, opportunity_score,
                saturation_grade, trend_grade, has_demand)
               VALUES (?,?,?,?,?,?,?)""",
            (keyword_id, blog_comp, view_comp, score, saturation, trend, int(has_demand)))
        self.conn.commit()

    # ── Content Plans ──
    def save_plan(self, content_id: Optional[int], plan_type: str, title: str,
                  structure: list[dict], keywords: list[str], ai_model: str) -> int:
        cur = self.conn.execute(
            """INSERT INTO content_plans (content_id, plan_type, title, structure, target_keywords, ai_model)
               VALUES (?,?,?,?,?,?)""",
            (content_id, plan_type, title,
             json.dumps(structure, ensure_ascii=False),
             json.dumps(keywords, ensure_ascii=False),
             ai_model))
        self.conn.commit()
        return cur.lastrowid

    # ── Pipeline Runs ──
    def start_run(self, mode: str, category: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO pipeline_runs (mode, category) VALUES (?,?)", (mode, category))
        self.conn.commit()
        return cur.lastrowid

    def complete_run(self, run_id: int, contents: int, keywords: int, plans: int,
                     duration: float, coverage: str):
        self.conn.execute(
            """UPDATE pipeline_runs SET status='completed', contents_found=?, keywords_analyzed=?,
               plans_generated=?, duration_seconds=?, source_coverage=?, completed_at=datetime('now')
               WHERE id=?""",
            (contents, keywords, plans, duration, coverage, run_id))
        self.conn.commit()

    # ── 분석 쿼리 ──
    def get_trending_contents(self, days: int = 7, limit: int = 20) -> list[dict]:
        rows = self.conn.execute(f"""
            SELECT c.title, c.content_type,
                   AVG(t.score) as avg_score,
                   COUNT(DISTINCT t.source) as source_count,
                   GROUP_CONCAT(DISTINCT t.source) as sources
            FROM contents c
            JOIN trend_snapshots t ON c.id = t.content_id
            WHERE t.collected_at >= datetime('now', '-{days} days')
            GROUP BY c.id
            ORDER BY avg_score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_golden_keywords(self, limit: int = 20) -> list[dict]:
        rows = self.conn.execute("""
            SELECT k.keyword, ka.opportunity_score, ka.saturation_grade,
                   ka.has_demand, c.title as related_content
            FROM keywords k
            JOIN keyword_analyses ka ON k.id = ka.keyword_id
            LEFT JOIN contents c ON k.content_id = c.id
            WHERE ka.saturation_grade IN ('blue', 'purple') AND ka.has_demand = 1
            ORDER BY ka.opportunity_score DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
