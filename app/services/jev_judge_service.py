import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Tuple
import httpx
from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, Score

from app.core.config import get_openrouter_api_key, get_system_proxy, get_typesafe_api_key, settings

logger = logging.getLogger(__name__)


class JevJudgeService:
    def is_jev_configured(self) -> bool:
        return bool(get_typesafe_api_key() or get_openrouter_api_key())

    async def _evaluate_single_with_official_jev(
        self, client: AsyncTypeSafeClient, item: Dict[str, Any]
    ) -> Tuple[str, str, float, float]:
        state = {
            "source": item.get("source_badge", ""),
            "author": item.get("author_handle") or item.get("author", ""),
            "title": item.get("raw_title", ""),
            "content": (item.get("raw_text") or "")[:900],
            "links": [lk.get("url") for lk in (item.get("project_links") or [])[:4]],
            "has_demo_video": bool(item.get("video_url")),
            "metrics": item.get("metrics", {}),
        }

        questions = {
            "category": Choice(
                instructions=(
                    "Classify this item for an AI builder/enthusiast radar tracking cool new models, "
                    "open-source repos, creative generation (video/image/audio/3D), local GPU hacks, "
                    "and clever apps built around AI."
                ),
                criteria={
                    "MODEL_WEIGHTS": "New AI model release, open weights, fine-tune, benchmark breakthrough, or LLM/VLM drop.",
                    "IMAGE_VIDEO_AUDIO": "Image/video/music/TTS/voice-clone/avatar/3D generation model, LoRA, or ComfyUI workflow/node.",
                    "LOCAL_HACK": "Low-VRAM optimization, GGUF quantization, uncensored local run, free GPU/Colab/ModelScope deployment trick, or speed boost.",
                    "WILD_PROJECT": "Creative standalone project, weekend hack, dashboard, or vertical app built USING AI/LLMs/APIs.",
                    "AGENT_TOOL": "Developer tool, AI browser, computer-use agent, coding assistant, CLI, SDK, or MCP tool.",
                    "NOISE": "Generic opinion, engagement bait, politics, pure crypto price talk, vague hype without any concrete tool/model/technique.",
                },
            ),
            "playability": Choice(
                instructions="How immediately usable or testable is the thing described?",
                criteria={
                    "READY_NOW": "Open-source code, open weights, HuggingFace Space, free download, live web app, or reproducible tutorial available right now.",
                    "DEMO_PAPER": "Research paper, technical blog, or real product demo video shown, but code/access is partial or paid.",
                    "WAITLIST_HYPE": "Teaser/waitlist only or no tangible artifact yet.",
                },
            ),
            "utility_score": Score(
                instructions="Rate how genuinely novel, fun, practical, or technically impressive this is for an AI builder.",
                criteria=[
                    "Trivial noise or repetitive fluff",
                    "Minor incremental update",
                    "Solid useful tool, workflow, or repo",
                    "High-impact release, clever hack, or must-bookmark resource",
                    "Breakthrough model/speedup or extraordinarily cool playable AI project",
                ],
            ),
            "is_hype_bait": Noul(
                instructions="Is this post mostly exaggerated clickbait or marketing fluff lacking real substance?"
            ),
        }

        resp = await client.system_one(state=state, questions=questions)
        cat_ans = resp.answers.get("category")
        play_ans = resp.answers.get("playability")
        score_ans = resp.answers.get("utility_score")
        hype_ans = resp.answers.get("is_hype_bait")

        category = getattr(cat_ans, "choice", "WILD_PROJECT") or "WILD_PROJECT"
        playability = getattr(play_ans, "choice", "DEMO_PAPER") or "DEMO_PAPER"
        raw_score = float(getattr(score_ans, "score", 2.5) or 2.5)  # 0.0 to 4.0
        jev_score = min(99.0, max(15.0, round((raw_score / 4.0) * 100.0, 1)))
        hype_prob = round(float(getattr(hype_ans, "noul", 0.18) or 0.18) * 100.0, 1)
        return category, playability, jev_score, hype_prob

    @staticmethod
    def _fallback_heuristic_judge(item: Dict[str, Any]) -> Tuple[str, str, float, float]:
        txt = f"{item.get('raw_title', '')} {item.get('raw_text', '')}".lower()
        links = item.get("project_links") or []
        kinds = {lk.get("kind") for lk in links}

        if any(w in txt for w in ("comfyui", "lora", "video", "diffusion", "tts", "voice", "music", "avatar", "lip-sync", "3d", "flux", "minimax", "moss")):
            cat = "IMAGE_VIDEO_AUDIO"
        elif any(w in txt for w in ("gguf", "vram", "12gb", "24gb", "quant", "uncensored", "abliterated", "modelscope", "colab", "显存", "t/s")):
            cat = "LOCAL_HACK"
        elif any(w in txt for w in ("open weights", "open-weights", "qwen", "deepseek", "gemma", "llama", "checkpoint", "huggingface")):
            cat = "MODEL_WEIGHTS"
        elif any(w in txt for w in ("browser", "computer use", "claude code", "cursor", "mcp", "cli", "agent", "autopilot")):
            cat = "AGENT_TOOL"
        else:
            cat = "WILD_PROJECT"

        play = "READY_NOW" if kinds.intersection({"github", "huggingface", "hf_space", "website", "platform"}) else "DEMO_PAPER"
        score = min(95.0, max(45.0, float(item.get("signal_score", 60.0))))
        return cat, play, score, 15.0

    async def evaluate_batch(self, items: List[Dict[str, Any]]) -> Dict[str, Tuple[str, str, float, float]]:
        if not items:
            return {}
        results: Dict[str, Tuple[str, str, float, float]] = {}
        api_key = get_typesafe_api_key()

        if api_key:
            sem = asyncio.Semaphore(16)
            try:
                async with AsyncTypeSafeClient(api_key=api_key) as client:
                    async def _worker(it: Dict[str, Any]) -> None:
                        async with sem:
                            try:
                                results[it["id"]] = await asyncio.wait_for(
                                    self._evaluate_single_with_official_jev(client, it),
                                    timeout=11.0,
                                )
                            except Exception as e:
                                logger.warning(f"Official Jev item eval fallback ({it['id']}): {e}")
                                results[it["id"]] = self._fallback_heuristic_judge(it)

                    await asyncio.gather(*[_worker(it) for it in items])
                return results
            except Exception as e:
                logger.error(f"Official TypeSafe client batch error: {e}")

        for it in items:
            results[it["id"]] = self._fallback_heuristic_judge(it)
        return results

    @staticmethod
    def _contains_mostly_chinese(text: str) -> bool:
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        return cjk >= 10

    async def translate_and_distill_batch(
        self, items: List[Dict[str, Any]], model_override: str = ""
    ) -> Dict[str, Tuple[str, List[str]]]:
        """
        Distills surviving items (whether English, Arabic, Japanese, or Chinese) into:
        - zh_title: crisp 1-line Chinese title highlighting what it is + key numbers/edge
        - zh_highlights: 2-3 punchy bullet points (how it works, hardware/playability, why care)
        """
        if not items:
            return {}
        out: Dict[str, Tuple[str, List[str]]] = {}
        or_key = get_openrouter_api_key()
        proxy = get_system_proxy()

        if or_key:
            # Process in chunks of 8 items for fast, reliable JSON generation
            for start in range(0, len(items), 8):
                chunk = items[start : start + 8]
                payload_items = [
                    {
                        "id": it["id"],
                        "source": it.get("source_badge", ""),
                        "title": it.get("raw_title", ""),
                        "text": (it.get("raw_text") or "")[:650],
                        "links": [lk.get("url") for lk in (it.get("project_links") or [])[:3]],
                    }
                    for it in chunk
                ]
                prompt = (
                    "你是一个硬核 AI 极客情报编辑。请把下面这组来自 X / HuggingFace / GitHub / Reddit / HN 的最新 AI 项目或技术帖，"
                    "逐条提炼成接地气的简体中文（哪怕原文是英文、阿拉伯语、日语也要准确翻成中文技术表达）。\n"
                    "要求：\n"
                    "1. `zh_title`：一句话直接说清【名字 + 它是干嘛的 + 最硬核的数字/卖点】（38字以内，拒绝空洞公关词）。\n"
                    "2. `zh_highlights`：数组，给 2 到 3 条精炼看点（每条 35 字以内），抠出：核心实现原理 / 显存或硬件门槛 / 是否已放开源代码或在线试玩。\n"
                    "严格只输出 JSON 数组，格式：[{\"id\": \"...\", \"zh_title\": \"...\", \"zh_highlights\": [\"...\", \"...\"]}]\n\n"
                    f"待处理条目：\n{json.dumps(payload_items, ensure_ascii=False)}"
                )
                try:
                    async with httpx.AsyncClient(proxy=proxy, timeout=28.0) as client:
                        resp = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {or_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": (model_override or settings.OPENROUTER_MODEL or "deepseek/deepseek-v4-flash").strip(),
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.2,
                            },
                        )
                        if resp.status_code == 200:
                            content = (
                                resp.json()
                                .get("choices", [{}])[0]
                                .get("message", {})
                                .get("content", "")
                            )
                            m_json = re.search(r"\[.*\]", content, re.DOTALL)
                            if m_json:
                                parsed = json.loads(m_json.group(0))
                                for entry in parsed:
                                    iid = entry.get("id")
                                    zt = (entry.get("zh_title") or "").strip()
                                    zh_list = [str(x).strip() for x in (entry.get("zh_highlights") or []) if str(x).strip()][:3]
                                    if iid and zt:
                                        out[iid] = (zt, zh_list)
                except Exception as e:
                    logger.warning(f"OpenRouter Chinese digest warning: {e}")

        # Only return items actually translated (or already Chinese) so failed API calls retry next scan instead of locking English!
        for it in items:
            if it["id"] not in out and self._contains_mostly_chinese(it.get("raw_text", "")):
                raw_t = (it.get("raw_title") or "").strip()
                raw_lines = [ln.strip() for ln in (it.get("raw_text") or "").splitlines() if ln.strip()]
                bullets = raw_lines[1:4] if len(raw_lines) > 1 else raw_lines[:2]
                out[it["id"]] = (raw_t[:90], [b[:90] for b in bullets])

        return out


jev_judge = JevJudgeService()
