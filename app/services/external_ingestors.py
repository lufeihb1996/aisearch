import datetime
import html
import logging
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List
import httpx

from app.core.config import get_system_proxy
from app.services.ranker_service import (
    AI_HINT_RE,
    classify_project_link,
    compute_signal_score,
    derive_canonical_key,
)

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


class ExternalIngestors:
    async def fetch_huggingface_trending(self, limit: int = 22) -> List[Dict[str, Any]]:
        proxy = get_system_proxy()
        items: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=18.0) as client:
                resp = await client.get(
                    f"https://huggingface.co/api/trending?limit={limit}",
                    headers={"user-agent": UA},
                )
                if resp.status_code != 200:
                    logger.warning(f"HF Trending HTTP {resp.status_code}")
                    return []
                raw_list = resp.json().get("recentlyTrending", [])
                for entry in raw_list:
                    rtype = entry.get("repoType", "model")
                    rdata = entry.get("repoData", {}) or {}
                    repo_id = rdata.get("id") or rdata.get("name")
                    if not repo_id:
                        continue
                    author_Obj = rdata.get("authorData", {}) or {}
                    author_name = author_Obj.get("fullname") or rdata.get("author") or repo_id.split("/")[0]
                    avatar = author_Obj.get("avatarUrl", "")
                    if avatar and avatar.startswith("/"):
                        avatar = f"https://huggingface.co{avatar}"

                    likes = int(rdata.get("likes", 0) or 0)
                    downloads = int(rdata.get("downloads", 0) or 0)
                    pipeline_tag = rdata.get("pipeline_tag") or rtype

                    if rtype == "space":
                        url = f"https://huggingface.co/spaces/{repo_id}"
                        kind = "hf_space"
                        label = f"HF Space 在线试玩 · {repo_id}"
                        badge = "HF Space 试玩榜"
                    elif rtype == "dataset":
                        url = f"https://huggingface.co/datasets/{repo_id}"
                        kind = "huggingface"
                        label = f"HF Dataset · {repo_id}"
                        badge = "HuggingFace 飙升"
                    else:
                        url = f"https://huggingface.co/{repo_id}"
                        kind = "huggingface"
                        label = f"HF 模型权重 · {repo_id}"
                        badge = "HuggingFace 飙升"

                    desc_parts = [f"[{rtype.upper()} · {pipeline_tag}] {repo_id}"]
                    if rdata.get("shortDescription"):
                        desc_parts.append(str(rdata["shortDescription"]))
                    if downloads:
                        desc_parts.append(f"近期下载量: {downloads:,} · 点赞: {likes:,}")
                    else:
                        desc_parts.append(f"HuggingFace 热度赞: {likes:,}")

                    links = [{"label": label, "url": url, "kind": kind}]
                    it: Dict[str, Any] = {
                        "id": f"hf:{rtype}:{repo_id}",
                        "source": "huggingface",
                        "source_badge": badge,
                        "author": author_name,
                        "author_handle": repo_id.split("/")[0],
                        "author_followers": 0,
                        "raw_title": f"{repo_id} ({pipeline_tag})",
                        "raw_text": "\n".join(desc_parts),
                        "original_url": url,
                        "project_links": links,
                        "video_url": "",
                        "image_url": rdata.get("thumbnail") or "",
                        "metrics": {"likes": likes, "downloads": downloads},
                        "created_at_ts": int(time.time()),
                    }
                    it["canonical_key"] = derive_canonical_key(it["id"], links)
                    it["signal_score"] = compute_signal_score(it)
                    items.append(it)
        except Exception as e:
            logger.warning(f"HF Trending fetch error: {e}")
        return items

    async def fetch_github_surging_repos(self, days: int = 12, limit: int = 22) -> List[Dict[str, Any]]:
        proxy = get_system_proxy()
        since_date = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        items: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=18.0) as client:
                # Two lightweight queries: general fast-rising new repos (filtered for AI/builder relevance) + explicit AI/LLM/vision new repos
                queries = [
                    f"created:>{since_date} stars:>60",
                    f"(llm OR agent OR comfyui OR diffusion OR mcp OR tts OR voice OR 3d OR model) created:>{since_date} stars:>25",
                ]
                seen_full: set[str] = set()
                for q in queries:
                    resp = await client.get(
                        "https://api.github.com/search/repositories",
                        params={"q": q, "sort": "stars", "order": "desc", "per_page": limit},
                        headers={"user-agent": UA, "accept": "application/vnd.github+json"},
                    )
                    if resp.status_code != 200:
                        continue
                    for repo in resp.json().get("items", []):
                        full_name = repo.get("full_name", "")
                        if not full_name or full_name in seen_full:
                            continue
                        desc = (repo.get("description") or "").strip()
                        topics = repo.get("topics") or []
                        blob = f"{full_name} {desc} {' '.join(topics)}"
                        if not AI_HINT_RE.search(blob):
                            continue
                        seen_full.add(full_name)

                        stars = int(repo.get("stargazers_count", 0) or 0)
                        forks = int(repo.get("forks_count", 0) or 0)
                        lang = repo.get("language") or ""
                        html_url = repo.get("html_url", f"https://github.com/{full_name}")
                        homepage = (repo.get("homepage") or "").strip()

                        links = [{"label": f"GitHub · {full_name}", "url": html_url, "kind": "github"}]
                        if homepage and homepage.startswith(("http://", "https://")):
                            hp_info = classify_project_link(homepage)
                            if hp_info and hp_info["url"] != html_url:
                                links.append(hp_info)

                        owner = (repo.get("owner") or {}).get("login", full_name.split("/")[0])
                        text_lines = [
                            f"{full_name} — {desc}" if desc else full_name,
                            f"语言: {lang or 'Multi'} · 新近暴涨 ★ {stars:,} Stars · Forks: {forks:,}",
                        ]
                        if topics:
                            text_lines.append(f"标签: {', '.join(topics[:8])}")

                        it: Dict[str, Any] = {
                            "id": f"gh:{full_name.lower()}",
                            "source": "github",
                            "source_badge": "GitHub 暴涨新库",
                            "author": owner,
                            "author_handle": f"@{owner}",
                            "author_followers": 0,
                            "raw_title": f"{full_name}: {desc[:90]}" if desc else full_name,
                            "raw_text": "\n".join(text_lines),
                            "original_url": html_url,
                            "project_links": links,
                            "video_url": "",
                            "image_url": "",
                            "metrics": {"stars": stars, "forks": forks},
                            "created_at_ts": int(time.time()),
                        }
                        it["canonical_key"] = derive_canonical_key(it["id"], links)
                        it["signal_score"] = compute_signal_score(it)
                        items.append(it)
        except Exception as e:
            logger.warning(f"GitHub surging fetch error: {e}")
        return items[:limit]

    async def fetch_reddit_communities(self) -> List[Dict[str, Any]]:
        """
        Single combined RSS request for r/LocalLLaMA + r/StableDiffusion + r/comfyui to avoid HTTP 429!
        """
        proxy = get_system_proxy()
        items: List[Dict[str, Any]] = []
        url = "https://www.reddit.com/r/LocalLLaMA+StableDiffusion+comfyui/top/.rss?t=day&limit=25"
        try:
            async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=18.0) as client:
                resp = await client.get(
                    url,
                    headers={
                        "user-agent": UA,
                        "accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
                    },
                )
                if resp.status_code != 200 or "<entry>" not in resp.text:
                    logger.warning(f"Reddit RSS HTTP {resp.status_code}")
                    return []

                ns = {"atom": "http://www.w3.org/2005/Atom", "media": "http://search.yahoo.com/mrss/"}
                root = ET.fromstring(resp.text)
                for entry in root.findall("atom:entry", ns):
                    eid = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
                    title = html.unescape(entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
                    link_el = entry.find("atom:link", ns)
                    post_url = link_el.attrib.get("href", "") if link_el is not None else ""
                    cat_el = entry.find("atom:category", ns)
                    sub = cat_el.attrib.get("term", "Reddit") if cat_el is not None else "Reddit"
                    author_name = (
                        entry.findtext("atom:author/atom:name", default="", namespaces=ns) or ""
                    ).strip()
                    raw_html = entry.findtext("atom:content", default="", namespaces=ns) or ""
                    unescaped = html.unescape(raw_html)

                    # Extract external links inside Reddit post body (GitHub, HuggingFace, Civitai, ArXiv, etc.)
                    ext_urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', unescaped)
                    links: List[Dict[str, str]] = []
                    seen_u: set[str] = set()
                    for u in ext_urls:
                        info = classify_project_link(u)
                        if info and info["url"] not in seen_u:
                            seen_u.add(info["url"])
                            links.append(info)

                    thumb_el = entry.find("media:thumbnail", ns)
                    img_url = thumb_el.attrib.get("url", "") if thumb_el is not None else ""

                    plain_body = re.sub(r"<[^>]+>", " ", unescaped)
                    plain_body = re.sub(r"\s+", " ", plain_body).strip()
                    plain_body = re.sub(r"submitted by\s+/u/\S+\s*\[link\]\s*\[comments\]", "", plain_body).strip()

                    full_text = f"{title}\n{plain_body}".strip()[:1600]
                    if not title:
                        continue

                    it: Dict[str, Any] = {
                        "id": f"rd:{eid or hash(post_url)}",
                        "source": "reddit",
                        "source_badge": f"Reddit r/{sub}",
                        "author": author_name.removeprefix("/u/"),
                        "author_handle": author_name,
                        "author_followers": 0,
                        "raw_title": title[:140],
                        "raw_text": full_text,
                        "original_url": post_url,
                        "project_links": links,
                        "video_url": "",
                        "image_url": img_url,
                        "metrics": {"subreddit": sub},
                        "created_at_ts": int(time.time()),
                    }
                    it["canonical_key"] = derive_canonical_key(it["id"], links)
                    it["signal_score"] = compute_signal_score(it)
                    items.append(it)
        except Exception as e:
            logger.warning(f"Reddit RSS parse error: {e}")
        return items

    async def fetch_hackernews_show_hn(self, limit: int = 20) -> List[Dict[str, Any]]:
        proxy = get_system_proxy()
        items: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=15.0) as client:
                resp = await client.get(
                    "https://hn.algolia.com/api/v1/search_by_date",
                    params={
                        "tags": "show_hn",
                        "numericFilters": "points>12",
                        "hitsPerPage": 40,
                    },
                    headers={"user-agent": UA},
                )
                if resp.status_code != 200:
                    return []
                for hit in resp.json().get("hits", []):
                    oid = str(hit.get("objectID") or "")
                    title = (hit.get("title") or "").strip()
                    story_text = html.unescape(re.sub(r"<[^>]+>", " ", hit.get("story_text") or "")).strip()
                    target_url = (hit.get("url") or "").strip()
                    blob = f"{title} {story_text} {target_url}"
                    if not AI_HINT_RE.search(blob):
                        continue

                    pts = int(hit.get("points", 0) or 0)
                    comments = int(hit.get("num_comments", 0) or 0)
                    hn_url = f"https://news.ycombinator.com/item?id={oid}"
                    links: List[Dict[str, str]] = []
                    if target_url:
                        info = classify_project_link(target_url)
                        if info:
                            links.append(info)

                    clean_title = re.sub(r"^Show HN:\s*", "", title, flags=re.IGNORECASE).strip()
                    it: Dict[str, Any] = {
                        "id": f"hn:{oid}",
                        "source": "hackernews",
                        "source_badge": "HN 极客手搓",
                        "author": hit.get("author") or "hacker",
                        "author_handle": f"hn/{hit.get('author', '')}",
                        "author_followers": 0,
                        "raw_title": clean_title[:140],
                        "raw_text": f"{title}\n{story_text[:1000]}".strip(),
                        "original_url": target_url or hn_url,
                        "project_links": links,
                        "video_url": "",
                        "image_url": "",
                        "metrics": {"points": pts, "comments": comments, "hn_url": hn_url},
                        "created_at_ts": int(hit.get("created_at_i") or time.time()),
                    }
                    it["canonical_key"] = derive_canonical_key(it["id"], links)
                    it["signal_score"] = compute_signal_score(it)
                    items.append(it)
                    if len(items) >= limit:
                        break
        except Exception as e:
            logger.warning(f"HN Show HN fetch error: {e}")
        return items


external_ingestors = ExternalIngestors()
