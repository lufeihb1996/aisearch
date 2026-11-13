import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import IS_VERCEL, is_supabase_enabled
from app.core.supabase_store import supabase_store

# On Vercel Serverless (/var/task is read-only), fallback SQLite path uses /tmp if Supabase is not set yet
DB_DIR = Path("/tmp/ai_radar_data") if IS_VERCEL else (Path(__file__).resolve().parent.parent / "data")
DB_PATH = DB_DIR / "ai_radar.db"


class RadarDatabase:
    """
    Dual-mode intelligence store:
    - Automatically uses Supabase Postgres (`public.radar_items` + `public.radar_settings`) when
      `SUPABASE_URL` + (`SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY`) are configured.
    - Seamlessly falls back to local SQLite (`app/data/ai_radar.db`) for zero-config local use.
    """

    def __init__(self) -> None:
        self._sqlite_initialized = False

    def _use_cloud(self) -> bool:
        return is_supabase_enabled()

    def _connect(self) -> sqlite3.Connection:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_init(self) -> None:
        if self._use_cloud():
            supabase_store.ensure_init()
            return
        if self._sqlite_initialized:
            return
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS items (
                        id TEXT PRIMARY KEY,
                        canonical_key TEXT NOT NULL,
                        source TEXT NOT NULL,
                        source_badge TEXT NOT NULL,
                        sources_merged TEXT DEFAULT '[]',
                        author TEXT DEFAULT '',
                        author_handle TEXT DEFAULT '',
                        author_followers INTEGER DEFAULT 0,
                        raw_title TEXT DEFAULT '',
                        raw_text TEXT DEFAULT '',
                        zh_title TEXT DEFAULT '',
                        zh_highlights TEXT DEFAULT '[]',
                        original_url TEXT DEFAULT '',
                        project_links TEXT DEFAULT '[]',
                        video_url TEXT DEFAULT '',
                        image_url TEXT DEFAULT '',
                        metrics TEXT DEFAULT '{}',
                        signal_score REAL DEFAULT 0.0,
                        jev_category TEXT DEFAULT 'PENDING',
                        jev_playability TEXT DEFAULT 'PENDING',
                        jev_score REAL DEFAULT 0.0,
                        jev_hype_prob REAL DEFAULT 0.0,
                        jev_evaluated INTEGER DEFAULT 0,
                        zh_translated INTEGER DEFAULT 0,
                        starred INTEGER DEFAULT 0,
                        created_at_ts INTEGER DEFAULT 0,
                        discovered_at INTEGER NOT NULL
                    );
                    """
                )
                conn.execute("CREATE INDEX IF NOT EXISTS idx_items_canonical ON items(canonical_key);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_items_score ON items(jev_score DESC, signal_score DESC);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_items_source ON items(source, discovered_at DESC);")
            self._sqlite_initialized = True
        finally:
            conn.close()

    def get_known_ids(self, prefix: Optional[str] = None, limit: int = 5000) -> Set[str]:
        if self._use_cloud():
            return supabase_store.get_known_ids(prefix=prefix, limit=limit)
        self.ensure_init()
        conn = self._connect()
        try:
            cur = conn.cursor()
            if prefix:
                cur.execute(
                    "SELECT id FROM items WHERE id LIKE ? ORDER BY discovered_at DESC LIMIT ?",
                    (f"{prefix}%", limit),
                )
            else:
                cur.execute(
                    "SELECT id FROM items ORDER BY discovered_at DESC LIMIT ?",
                    (limit,),
                )
            return {row["id"] for row in cur.fetchall()}
        finally:
            conn.close()

    def upsert_raw_items(self, items: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        if self._use_cloud():
            return supabase_store.upsert_raw_items(items)
        self.ensure_init()
        if not items:
            return 0, []
        now = int(time.time())
        inserted = 0
        new_ids: List[str] = []
        conn = self._connect()
        try:
            with conn:
                for it in items:
                    item_id = it["id"]
                    ckey = it.get("canonical_key") or item_id
                    cur = conn.execute(
                        "SELECT * FROM items WHERE id = ? OR canonical_key = ? LIMIT 1",
                        (item_id, ckey),
                    )
                    existing = cur.fetchone()
                    if existing:
                        merged_sources = set(json.loads(existing["sources_merged"] or "[]"))
                        merged_sources.add(existing["source_badge"])
                        merged_sources.add(it.get("source_badge", it["source"]))

                        existing_links = json.loads(existing["project_links"] or "[]")
                        seen_urls = {lk.get("url") for lk in existing_links}
                        for lk in it.get("project_links", []):
                            if lk.get("url") and lk["url"] not in seen_urls:
                                existing_links.append(lk)
                                seen_urls.add(lk["url"])

                        video_url = existing["video_url"] or it.get("video_url", "")
                        image_url = existing["image_url"] or it.get("image_url", "")
                        new_sig = max(float(existing["signal_score"] or 0), float(it.get("signal_score", 0)))
                        if len(merged_sources) > 1:
                            new_sig = min(100.0, new_sig + 8.0)

                        old_m = json.loads(existing["metrics"] or "{}")
                        new_m = it.get("metrics", {})
                        merged_m = dict(old_m)
                        for mk, mv in new_m.items():
                            if isinstance(mv, (int, float)) and isinstance(old_m.get(mk), (int, float)):
                                merged_m[mk] = max(old_m[mk], mv)
                            elif mv and not old_m.get(mk):
                                merged_m[mk] = mv

                        conn.execute(
                            """
                            UPDATE items
                            SET sources_merged = ?,
                                project_links = ?,
                                video_url = ?,
                                image_url = ?,
                                metrics = ?,
                                signal_score = ?
                            WHERE id = ?
                            """,
                            (
                                json.dumps(list(merged_sources), ensure_ascii=False),
                                json.dumps(existing_links, ensure_ascii=False),
                                video_url,
                                image_url,
                                json.dumps(merged_m, ensure_ascii=False),
                                round(new_sig, 2),
                                existing["id"],
                            ),
                        )
                    else:
                        conn.execute(
                            """
                            INSERT INTO items (
                                id, canonical_key, source, source_badge, sources_merged,
                                author, author_handle, author_followers,
                                raw_title, raw_text, zh_title, zh_highlights,
                                original_url, project_links, video_url, image_url,
                                metrics, signal_score, jev_category, jev_playability,
                                jev_score, jev_hype_prob, jev_evaluated, zh_translated,
                                starred, created_at_ts, discovered_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                item_id,
                                ckey,
                                it["source"],
                                it.get("source_badge", it["source"]),
                                json.dumps([it.get("source_badge", it["source"])], ensure_ascii=False),
                                it.get("author", ""),
                                it.get("author_handle", ""),
                                int(it.get("author_followers", 0) or 0),
                                it.get("raw_title", ""),
                                it.get("raw_text", ""),
                                it.get("zh_title", ""),
                                json.dumps(it.get("zh_highlights", []), ensure_ascii=False),
                                it.get("original_url", ""),
                                json.dumps(it.get("project_links", []), ensure_ascii=False),
                                it.get("video_url", ""),
                                it.get("image_url", ""),
                                json.dumps(it.get("metrics", {}), ensure_ascii=False),
                                round(float(it.get("signal_score", 0.0)), 2),
                                it.get("jev_category", "PENDING"),
                                it.get("jev_playability", "PENDING"),
                                float(it.get("jev_score", 0.0)),
                                float(it.get("jev_hype_prob", 0.0)),
                                int(it.get("jev_evaluated", 0)),
                                int(it.get("zh_translated", 0)),
                                0,
                                int(it.get("created_at_ts") or now),
                                now,
                            ),
                        )
                        inserted += 1
                        new_ids.append(item_id)
            return inserted, new_ids
        finally:
            conn.close()

    def get_unevaluated_top(
        self,
        limit: int = 28,
        preferred_sources: Optional[List[str]] = None,
        priority_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if self._use_cloud():
            return supabase_store.get_unevaluated_top(
                limit=limit, preferred_sources=preferred_sources, priority_ids=priority_ids
            )
        self.ensure_init()
        conn = self._connect()
        try:
            fresh_cutoff = int(time.time()) - 86400
            expanded: List[str] = []
            for s in (preferred_sources or []):
                if s == "x":
                    expanded.extend(["x_home", "x_search"])
                else:
                    expanded.append(s)

            params: List[Any] = []
            order_clauses: List[str] = []

            if expanded:
                src_ph = ",".join("?" for _ in expanded)
                order_clauses.append(f"CASE WHEN source IN ({src_ph}) THEN 0 ELSE 1 END")
                params.extend(expanded)

            clean_prio = [pid for pid in (priority_ids or []) if pid][:300]
            if clean_prio:
                prio_ph = ",".join("?" for _ in clean_prio)
                order_clauses.append(
                    f"CASE WHEN id IN ({prio_ph}) THEN 0 WHEN discovered_at >= ? THEN 1 ELSE 2 END"
                )
                params.extend(clean_prio)
                params.append(fresh_cutoff)
            else:
                order_clauses.append("CASE WHEN discovered_at >= ? THEN 0 ELSE 1 END")
                params.append(fresh_cutoff)

            order_clauses.extend(["signal_score DESC", "created_at_ts DESC"])
            params.append(limit)

            cur = conn.execute(
                f"""
                WITH ranked AS (
                    SELECT *,
                           ((ROW_NUMBER() OVER (PARTITION BY source_badge ORDER BY signal_score DESC, created_at_ts DESC) - 1) / 5) AS ch_wave
                    FROM items
                    WHERE jev_evaluated = 0
                )
                SELECT * FROM ranked
                ORDER BY {', '.join(order_clauses[:2])}, ch_wave ASC, signal_score DESC, created_at_ts DESC
                LIMIT ?
                """ if len(order_clauses) >= 4 else f"""
                WITH ranked AS (
                    SELECT *,
                           ((ROW_NUMBER() OVER (PARTITION BY source_badge ORDER BY signal_score DESC, created_at_ts DESC) - 1) / 5) AS ch_wave
                    FROM items
                    WHERE jev_evaluated = 0
                )
                SELECT * FROM ranked
                ORDER BY {order_clauses[0]}, ch_wave ASC, signal_score DESC, created_at_ts DESC
                LIMIT ?
                """,
                tuple(params),
            )
            return [self._row_to_dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_untranslated_approved(
        self,
        limit: int = 16,
        preferred_sources: Optional[List[str]] = None,
        min_jev_score: float = 70.0,
        priority_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if self._use_cloud():
            return supabase_store.get_untranslated_approved(
                limit=limit,
                preferred_sources=preferred_sources,
                min_jev_score=min_jev_score,
                priority_ids=priority_ids,
            )
        self.ensure_init()
        conn = self._connect()
        try:
            expanded: List[str] = []
            for s in (preferred_sources or []):
                if s == "x":
                    expanded.extend(["x_home", "x_search"])
                elif s:
                    expanded.append(s)

            clean_prio = [str(pid).strip() for pid in (priority_ids or []) if str(pid).strip()][:100]
            order_parts: List[str] = []
            params: List[Any] = [float(min_jev_score)]

            if clean_prio:
                prio_ph = ",".join("?" for _ in clean_prio)
                order_parts.append(f"CASE WHEN id IN ({prio_ph}) THEN 0 ELSE 1 END")
                params.extend(clean_prio)
            if expanded:
                src_ph = ",".join("?" for _ in expanded)
                order_parts.append(f"CASE WHEN source IN ({src_ph}) THEN 0 ELSE 1 END")
                params.extend(expanded)

            order_parts.extend(["jev_score DESC", "signal_score DESC"])
            params.append(limit)

            cur = conn.execute(
                f"""
                SELECT * FROM items
                WHERE jev_evaluated = 1
                  AND jev_category != 'NOISE'
                  AND jev_hype_prob < 72.0
                  AND jev_score >= ?
                  AND zh_translated = 0
                ORDER BY {', '.join(order_parts)}
                LIMIT ?
                """,
                tuple(params),
            )
            return [self._row_to_dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def get_items_by_ids(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        if not item_ids:
            return []
        if self._use_cloud():
            return supabase_store.get_items_by_ids(item_ids)
        self.ensure_init()
        conn = self._connect()
        try:
            placeholders = ",".join("?" for _ in item_ids)
            cur = conn.execute(
                f"SELECT * FROM items WHERE id IN ({placeholders})",
                tuple(item_ids),
            )
            return [self._row_to_dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

    def bulk_update_jev_evaluations(
        self, judged_map: Dict[str, Tuple[str, str, float, float]]
    ) -> None:
        if not judged_map:
            return
        if self._use_cloud():
            supabase_store.bulk_update_jev_evaluations(judged_map)
            return
        self.ensure_init()
        conn = self._connect()
        try:
            with conn:
                conn.executemany(
                    """
                    UPDATE items
                    SET jev_category = ?,
                        jev_playability = ?,
                        jev_score = ?,
                        jev_hype_prob = ?,
                        jev_evaluated = 1
                    WHERE id = ?
                    """,
                    [
                        (cat, play, round(float(jscore), 1), round(float(hype), 1), item_id)
                        for item_id, (cat, play, jscore, hype) in judged_map.items()
                    ],
                )
        finally:
            conn.close()

    def update_jev_evaluation(
        self,
        item_id: str,
        category: str,
        playability: str,
        score: float,
        hype_prob: float,
    ) -> None:
        if self._use_cloud():
            supabase_store.update_jev_evaluation(item_id, category, playability, score, hype_prob)
            return
        self.ensure_init()
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE items
                    SET jev_category = ?,
                        jev_playability = ?,
                        jev_score = ?,
                        jev_hype_prob = ?,
                        jev_evaluated = 1
                    WHERE id = ?
                    """,
                    (category, playability, round(score, 1), round(hype_prob, 1), item_id),
                )
        finally:
            conn.close()

    def update_translation(self, item_id: str, zh_title: str, zh_highlights: List[str]) -> None:
        if self._use_cloud():
            supabase_store.update_translation(item_id, zh_title, zh_highlights)
            return
        self.ensure_init()
        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE items
                    SET zh_title = ?,
                        zh_highlights = ?,
                        zh_translated = 1
                    WHERE id = ?
                    """,
                    (zh_title, json.dumps(zh_highlights, ensure_ascii=False), item_id),
                )
        finally:
            conn.close()

    def bulk_update_translations(
        self, zh_map: Dict[str, Tuple[str, List[str]]]
    ) -> None:
        if not zh_map:
            return
        if self._use_cloud():
            supabase_store.bulk_update_translations(zh_map)
            return
        self.ensure_init()
        conn = self._connect()
        try:
            with conn:
                conn.executemany(
                    """
                    UPDATE items
                    SET zh_title = ?,
                        zh_highlights = ?,
                        zh_translated = 1
                    WHERE id = ?
                    """,
                    [
                        (zt, json.dumps(zhl, ensure_ascii=False), item_id)
                        for item_id, (zt, zhl) in zh_map.items()
                        if item_id and zt
                    ],
                )
        finally:
            conn.close()

    def update_project_links(self, item_id: str, links: List[Dict[str, str]]) -> None:
        if self._use_cloud():
            supabase_store.update_project_links(item_id, links)
            return
        self.ensure_init()
        conn = self._connect()
        try:
            with conn:
                cur = conn.execute("SELECT project_links FROM items WHERE id = ?", (item_id,))
                row = cur.fetchone()
                if not row:
                    return
                existing = json.loads(row["project_links"] or "[]")
                seen = {x.get("url") for x in existing}
                for lk in links:
                    if lk.get("url") and lk["url"] not in seen:
                        existing.append(lk)
                        seen.add(lk["url"])
                conn.execute(
                    "UPDATE items SET project_links = ? WHERE id = ?",
                    (json.dumps(existing, ensure_ascii=False), item_id),
                )
        finally:
            conn.close()

    def toggle_star(self, item_id: str) -> Optional[int]:
        if self._use_cloud():
            return supabase_store.toggle_star(item_id)
        self.ensure_init()
        conn = self._connect()
        try:
            with conn:
                cur = conn.execute("SELECT starred FROM items WHERE id = ?", (item_id,))
                row = cur.fetchone()
                if not row:
                    return None
                new_val = 0 if row["starred"] else 1
                conn.execute("UPDATE items SET starred = ? WHERE id = ?", (new_val, item_id))
                return new_val
        finally:
            conn.close()

    def query_items(
        self,
        source: str = "all",
        category: str = "all",
        playability: str = "all",
        has_video: bool = False,
        starred_only: bool = False,
        include_noise: bool = False,
        q: str = "",
        sort: str = "score",
        hours: int = 0,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        if self._use_cloud():
            return supabase_store.query_items(
                source=source,
                category=category,
                playability=playability,
                has_video=has_video,
                starred_only=starred_only,
                include_noise=include_noise,
                q=q,
                sort=sort,
                hours=hours,
                page=page,
                page_size=page_size,
            )
        self.ensure_init()
        conn = self._connect()
        try:
            where = ["1=1"]
            params: List[Any] = []
            cutoff_ts = int(time.time()) - int(hours) * 3600 if hours and int(hours) > 0 else 0

            if not include_noise and not starred_only:
                where.append("jev_category != 'NOISE'")
                where.append("(jev_evaluated = 0 OR jev_hype_prob < 75.0)")

            if cutoff_ts > 0 and not starred_only:
                where.append("created_at_ts >= ?")
                params.append(cutoff_ts)

            if source != "all":
                raw_srcs = [s.strip() for s in source.split(",") if s.strip()]
                db_srcs: List[str] = []
                for s in raw_srcs:
                    if s == "x":
                        db_srcs.extend(["x_home", "x_search"])
                    else:
                        db_srcs.append(s)
                if db_srcs:
                    placeholders = ",".join("?" for _ in db_srcs)
                    where.append(f"source IN ({placeholders})")
                    params.extend(db_srcs)

            if category != "all":
                where.append("jev_category = ?")
                params.append(category)

            if playability != "all":
                where.append("jev_playability = ?")
                params.append(playability)

            if has_video:
                where.append("video_url != ''")

            if starred_only:
                where.append("starred = 1")

            if q.strip():
                kw = f"%{q.strip()}%"
                where.append("(zh_title LIKE ? OR raw_title LIKE ? OR raw_text LIKE ? OR zh_highlights LIKE ? OR author_handle LIKE ?)")
                params.extend([kw, kw, kw, kw, kw])

            if sort == "latest":
                order_sql = "created_at_ts DESC, jev_score DESC, signal_score DESC"
            elif sort == "views":
                order_sql = "CAST(COALESCE(json_extract(metrics, '$.views'), 0) AS INTEGER) DESC, signal_score DESC, jev_score DESC"
            elif sort == "bookmarks":
                order_sql = "signal_score DESC, jev_score DESC"
            elif sort == "score":
                order_sql = "jev_evaluated DESC, jev_score DESC, signal_score DESC, created_at_ts DESC"
            else:
                # Default 'combo': Jev technical score + 200k-view signal score + READY_NOW bonus - high hype penalty
                order_sql = (
                    "jev_evaluated DESC, "
                    "CASE WHEN jev_evaluated = 1 THEN ("
                    "  jev_score * 0.55 + signal_score * 0.45 "
                    "  + (CASE WHEN jev_playability = 'READY_NOW' THEN 6.0 WHEN jev_playability = 'WAITLIST_HYPE' THEN -10.0 ELSE 0.0 END) "
                    "  - MAX(0.0, (jev_hype_prob - 45.0) * 0.35)"
                    ") ELSE signal_score * 0.80 END DESC, "
                    "created_at_ts DESC"
                )

            where_clause = " AND ".join(where)
            total_cnt = conn.execute(
                f"SELECT COUNT(*) AS cnt FROM items WHERE {where_clause}",
                params,
            ).fetchone()["cnt"]

            safe_page_size = max(1, min(100, int(page_size or 10)))
            total_pages = max(1, (total_cnt + safe_page_size - 1) // safe_page_size)
            safe_page = min(max(1, int(page or 1)), total_pages)
            offset = (safe_page - 1) * safe_page_size

            sql = f"SELECT * FROM items WHERE {where_clause} ORDER BY {order_sql} LIMIT ? OFFSET ?"
            rows = [
                self._row_to_dict(r)
                for r in conn.execute(sql, [*params, safe_page_size, offset]).fetchall()
            ]

            cnt_where = ["jev_category != 'NOISE'", "(jev_evaluated = 0 OR jev_hype_prob < 75.0)"]
            cnt_params: List[Any] = []
            if cutoff_ts > 0:
                cnt_where.append("created_at_ts >= ?")
                cnt_params.append(cutoff_ts)
            counts_cur = conn.execute(
                f"""
                SELECT source, COUNT(*) AS cnt
                FROM items
                WHERE {' AND '.join(cnt_where)}
                GROUP BY source
                """,
                cnt_params,
            )
            source_counts = {r["source"]: r["cnt"] for r in counts_cur.fetchall()}
            star_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM items WHERE starred = 1").fetchone()["cnt"]

            return {
                "items": rows,
                "total": total_cnt,
                "page": safe_page,
                "page_size": safe_page_size,
                "total_pages": total_pages,
                "source_counts": {
                    "x": source_counts.get("x_home", 0) + source_counts.get("x_search", 0),
                    "huggingface": source_counts.get("huggingface", 0),
                    "github": source_counts.get("github", 0),
                    "reddit": source_counts.get("reddit", 0),
                    "hackernews": source_counts.get("hackernews", 0),
                    "starred": star_cnt,
                },
            }
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        for jcol, default in [
            ("sources_merged", []),
            ("zh_highlights", []),
            ("project_links", []),
            ("metrics", {}),
        ]:
            try:
                d[jcol] = json.loads(d.get(jcol) or json.dumps(default))
            except Exception:
                d[jcol] = default
        return d


radar_db = RadarDatabase()
