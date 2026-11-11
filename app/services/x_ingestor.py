import email.utils
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import httpx

from app.core.config import get_system_proxy, settings
from app.services.ranker_service import (
    classify_project_link,
    compute_signal_score,
    derive_canonical_key,
    is_obvious_spam_or_offtopic,
    needs_reply_link_rescue,
)

logger = logging.getLogger(__name__)

BEARER = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# Fallback query IDs verified live; dynamically refreshed from x.com/home JS bundles
DEFAULT_OPS: Dict[str, Tuple[str, List[str]]] = {
    "HomeTimeline": ("KmJCeZ__ef1fNos7tKN_fg", []),
    "HomeLatestTimeline": ("IVA5BUbeYPTrpYekQH7jiA", []),
    "SearchTimeline": ("vLHjqbDv7TPFMBkIIO1nOA", []),
    "TweetDetail": ("dQDdKtt882nl-Km98FJGSQ", []),
}

DEFAULT_FEATURES = {
    "rweb_video_screen_enabled": True,
    "profile_label_improvements_pcf_label_in_post_enabled": True,
    "rweb_tipjar_consumption_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "premium_content_api_read_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "responsive_web_grok_analyze_button_fetch_trends_enabled": False,
    "responsive_web_grok_analyze_post_followups_enabled": True,
    "responsive_web_jetfuel_frame": False,
    "responsive_web_grok_share_attachment_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "responsive_web_grok_show_grok_translated_post": False,
    "responsive_web_grok_analysis_button_from_backend": True,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_grok_image_annotation_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
    "rweb_video_timestamps_enabled": True,
}


