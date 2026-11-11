import asyncio
import re
import secrets
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import (
    ENV_FILE,
    IS_VERCEL,
    get_admin_password,
    get_openrouter_api_key,
    get_system_proxy,
    get_typesafe_api_key,
    is_supabase_enabled,
    settings,
)
from app.core.database import radar_db
from app.core.supabase_store import supabase_store
from app.services.external_ingestors import UA, external_ingestors
from app.services.jev_judge_service import jev_judge
from app.services.x_ingestor import x_ingestor

router = APIRouter(prefix="/api", tags=["Radar"])

ALLOWED_MEDIA_HOSTS = (
    "twimg.com",
    "redd.it",
    "redditmedia.com",
    "huggingface.co",
    "hf.space",
    "githubusercontent.com",
    "githubassets.com",
)

# Vercel Serverless has a 4.5MB response payload ceiling; clamp video Range chunks to 3MB
VERCEL_VIDEO_CHUNK_BYTES = 3 * 1024 * 1024

_media_client: Optional[httpx.AsyncClient] = None


def _get_media_client() -> httpx.AsyncClient:
    global _media_client
    if _media_client is None or _media_client.is_closed:
        _media_client = httpx.AsyncClient(
            proxy=get_system_proxy(),
            follow_redirects=True,
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=24, max_connections=48),
        )
    return _media_client


def _require_admin_if_configured(request: Request) -> None:
    expected = get_admin_password()
    if not expected:
        return
    provided = (request.headers.get("x-admin-password") or "").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(
            status_code=401,
            detail="Admin password required (set X-Admin-Password or configure in Settings modal)",
        )


class ScanRequest(BaseModel):
    sources: List[str] = Field(
        default_factory=lambda: ["x", "huggingface", "github", "reddit", "hackernews"]
    )
    max_judge: int = Field(default=24, ge=5, le=50)
    translate_model: Optional[str] = None


class StarRequest(BaseModel):
    id: str


class TranslateRequest(BaseModel):
    ids: List[str] = Field(default_factory=list)


class SettingsPayload(BaseModel):
    typesafe_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    twitter_auth_token: Optional[str] = None
    twitter_ct0: Optional[str] = None


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    radar_db.ensure_init()
    data = radar_db.query_items(page=1, page_size=1)
    return {
        "ok": True,
        "storage_backend": "supabase" if is_supabase_enabled() else "sqlite",
        "requires_admin_password": bool(get_admin_password()),
        "has_jev_key": bool(get_typesafe_api_key()),
        "has_openrouter_key": bool(get_openrouter_api_key()),
        "has_x_cookie": x_ingestor.is_configured(),
        "openrouter_model": settings.OPENROUTER_MODEL,
        "source_counts": data["source_counts"],
    }


