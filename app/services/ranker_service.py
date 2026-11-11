import math
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

SPAM_PATTERNS = [
    r"comment\s+['\"`]?[a-z0-9_+-]{1,15}['\"`]?\s+(and\s+)?(i'?ll|to\s+get|for\s+the)\s+(dm|send)",
    r"reply\s+['\"`]?[a-z0-9_+-]{1,15}['\"`]?\s+and\s+i'?ll\s+send",
    r"retweet\s+and\s+comment",
    r"\bgiveaway\b",
    r"10\s+ai\s+tools\s+that\s+feel\s+illegal",
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
        "comment", "reply", "below", "thread", "link in", "links in",
        "on hf", "on github", "github repo", "hf repo", "open weights",
        "👇", "🧵", "评论", "一楼", "置顶",
    )
    return any(c in lower for c in cues)


def compute_signal_score(item: Dict[str, Any]) -> float:
    """
    Tier-1 deterministic 'Dry-Goods Score' (0 - 100):
    Heavily rewards X bookmark-to-like ratio, small-account viral breakouts,
    concrete deliverables (GitHub / HF Space / HuggingFace / Demo Video), and fresh velocity.
    """
    source = item.get("source", "")
    m = item.get("metrics", {}) or {}
    links = item.get("project_links", []) or []
    has_video = bool(item.get("video_url"))
    score = 30.0

    # Deliverable bonuses
    kinds = {lk.get("kind") for lk in links}
    if "hf_space" in kinds:
        score += 18.0
    elif "github" in kinds:
        score += 16.0
    elif "huggingface" in kinds:
        score += 15.0
    elif "website" in kinds or "platform" in kinds:
        score += 10.0
    elif "paper" in kinds:
        score += 8.0

    if has_video:
        score += 9.0

    if source in ("x_home", "x_search"):
        likes = max(0, int(m.get("likes", 0) or 0))
        bookmarks = max(0, int(m.get("bookmarks", 0) or 0))
        retweets = max(0, int(m.get("retweets", 0) or 0))
        followers = max(100, int(item.get("author_followers", 1000) or 1000))

        # Bookmark-to-Like ratio: dry-goods posts routinely hit 0.25 - 1.2+ bookmark/like ratio!
        if likes >= 10:
            bm_ratio = bookmarks / max(likes, 1)
            m["bookmark_ratio"] = round(bm_ratio * 100, 1)
            score += min(24.0, bm_ratio * 28.0)

        # Engagement magnitude + small-creator breakout multiplier
        eng = likes + bookmarks * 1.8 + retweets * 1.5
        if eng > 0:
            mag = min(18.0, math.log10(max(1.0, eng)) * 5.2)
            breakout = min(10.0, (eng / math.sqrt(followers)) * 0.45)
            score += mag + breakout

    elif source == "huggingface":
        likes = int(m.get("likes", 0) or 0)
        downloads = int(m.get("downloads", 0) or 0)
        score += min(28.0, math.log10(max(1, likes + 1)) * 10.5)
        if downloads > 1000:
            score += min(10.0, math.log10(downloads) * 2.0)

    elif source == "github":
        stars = int(m.get("stars", 0) or 0)
        score += min(32.0, math.log10(max(1, stars + 1)) * 9.5)

    elif source == "reddit":
        score += 16.0
        if kinds:
            score += 8.0

    elif source == "hackernews":
        pts = int(m.get("points", 0) or 0)
        score += min(28.0, math.log10(max(1, pts + 1)) * 11.0)

    return round(min(99.0, max(5.0, score)), 1)
