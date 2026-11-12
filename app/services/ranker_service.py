import math
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

SPAM_PATTERNS = [
    r"comment\s+['\"`]?[a-z0-9_+-]{1,15}['\"`]?\s+(and\s+)?(i'?ll|to\s+get|for\s+the)\s+(dm|send)",
    r"reply\s+['\"`]?[a-z0-9_+-]{1,15}['\"`]?\s+and\s+i'?ll\s+send",
    r"retweet\s+and\s+comment",
    r"\bgiveaway\b",
    r"10\s+ai\s+tools\s+that\s+feel\s+illegal",
    r"\b\d+\s+(open[\s-]?source|github)\s+(repos|repositories)\s+(that|you\s+need)",
    r"bookmark\s+this\s+thread",
    r"点赞.{0,6}评论.{0,6}私信",
]
SPAM_RE = re.compile("|".join(SPAM_PATTERNS), re.IGNORECASE)

PURE_CRYPTO_TICKER_RE = re.compile(r"\$(BTC|ETH|SOL|DOGE|XRP|PEPE|SHIB|BNB)\b", re.IGNORECASE)
AI_HINT_RE = re.compile(
    r"\b(ai|llm|gpt|claude|gemini|qwen|deepseek|gemma|llama|mistral|minimax|moss|flux|wan|hunyuan|"
    r"diffusion|lora|comfyui|gguf|vram|gpu|cuda|openvino|mlx|ollama|vllm|huggingface|hf|github|repo|"
    r"open[\s-]?(source|weights)|model|agent|mcp|tts|voice|avatar|3d|splatting|arxiv|benchmark|"
    r"uncensored|quant|colab|modelscope|browser|cli|sdk|workflow|codegen|cursor|opencode)\b|"
    r"(开源|模型|显存|部署|算力|权重|微调|量化|智能体|工作流|生图|视频生成|数字人|语音克隆|手搓)",
    re.IGNORECASE,
)

IGNORED_LINK_HOSTS = {
    "x.com",
    "twitter.com",
    "t.co",
    "pic.twitter.com",
    "pbs.twimg.com",
    "video.twimg.com",
    "www.reddit.com",
    "reddit.com",
    "old.reddit.com",
    "i.redd.it",
    "v.redd.it",
    "preview.redd.it",
}


def classify_project_link(url: str) -> Optional[Dict[str, str]]:
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower().removeprefix("www.")
        if not host or host in IGNORED_LINK_HOSTS:
            return None
        path = parsed.path.rstrip("/")
        if host == "github.com" and path.count("/") >= 2:
            parts = [p for p in path.split("/") if p][:2]
            clean = f"https://github.com/{parts[0]}/{parts[1]}"
            return {"label": f"GitHub · {parts[0]}/{parts[1]}", "url": clean, "kind": "github"}
        if host == "huggingface.co" and path:
            if path.startswith("/spaces/"):
                sp = "/".join([p for p in path.split("/") if p][:3])
                return {"label": f"HF Space 试玩", "url": f"https://huggingface.co/{sp}", "kind": "hf_space"}
            if path.startswith("/papers/"):
                return {"label": "HF Paper 论文", "url": f"https://huggingface.co{path}", "kind": "paper"}
            parts = [p for p in path.split("/") if p][:2]
            clean = f"https://huggingface.co/{'/'.join(parts)}"
            return {"label": f"HuggingFace · {'/'.join(parts)}", "url": clean, "kind": "huggingface"}
        if host in ("arxiv.org", "alphaxiv.org"):
            return {"label": "论文 ArXiv", "url": url, "kind": "paper"}
        if host in ("modelscope.cn", "civitai.com", "colab.research.google.com"):
            return {"label": host.split(".")[0].capitalize(), "url": url, "kind": "platform"}
        return {"label": f"官网/博客 · {host}", "url": url, "kind": "website"}
    except Exception:
        return None


def derive_canonical_key(fallback_id: str, project_links: List[Dict[str, str]]) -> str:
    for kind_priority in ("github", "hf_space", "huggingface", "website", "platform", "paper"):
        for lk in project_links:
            if lk.get("kind") == kind_priority and lk.get("url"):
                u = lk["url"].lower().rstrip("/")
                return f"url:{u}"
    return fallback_id


def is_obvious_spam_or_offtopic(text: str, source: str) -> bool:
    if not text or len(text.strip()) < 12:
        return True
    if SPAM_RE.search(text):
        return True
    # For personal timeline (x_home), filter out pure sports / pure crypto price calls without AI/tech signal
    if source == "x_home":
        if PURE_CRYPTO_TICKER_RE.search(text) and not AI_HINT_RE.search(text):
            return True
        if not AI_HINT_RE.search(text):
            return True
    return False


