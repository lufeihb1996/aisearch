import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import httpx

from app.core.config import (
    apply_runtime_overrides,
    current_user_jwt,
    get_supabase_publishable_key,
    get_supabase_server_key,
    get_supabase_url,
    get_system_proxy,
)

logger = logging.getLogger(__name__)


class SupabaseRadarStore:
    """
    Zero-env-config Supabase client (matching MOSS_Krea_Studio pattern):
    - Public feed queries run directly with bundled `publishableKey` (`sb_publishable_...`).
    - Owner actions & secret `radar_settings` sync use either the signed-in owner's Supabase Auth JWT
      (`Authorization: Bearer <user_jwt>`) enforced by Postgres RLS (`app_metadata.radar_admin`),
      or `SUPABASE_SECRET_KEY` / `SUPABASE_SERVICE_ROLE_KEY` if configured.
    """

    def __init__(self) -> None:
        self._client: Optional[httpx.Client] = None
        self._settings_synced_at: float = 0.0

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                proxy=get_system_proxy(),
                timeout=httpx.Timeout(25.0, connect=8.0),
                limits=httpx.Limits(max_keepalive_connections=16, max_connections=32),
            )
        return self._client

    @staticmethod
    def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        srv_key = get_supabase_server_key()
        pub_key = get_supabase_publishable_key()
        user_jwt = (current_user_jwt.get() or "").strip()

        if srv_key:
            hdrs = {
                "apikey": srv_key,
                "Authorization": f"Bearer {srv_key}",
                "Content-Type": "application/json",
            }
        else:
            hdrs = {
                "apikey": pub_key,
                "Content-Type": "application/json",
            }
            if user_jwt:
                hdrs["Authorization"] = f"Bearer {user_jwt}"

        if extra:
            hdrs.update(extra)
        return hdrs

    @staticmethod
    def _rest_url(path: str) -> str:
        return f"{get_supabase_url()}/rest/v1/{path.lstrip('/')}"

    @staticmethod
    def _normalize_row(d: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(d)
        for jcol, default in (
            ("sources_merged", []),
            ("zh_highlights", []),
            ("project_links", []),
            ("metrics", {}),
        ):
            val = out.get(jcol)
            if isinstance(val, str):
                try:
                    out[jcol] = json.loads(val)
                except Exception:
                    out[jcol] = default
            elif val is None:
                out[jcol] = default
        return out

    def sync_runtime_settings(self, force: bool = False) -> Dict[str, str]:
        # Only attempt reading protected `radar_settings` when authenticated as admin or using server key
        if not get_supabase_server_key() and not current_user_jwt.get():
            return {}
        now = time.time()
        if not force and (now - self._settings_synced_at) < 45.0:
            return {}
        try:
            resp = self._get_client().get(
                self._rest_url("radar_settings"),
                params={"select": "key,value"},
                headers=self._headers(),
            )
            if resp.status_code == 200:
                rows = resp.json() or []
                kv = {r["key"]: r["value"] for r in rows if r.get("key") and r.get("value")}
                if kv:
                    apply_runtime_overrides(kv)
                    self._settings_synced_at = now
                return kv
        except Exception as e:
            logger.warning(f"Supabase runtime settings sync skipped: {e}")
        return {}

    def save_runtime_settings(self, kv: Dict[str, str]) -> None:
        clean_rows = [
            {"key": k, "value": v.strip()}
            for k, v in kv.items()
            if k and v and v.strip()
        ]
        if not clean_rows:
            return
        resp = self._get_client().post(
            self._rest_url("radar_settings"),
            params={"on_conflict": "key"},
            headers=self._headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
            json=clean_rows,
        )
        resp.raise_for_status()
        apply_runtime_overrides({r["key"]: r["value"] for r in clean_rows})
        self._settings_synced_at = time.time()

    def ensure_init(self) -> None:
        self.sync_runtime_settings(force=False)

    def get_known_ids(self, prefix: Optional[str] = None, limit: int = 5000) -> Set[str]:
        params: Dict[str, Any] = {
            "select": "id",
            "order": "discovered_at.desc",
            "limit": str(min(max(1, limit), 5000)),
        }
        if prefix:
            params["id"] = f"like.{prefix}*"
        resp = self._get_client().get(
            self._rest_url("radar_items"),
            params=params,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return {row["id"] for row in (resp.json() or []) if row.get("id")}

    def upsert_raw_items(self, items: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        if not items:
            return 0, []
        resp = self._get_client().post(
            self._rest_url("rpc/radar_upsert_items"),
            headers=self._headers(),
            json={"p_items": items},
        )
        resp.raise_for_status()
        data = resp.json() or {}
        return int(data.get("inserted", 0)), list(data.get("new_ids") or [])

    def get_unevaluated_top(
        self,
        limit: int = 28,
        preferred_sources: Optional[List[str]] = None,
        priority_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        clean_prio = [pid for pid in (priority_ids or []) if pid][:300]
        resp = self._get_client().post(
            self._rest_url("rpc/radar_get_unevaluated_top"),
            headers=self._headers(),
            json={
                "p_limit": int(limit or 28),
                "p_sources": list(preferred_sources) if preferred_sources else None,
                "p_priority_ids": clean_prio if clean_prio else None,
            },
        )
        resp.raise_for_status()
        return [self._normalize_row(r) for r in (resp.json() or [])]

    def get_untranslated_approved(
        self, limit: int = 24, preferred_sources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        params: Dict[str, str] = {
            "select": "*",
            "jev_evaluated": "eq.1",
            "jev_category": "neq.NOISE",
            "jev_hype_prob": "lt.72",
            "zh_translated": "eq.0",
            "order": "jev_score.desc,signal_score.desc",
            "limit": str(limit),
        }
        if preferred_sources:
            expanded: List[str] = []
            for s in preferred_sources:
                if s == "x":
                    expanded.extend(["x_home", "x_search"])
                elif s:
                    expanded.append(s)
            if expanded:
                quoted = ",".join(f'"{x}"' for x in expanded)
                params["source"] = f"in.({quoted})"
        resp = self._get_client().get(
            self._rest_url("radar_items"),
            params=params,
            headers=self._headers(),
        )
        resp.raise_for_status()
        return [self._normalize_row(r) for r in (resp.json() or [])]

    def get_items_by_ids(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        clean = [str(i).strip() for i in (item_ids or []) if str(i).strip()]
        if not clean:
            return []
        escaped = ",".join('"' + x.replace('"', '\\"') + '"' for x in clean)
        resp = self._get_client().get(
            self._rest_url("radar_items"),
            params={"select": "*", "id": f"in.({escaped})"},
            headers=self._headers(),
        )
        resp.raise_for_status()
        return [self._normalize_row(r) for r in (resp.json() or [])]

    def update_jev_evaluation(
        self,
        item_id: str,
        category: str,
        playability: str,
        score: float,
        hype_prob: float,
    ) -> None:
        resp = self._get_client().patch(
            self._rest_url("radar_items"),
            params={"id": f"eq.{item_id}"},
            headers=self._headers({"Prefer": "return=minimal"}),
            json={
                "jev_category": category,
                "jev_playability": playability,
                "jev_score": round(float(score), 1),
                "jev_hype_prob": round(float(hype_prob), 1),
                "jev_evaluated": 1,
            },
        )
        resp.raise_for_status()

    def update_translation(self, item_id: str, zh_title: str, zh_highlights: List[str]) -> None:
        resp = self._get_client().patch(
            self._rest_url("radar_items"),
            params={"id": f"eq.{item_id}"},
            headers=self._headers({"Prefer": "return=minimal"}),
            json={
                "zh_title": zh_title,
                "zh_highlights": zh_highlights,
                "zh_translated": 1,
            },
        )
        resp.raise_for_status()

    def update_project_links(self, item_id: str, links: List[Dict[str, str]]) -> None:
        rows = self.get_items_by_ids([item_id])
        if not rows:
            return
        existing = list(rows[0].get("project_links") or [])
        seen = {x.get("url") for x in existing if isinstance(x, dict)}
        for lk in links:
            if lk.get("url") and lk["url"] not in seen:
                existing.append(lk)
                seen.add(lk["url"])
        resp = self._get_client().patch(
            self._rest_url("radar_items"),
            params={"id": f"eq.{item_id}"},
            headers=self._headers({"Prefer": "return=minimal"}),
            json={"project_links": existing},
        )
        resp.raise_for_status()

    def toggle_star(self, item_id: str) -> Optional[int]:
        rows = self.get_items_by_ids([item_id])
        if not rows:
            return None
        new_val = 0 if rows[0].get("starred") else 1
        resp = self._get_client().patch(
            self._rest_url("radar_items"),
            params={"id": f"eq.{item_id}"},
            headers=self._headers({"Prefer": "return=minimal"}),
            json={"starred": new_val},
        )
        resp.raise_for_status()
        return new_val

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
        resp = self._get_client().post(
            self._rest_url("rpc/radar_query_items"),
            headers=self._headers(),
            json={
                "p_source": source or "all",
                "p_category": category or "all",
                "p_playability": playability or "all",
                "p_has_video": bool(has_video),
                "p_starred_only": bool(starred_only),
                "p_include_noise": bool(include_noise),
                "p_q": q or "",
                "p_sort": sort or "score",
                "p_hours": int(hours or 0),
                "p_page": int(page or 1),
                "p_page_size": int(page_size or 10),
            },
        )
        resp.raise_for_status()
        data = resp.json() or {}
        data["items"] = [self._normalize_row(r) for r in (data.get("items") or [])]
        return data


supabase_store = SupabaseRadarStore()