@router.get("/items")
async def list_items(
    source: str = "all",
    category: str = "all",
    playability: str = "all",
    has_video: bool = False,
    starred: bool = False,
    include_noise: bool = False,
    q: str = "",
    sort: str = "score",
    hours: int = 0,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    return radar_db.query_items(
        source=source,
        category=category,
        playability=playability,
        has_video=has_video,
        starred_only=starred,
        include_noise=include_noise,
        q=q,
        sort=sort,
        hours=hours,
        page=page,
        page_size=page_size,
    )


@router.post("/scan", dependencies=[Depends(_require_admin_if_configured)])
async def run_scan(req: ScanRequest) -> Dict[str, Any]:
    radar_db.ensure_init()
    t0 = time.time()
    enabled = set(req.sources or [])
    tasks: Dict[str, Any] = {}

    if "huggingface" in enabled:
        tasks["huggingface"] = asyncio.create_task(external_ingestors.fetch_huggingface_trending(limit=20))
    if "github" in enabled:
        tasks["github"] = asyncio.create_task(external_ingestors.fetch_github_surging_repos(days=12, limit=20))
    if "reddit" in enabled:
        tasks["reddit"] = asyncio.create_task(external_ingestors.fetch_reddit_communities())
    if "hackernews" in enabled:
        tasks["hackernews"] = asyncio.create_task(external_ingestors.fetch_hackernews_show_hn(limit=18))
    if "x" in enabled and x_ingestor.is_configured():
        tasks["x_home"] = asyncio.create_task(x_ingestor.fetch_personal_feeds(pages_for_you=3, pages_following=2))

    fetched_by_source: Dict[str, int] = {}
    all_raw: List[Dict[str, Any]] = []
    hot_terms_for_x: List[str] = []

    if tasks:
        done_values = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, res in zip(tasks.keys(), done_values):
            if isinstance(res, list):
                fetched_by_source[name] = len(res)
                all_raw.extend(res)
                if name in ("huggingface", "github"):
                    for r in res[:6]:
                        title_head = (r.get("raw_title") or "").split(":")[0].split("(")[0].strip()
                        if title_head:
                            hot_terms_for_x.append(title_head)
            else:
                fetched_by_source[name] = 0

    known_x = radar_db.get_known_ids(prefix="x:", limit=5000) if "x" in enabled else set()

    if "x" in enabled and x_ingestor.is_configured():
        x_extra = await x_ingestor.fetch_broad_launches_and_reverse_terms(hot_terms_for_x, known_x)
        fetched_by_source["x_search"] = len(x_extra)
        all_raw.extend(x_extra)

    all_raw.sort(key=lambda x: float(x.get("signal_score", 0.0)), reverse=True)
    rescued_links_count = 0
    if "x" in enabled and x_ingestor.is_configured():
        fresh_x_raw = [c for c in all_raw if c["id"] not in known_x]
        rescued_map = await x_ingestor.rescue_author_reply_links(fresh_x_raw[:25], max_checks=6)
        for it in all_raw:
            if it["id"] in rescued_map:
                it["project_links"] = (it.get("project_links") or []) + rescued_map[it["id"]]
                rescued_links_count += len(rescued_map[it["id"]])

    inserted, new_ids = radar_db.upsert_raw_items(all_raw)
    new_id_set = set(new_ids)

    to_judge = radar_db.get_unevaluated_top(
        limit=req.max_judge,
        preferred_sources=list(enabled),
        priority_ids=new_ids,
    )
    judged_map = await jev_judge.evaluate_batch(to_judge)
    noise_filtered = 0
    new_judged_count = 0
    for item_id, (cat, play, jscore, hype) in judged_map.items():
        radar_db.update_jev_evaluation(item_id, cat, play, jscore, hype)
        if item_id in new_id_set:
            new_judged_count += 1
        if cat == "NOISE" or hype >= 75.0:
            noise_filtered += 1

    elapsed = round(time.time() - t0, 1)
    latest_view = radar_db.query_items(page=1, page_size=1)
    return {
        "ok": True,
        "elapsed_sec": elapsed,
        "fetched_by_source": fetched_by_source,
        "total_fetched": len(all_raw),
        "new_inserted": inserted,
        "rescued_comment_links": rescued_links_count,
        "jev_judged": len(judged_map),
        "jev_judged_new": new_judged_count,
        "jev_judged_backlog": max(0, len(judged_map) - new_judged_count),
        "noise_filtered": noise_filtered,
        "zh_distilled": 0,
        "source_counts": latest_view["source_counts"],
    }


@router.post("/star", dependencies=[Depends(_require_admin_if_configured)])
async def toggle_star_item(req: StarRequest) -> Dict[str, Any]:
    new_state = radar_db.toggle_star(req.id)
    return {"ok": new_state is not None, "id": req.id, "starred": new_state}


@router.post("/translate", dependencies=[Depends(_require_admin_if_configured)])
async def manual_translate_items(req: TranslateRequest) -> Dict[str, Any]:
    radar_db.ensure_init()
    clean_ids = [str(x).strip() for x in (req.ids or []) if str(x).strip()][:20]
    if not clean_ids:
        return {"ok": True, "translated": 0, "results": {}}
    items = radar_db.get_items_by_ids(clean_ids)
    if not items:
        return {"ok": True, "translated": 0, "results": {}}

    zh_map = await jev_judge.translate_and_distill_batch(
        items, model_override="deepseek/deepseek-v4-flash"
    )
    results: Dict[str, Any] = {}
    for item_id, (zt, zhl) in zh_map.items():
        radar_db.update_translation(item_id, zt, zhl)
        results[item_id] = {"zh_title": zt, "zh_highlights": zhl}

    return {
        "ok": True,
        "translated": len(results),
        "results": results,
    }


@router.post("/settings", dependencies=[Depends(_require_admin_if_configured)])
async def save_settings(payload: SettingsPayload) -> Dict[str, Any]:
    updates: Dict[str, str] = {}

    if payload.typesafe_api_key is not None and payload.typesafe_api_key.strip():
        val = payload.typesafe_api_key.strip()
        settings.TYPESAFE_API_KEY = val
        updates["TYPESAFE_API_KEY"] = val

    if payload.openrouter_api_key is not None and payload.openrouter_api_key.strip():
        val = payload.openrouter_api_key.strip()
        settings.OPENROUTER_API_KEY = val
        updates["OPENROUTER_API_KEY"] = val

    if payload.twitter_auth_token is not None and payload.twitter_auth_token.strip():
        val = payload.twitter_auth_token.strip()
        settings.TWITTER_AUTH_TOKEN = val
        updates["TWITTER_AUTH_TOKEN"] = val

    if payload.twitter_ct0 is not None and payload.twitter_ct0.strip():
        val = payload.twitter_ct0.strip()
        settings.TWITTER_CT0 = val
        updates["TWITTER_CT0"] = val

    # 1. Persist in Supabase `public.radar_settings` when cloud DB is active (works on read-only Vercel!)
    if updates and is_supabase_enabled():
        supabase_store.save_runtime_settings(updates)

    # 2. Persist in local `.env` when running locally (never write `/var/task/.env` on Vercel)
    if updates and not IS_VERCEL:
        env_vars: Dict[str, str] = {}
        if ENV_FILE.exists():
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    env_vars[k.strip()] = v.strip()
        env_vars.update(updates)
        ENV_FILE.write_text(
            "\n".join(f"{k}={v}" for k, v in env_vars.items()) + "\n",
            encoding="utf-8",
        )

    return await get_status()


def _clamp_vercel_range(range_hdr: Optional[str], url_path: str) -> Optional[str]:
    if not IS_VERCEL:
        return range_hdr
    is_video = url_path.lower().endswith((".mp4", ".mov", ".webm", ".m4v"))
    if not range_hdr:
        return f"bytes=0-{VERCEL_VIDEO_CHUNK_BYTES - 1}" if is_video else None
    m = re.match(r"^bytes=(\d+)-(\d*)$", range_hdr.strip())
    if not m:
        return range_hdr
    start = int(m.group(1))
    end_str = m.group(2)
    max_end = start + VERCEL_VIDEO_CHUNK_BYTES - 1
    if not end_str:
        return f"bytes={start}-{max_end}"
    end = min(int(end_str), max_end)
    return f"bytes={start}-{end}"


@router.get("/media")
async def proxy_media(url: str, request: Request) -> Response:
    """
    Streams external X / Reddit / HF / GitHub images & MP4 videos with Range support,
    anti-hotlink Referer headers, and 3MB chunk clamping for Vercel Serverless safety.
    """
    parsed = urlparse((url or "").strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not any(
        host == h or host.endswith(f".{h}") for h in ALLOWED_MEDIA_HOSTS
    ):
        raise HTTPException(status_code=400, detail="Unsupported media domain")

    up_headers: Dict[str, str] = {"User-Agent": UA}
    if "twimg.com" in host:
        up_headers["Referer"] = "https://x.com/"
    eff_range = _clamp_vercel_range(request.headers.get("range"), parsed.path or "")
    if eff_range:
        up_headers["Range"] = eff_range

    client = _get_media_client()
    try:
        req_up = client.build_request("GET", url, headers=up_headers)
        resp_up = await client.send(req_up, stream=True)
    except Exception:
        return Response(status_code=502)

    if resp_up.status_code >= 400:
        status_code = resp_up.status_code
        await resp_up.aclose()
        return Response(status_code=status_code)

    out_headers: Dict[str, str] = {
        "Cache-Control": "public, max-age=86400, s-maxage=86400",
        "Accept-Ranges": resp_up.headers.get("accept-ranges", "bytes"),
    }
    for h_name in ("content-type", "content-length", "content-range"):
        val = resp_up.headers.get(h_name)
        if val:
            out_headers[h_name] = val

    async def _stream():
        try:
            async for chunk in resp_up.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await resp_up.aclose()

    return StreamingResponse(
        _stream(),
        status_code=resp_up.status_code,
        headers=out_headers,
    )