def needs_reply_link_rescue(text: str, project_links: List[Dict[str, str]]) -> bool:
    if project_links:
        return False
    lower = text.lower()
    cues = (
        "comment", "reply", "below", "thread", "link in", "links in", "link below",
        "on hf", "on github", "github repo", "hf repo", "open weights",
        "👇", "⬇️", "↓", "🧵", "评论", "一楼", "置顶", "リプ", "リンク",
    )
    return any(c in lower for c in cues)


def compute_signal_score(item: Dict[str, Any]) -> float:
    """
    Tier-1 deterministic 'Viral + Dry-Goods Score' (0 - 100):
    Combines X impressions/views (200k+ viral threshold), bookmark-to-view & bookmark-to-like
    density (filtering celebrity/gossip fluff), concrete deliverables (GitHub / HF / Demo Video),
    and fresh velocity.
    """
    source = item.get("source", "")
    m = item.get("metrics", {}) or {}
    links = item.get("project_links", []) or []
    has_video = bool(item.get("video_url"))
    score = 25.0

    # 1. Concrete deliverable bonuses (max +24)
    kinds = {lk.get("kind") for lk in links}
    if "hf_space" in kinds:
        score += 16.0
    elif "github" in kinds:
        score += 15.0
    elif "huggingface" in kinds:
        score += 15.0
    elif "website" in kinds or "platform" in kinds:
        score += 8.0
    elif "paper" in kinds:
        score += 6.0

    if has_video:
        score += 8.0

    if source in ("x_home", "x_search"):
        likes = max(0, int(m.get("likes", 0) or 0))
        bookmarks = max(0, int(m.get("bookmarks", 0) or 0))
        retweets = max(0, int(m.get("retweets", 0) or 0))
        views = max(0, int(m.get("views", 0) or 0))
        followers = max(100, int(item.get("author_followers", 1000) or 1000))

        if likes >= 10:
            m["bookmark_ratio"] = round((bookmarks / max(likes, 1)) * 100, 1)
        if views >= 1000:
            m["bm_per_kviews"] = round((bookmarks / views) * 1000, 2)

        # 2. Views / Impressions viral ladder (200k+ = industry AI/Tech viral threshold, max +20)
        if views >= 500_000:
            views_pts = 20.0
        elif views >= 200_000:
            views_pts = 16.0
        elif views >= 100_000:
            views_pts = 12.0
        elif views >= 50_000:
            views_pts = 8.5
        elif views >= 15_000:
            views_pts = 4.5
        elif views >= 3_000:
            views_pts = 2.0
        else:
            views_pts = 0.0

        # Anti-gossip damper: high impressions (>100k) with <0.5 saves per 1k views -> halve view bonus
        if views >= 100_000 and (bookmarks / max(views, 1)) < 0.0005:
            views_pts *= 0.45
        score += views_pts

        # 3. Bookmark density (Bookmark/View + Bookmark/Like, max +22)
        kv_pts = min(14.0, ((bookmarks / views) * 1000) * 2.8) if views >= 1000 else 0.0
        if likes >= 8:
            bl_pts = min(14.0, (bookmarks / max(likes, 1)) * 20.0)
        else:
            bl_pts = 4.0 if bookmarks >= 3 else 0.0
        save_pts = min(22.0, max(kv_pts, bl_pts) + 0.35 * min(kv_pts, bl_pts))
        score += save_pts

        # 4. Small-account breakout + fresh (<8h) velocity boost (max +9)
        eng = likes + bookmarks * 2.0 + retweets * 1.5
        if eng > 0:
            score += min(6.0, (eng / math.sqrt(followers)) * 0.35)
        created_ts = int(item.get("created_at_ts") or 0)
        if created_ts > 0 and (time.time() - created_ts) < 8 * 3600 and (bookmarks >= 4 or kinds or has_video):
            score += 3.0

    elif source == "huggingface":
        likes = int(m.get("likes", 0) or 0)
        downloads = int(m.get("downloads", 0) or 0)
        score += min(32.0, math.log10(max(1, likes + 1)) * 11.5)
        if downloads > 1000:
            score += min(11.0, math.log10(downloads) * 2.2)

    elif source == "github":
        stars = int(m.get("stars", 0) or 0)
        score += min(36.0, math.log10(max(1, stars + 1)) * 10.5)

    elif source == "reddit":
        score += 20.0
        if kinds:
            score += 8.0

    elif source == "hackernews":
        pts = int(m.get("points", 0) or 0)
        score += min(32.0, math.log10(max(1, pts + 1)) * 12.0)

    return round(min(99.0, max(5.0, score)), 1)