class XIngestor:
    def __init__(self) -> None:
        self._ops_cache: Dict[str, Tuple[str, Dict[str, bool]]] = {}
        self._ops_cached_at: float = 0.0

    def is_configured(self) -> bool:
        return bool((settings.TWITTER_AUTH_TOKEN or "").strip() and (settings.TWITTER_CT0 or "").strip())

    def _cookies(self) -> Dict[str, str]:
        return {
            "auth_token": (settings.TWITTER_AUTH_TOKEN or "").strip(),
            "ct0": (settings.TWITTER_CT0 or "").strip(),
        }

    def _api_headers(self) -> Dict[str, str]:
        return {
            "authorization": f"Bearer {BEARER}",
            "x-csrf-token": (settings.TWITTER_CT0 or "").strip(),
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-active-user": "yes",
            "content-type": "application/json",
            "referer": "https://x.com/home",
            "user-agent": UA,
        }

    async def _ensure_graphql_ops(self, client: httpx.AsyncClient) -> None:
        if self._ops_cache and (time.time() - self._ops_cached_at) < 1800:
            return
        try:
            rh = await client.get(
                "https://x.com/home",
                cookies=self._cookies(),
                headers={"user-agent": UA, "accept": "text/html"},
            )
            if rh.status_code != 200:
                return
            html = rh.text
            bundle_urls: List[str] = []
            main_js = re.findall(r"https://abs\.twimg\.com/responsive-web/client-web/main\.[a-zA-Z0-9._-]+\.js", html)
            if main_js:
                bundle_urls.append(main_js[0])

            m_home_chunk = re.search(r'(\d+):"(shared~bundle\.[^"]*HomeTimeline[^"]*)"', html)
            if m_home_chunk:
                cid, cname = m_home_chunk.group(1), m_home_chunk.group(2)
                m_hashes = re.findall(rf'{cid}:"([a-f0-9]+)"', html)
                if m_hashes:
                    bundle_urls.append(
                        f"https://abs.twimg.com/responsive-web/client-web/{cname}.{m_hashes[-1]}a.js"
                    )

            for b_url in bundle_urls:
                rb = await client.get(b_url, headers={"user-agent": UA})
                if rb.status_code != 200:
                    continue
                for op in ("HomeTimeline", "HomeLatestTimeline", "SearchTimeline", "TweetDetail"):
                    mo = re.search(
                        rf'queryId:"([^"]+)",operationName:"{op}",operationType:"[^"]+",metadata:\{{featureSwitches:\[([^\]]*)\]',
                        rb.text,
                    )
                    if mo:
                        qid = mo.group(1)
                        switches = re.findall(r'"([^"]+)"', mo.group(2))
                        feats = dict(DEFAULT_FEATURES)
                        for s in switches:
                            feats[s] = True
                        self._ops_cache[op] = (qid, feats)
            if self._ops_cache:
                self._ops_cached_at = time.time()
        except Exception as e:
            logger.warning(f"GraphQL bundle discovery warning: {e}")

    def _get_op(self, op: str) -> Tuple[str, Dict[str, bool]]:
        if op in self._ops_cache:
            return self._ops_cache[op]
        qid, _ = DEFAULT_OPS[op]
        return qid, dict(DEFAULT_FEATURES)

    @staticmethod
    def _parse_created_ts(created_at: str) -> int:
        if not created_at:
            return int(time.time())
        try:
            dt = email.utils.parsedate_to_datetime(created_at)
            return int(dt.timestamp())
        except Exception:
            return int(time.time())

    @classmethod
    def _extract_media_and_urls(cls, tweet_obj: Dict[str, Any]) -> Tuple[List[Dict[str, str]], str, str]:
        legacy = tweet_obj.get("legacy", {}) or {}
        links: List[Dict[str, str]] = []
        seen_urls: Set[str] = set()

        def _add_url(u: Optional[str]) -> None:
            if not u:
                return
            info = classify_project_link(u)
            if info and info["url"] not in seen_urls:
                seen_urls.add(info["url"])
                links.append(info)

        # Standard entities + note_tweet entities
        for u_ent in (legacy.get("entities", {}) or {}).get("urls", []) or []:
            _add_url(u_ent.get("expanded_url") or u_ent.get("url"))

        note_res = (
            tweet_obj.get("note_tweet", {})
            .get("note_tweet_results", {})
            .get("result", {})
        ) or {}
        for u_ent in (note_res.get("entity_set", {}) or {}).get("urls", []) or []:
            _add_url(u_ent.get("expanded_url") or u_ent.get("url"))

        # Card URL (e.g. HuggingFace or blog preview cards!)
        card_legacy = (tweet_obj.get("card", {}) or {}).get("legacy", {}) or {}
        for bv in card_legacy.get("binding_values", []) or []:
            val = (bv.get("value", {}) or {}).get("string_value", "")
            if val and val.startswith(("http://", "https://")):
                _add_url(val)

        # Media (video .mp4 + thumbnail image)
        video_url = ""
        image_url = ""
        media_list = (legacy.get("extended_entities", {}) or {}).get("media", []) or (
            legacy.get("entities", {}) or {}
        ).get("media", []) or []
        for m in media_list:
            if not image_url and m.get("media_url_https"):
                image_url = m["media_url_https"]
            mtype = m.get("type", "")
            if mtype in ("video", "animated_gif"):
                variants = (m.get("video_info", {}) or {}).get("variants", []) or []
                mp4s = [v for v in variants if v.get("content_type") == "video/mp4" and v.get("url")]
                if mp4s:
                    mp4s.sort(key=lambda v: int(v.get("bitrate", 0) or 0), reverse=True)
                    video_url = mp4s[0]["url"]

        # Card thumbnail fallback (e.g. HuggingFace / GitHub card preview image)
        if not image_url:
            for bv in card_legacy.get("binding_values", []) or []:
                img_v = (bv.get("value", {}) or {}).get("image_value", {}) or {}
                if img_v.get("url"):
                    image_url = img_v["url"]
                    break

        return links, video_url, image_url

    @classmethod
    def _parse_tweet_result(cls, raw_res: Dict[str, Any], source: str, badge: str) -> Optional[Dict[str, Any]]:
        if not raw_res:
            return None
        if "tweet" in raw_res:
            raw_res = raw_res["tweet"]
        legacy = raw_res.get("legacy", {})
        if not legacy:
            return None

        # Skip retweets without commentary
        if legacy.get("retweeted_status_result"):
            return None

        tid = str(legacy.get("id_str") or raw_res.get("rest_id") or "")
        if not tid:
            return None

        core_user = (raw_res.get("core", {}) or {}).get("user_results", {}).get("result", {}) or {}
        u_leg = core_user.get("legacy", {}) or {}
        u_core = core_user.get("core", {}) or {}
        handle = u_core.get("screen_name") or u_leg.get("screen_name") or "user"
        author_name = u_core.get("name") or u_leg.get("name") or handle
        followers = int(
            (core_user.get("relationship_counts", {}) or {}).get("followers")
            or u_leg.get("followers_count", 0)
            or 0
        )

        note_text = (
            raw_res.get("note_tweet", {})
            .get("note_tweet_results", {})
            .get("result", {})
            .get("text")
        )
        full_text = (note_text or legacy.get("full_text") or "").strip()
        # Strip trailing t.co links from display text
        clean_text = re.sub(r"https?://t\.co/[A-Za-z0-9]+", "", full_text).strip()

        links, video_url, image_url = cls._extract_media_and_urls(raw_res)

        # Penetrate Quote Tweet! If author quoted a launch tweet, merge its text, links, and demo video!
        quoted = (raw_res.get("quoted_status_result", {}) or {}).get("result", {})
        if "tweet" in quoted:
            quoted = quoted["tweet"]
        if quoted and quoted.get("legacy"):
            q_note = (
                quoted.get("note_tweet", {})
                .get("note_tweet_results", {})
                .get("result", {})
                .get("text")
            )
            q_text = re.sub(r"https?://t\.co/[A-Za-z0-9]+", "", (q_note or quoted["legacy"].get("full_text") or "")).strip()
            if q_text:
                clean_text = f"{clean_text}\n\n[引用原帖]: {q_text}".strip()
            q_links, q_vid, q_img = cls._extract_media_and_urls(quoted)
            seen = {lk["url"] for lk in links}
            for lk in q_links:
                if lk["url"] not in seen:
                    links.append(lk)
                    seen.add(lk["url"])
            video_url = video_url or q_vid
            image_url = image_url or q_img

        if is_obvious_spam_or_offtopic(clean_text, source):
            return None

        likes = int(legacy.get("favorite_count", 0) or 0)
        bookmarks = int(legacy.get("bookmark_count", 0) or 0)
        retweets = int(legacy.get("retweet_count", 0) or 0)
        views_str = (raw_res.get("views", {}) or {}).get("count")
        views = int(views_str) if views_str and str(views_str).isdigit() else 0

        first_line = clean_text.split("\n")[0].strip()[:110]
        item: Dict[str, Any] = {
            "id": f"x:{tid}",
            "tweet_id": tid,
            "source": source,
            "source_badge": badge,
            "author": author_name,
            "author_handle": f"@{handle}",
            "author_followers": followers,
            "raw_title": first_line,
            "raw_text": clean_text[:2000],
            "original_url": f"https://x.com/{handle}/status/{tid}",
            "project_links": links,
            "video_url": video_url,
            "image_url": image_url,
            "metrics": {
                "likes": likes,
                "bookmarks": bookmarks,
                "retweets": retweets,
                "views": views,
            },
            "created_at_ts": cls._parse_created_ts(legacy.get("created_at", "")),
        }
        item["canonical_key"] = derive_canonical_key(item["id"], links)
        item["signal_score"] = compute_signal_score(item)
        return item

    @classmethod
    def _extract_entries_from_instructions(
        cls, instructions: List[Dict[str, Any]], source: str, badge: str
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        parsed_items: List[Dict[str, Any]] = []
        next_cursor: Optional[str] = None
        for inst in instructions:
            entries = inst.get("entries") or []
            for entry in entries:
                eid = str(entry.get("entryId", ""))
                content = entry.get("content", {}) or {}
                if eid.startswith("cursor-bottom"):
                    next_cursor = content.get("value")
                    continue
                if "promoted" in eid.lower():
                    continue
                item_content = content.get("itemContent", {}) or {}
                if item_content.get("promotedMetadata"):
                    continue
                tr = (item_content.get("tweet_results", {}) or {}).get("result", {})
                if tr:
                    item = cls._parse_tweet_result(tr, source, badge)
                    if item:
                        parsed_items.append(item)
        return parsed_items, next_cursor

    async def fetch_personal_feeds(self, pages_for_you: int = 3, pages_following: int = 2) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        proxy = get_system_proxy()
        collected: Dict[str, Dict[str, Any]] = {}
        async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=22.0) as client:
            await self._ensure_graphql_ops(client)

            for op_name, pages, badge in [
                ("HomeTimeline", pages_for_you, "X 为你推荐"),
                ("HomeLatestTimeline", pages_following, "X 正在关注"),
            ]:
                qid, feats = self._get_op(op_name)
                cursor: Optional[str] = None
                for _ in range(pages):
                    variables: Dict[str, Any] = {
                        "count": 35,
                        "includePromotedContent": False,
                        "latestControlAvailable": True,
                        "requestContext": "launch",
                    }
                    if cursor:
                        variables["cursor"] = cursor
                    try:
                        resp = await client.post(
                            f"https://x.com/i/api/graphql/{qid}/{op_name}",
                            json={"variables": variables, "features": feats, "queryId": qid},
                            cookies=self._cookies(),
                            headers=self._api_headers(),
                        )
                        if resp.status_code != 200:
                            logger.warning(f"{op_name} HTTP {resp.status_code}")
                            break
                        instructions = (
                            resp.json()
                            .get("data", {})
                            .get("home", {})
                            .get("home_timeline_urt", {})
                            .get("instructions", [])
                        )
                        batch, cursor = self._extract_entries_from_instructions(instructions, "x_home", badge)
                        for b in batch:
                            # Keep low-noise high-signal posts from timeline
                            m = b["metrics"]
                            if m["likes"] >= 8 or m["bookmarks"] >= 3 or b["project_links"] or b["video_url"]:
                                collected[b["id"]] = b
                        if not cursor:
                            break
                    except Exception as e:
                        logger.warning(f"Error fetching {op_name}: {e}")
                        break

        return list(collected.values())

    async def fetch_broad_launches_and_reverse_terms(
        self, hot_terms: List[str], known_x_ids: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Zero-guess broad X launch catchers + reverse lookup for today's hot HF/GitHub project names.
        """
        if not self.is_configured():
            return []
        proxy = get_system_proxy()
        queries: List[Tuple[str, str]] = [
            (
                '(github OR huggingface OR "open weights" OR "open source") min_faves:100 -is:retweet -filter:replies',
                "X 开源高热",
            ),
        ]
        # Take top 3 clean distinctive project names from today's HF/GitHub trending for X video/demo cross-match
        clean_terms: List[str] = []
        for t in hot_terms:
            slug = t.split("/")[-1].strip()
            if 4 <= len(slug) <= 28 and re.match(r"^[A-Za-z0-9._-]+$", slug):
                clean_terms.append(f'"{slug}"')
            if len(clean_terms) >= 4:
                break
        if clean_terms:
            queries.append(
                (f"({' OR '.join(clean_terms)}) min_faves:15 -is:retweet -filter:replies", "X 热榜联动")
            )

        collected: Dict[str, Dict[str, Any]] = {}
        async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=20.0) as client:
            await self._ensure_graphql_ops(client)
            qid, feats = self._get_op("SearchTimeline")

            for raw_q, badge in queries:
                variables = {
                    "rawQuery": raw_q,
                    "count": 25,
                    "querySource": "typed_query",
                    "product": "Top",
                }
                try:
                    resp = await client.post(
                        f"https://x.com/i/api/graphql/{qid}/SearchTimeline",
                        json={"variables": variables, "features": feats},
                        cookies=self._cookies(),
                        headers=self._api_headers(),
                    )
                    if resp.status_code != 200:
                        resp = await client.get(
                            f"https://x.com/i/api/graphql/{qid}/SearchTimeline",
                            params={"variables": json.dumps(variables), "features": json.dumps(feats)},
                            cookies=self._cookies(),
                            headers=self._api_headers(),
                        )
                    if resp.status_code != 200:
                        continue
                    instructions = (
                        resp.json()
                        .get("data", {})
                        .get("search_by_raw_query", {})
                        .get("search_timeline", {})
                        .get("timeline", {})
                        .get("instructions", [])
                    )
                    batch, _ = self._extract_entries_from_instructions(instructions, "x_search", badge)
                    for b in batch:
                        if b["id"] not in known_x_ids:
                            collected[b["id"]] = b
                except Exception as e:
                    logger.warning(f"X search warning ({badge}): {e}")

        return list(collected.values())

    async def rescue_author_reply_links(self, candidates: List[Dict[str, Any]], max_checks: int = 8) -> Dict[str, List[Dict[str, str]]]:
        """
        Penetrates 'Links in first comment 👇' on X:
        Fetches TweetDetail for top candidates missing direct links and extracts URLs posted by the author in replies!
        """
        if not self.is_configured():
            return {}
        targets = [
            c for c in candidates
            if c.get("source", "").startswith("x_") and needs_reply_link_rescue(c.get("raw_text", ""), c.get("project_links", []))
        ][:max_checks]
        if not targets:
            return {}

        proxy = get_system_proxy()
        rescued: Dict[str, List[Dict[str, str]]] = {}
        async with httpx.AsyncClient(proxy=proxy, follow_redirects=True, timeout=18.0) as client:
            await self._ensure_graphql_ops(client)
            qid, feats = self._get_op("TweetDetail")

            for item in targets:
                tid = item.get("tweet_id") or item["id"].removeprefix("x:")
                author_handle = (item.get("author_handle") or "").lstrip("@").lower()
                variables = {
                    "focalTweetId": tid,
                    "with_rux_injections": False,
                    "rankingMode": "Relevance",
                    "includePromotedContent": False,
                    "withCommunity": True,
                    "withQuickPromoteEligibilityTweetFields": True,
                    "withBirdwatchNotes": True,
                    "withVoice": True,
                }
                try:
                    resp = await client.get(
                        f"https://x.com/i/api/graphql/{qid}/TweetDetail",
                        params={"variables": json.dumps(variables), "features": json.dumps(feats)},
                        cookies=self._cookies(),
                        headers=self._api_headers(),
                    )
                    if resp.status_code != 200:
                        continue
                    instructions = (
                        resp.json()
                        .get("data", {})
                        .get("threaded_conversation_with_injections_v2", {})
                        .get("instructions", [])
                    )
                    found_links: List[Dict[str, str]] = []
                    seen_u: Set[str] = set()
                    for inst in instructions:
                        for entry in inst.get("entries") or []:
                            # Thread conversation items live inside content.items[].item.itemContent
                            sub_items = (entry.get("content", {}) or {}).get("items") or []
                            for sub in sub_items:
                                tr = (
                                    (sub.get("item", {}) or {})
                                    .get("itemContent", {})
                                    .get("tweet_results", {})
                                    .get("result", {})
                                )
                                if "tweet" in tr:
                                    tr = tr["tweet"]
                                if not tr:
                                    continue
                                u_res = (tr.get("core", {}) or {}).get("user_results", {}).get("result", {}) or {}
                                r_handle = (
                                    (u_res.get("core", {}) or {}).get("screen_name")
                                    or (u_res.get("legacy", {}) or {}).get("screen_name")
                                    or ""
                                ).lower()
                                # Prioritize author's own thread replies (or top reply if it holds GitHub/HF)
                                lks, _, _ = self._extract_media_and_urls(tr)
                                for lk in lks:
                                    if r_handle == author_handle or lk.get("kind") in ("github", "huggingface", "hf_space"):
                                        if lk["url"] not in seen_u:
                                            seen_u.add(lk["url"])
                                            lk["label"] = f"💬评论区抠出 · {lk['label']}"
                                            found_links.append(lk)
                    if found_links:
                        rescued[item["id"]] = found_links
                except Exception as e:
                    logger.debug(f"TweetDetail rescue skipped for {tid}: {e}")

        return rescued


x_ingestor = XIngestor()
