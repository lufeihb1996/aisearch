const I18N = {
  zh: {
    brandTitle: "AI 新物种猎手雷达",
    brandSub: "5 源无词捕获 · 书签收藏比提纯 · 评论区一楼穿透 · TypeSafe Jev 终审",
    stJev: "Jev 裁判",
    stX: "X Cookie",
    stZh: "DeepSeek 翻译",
    btnSettings: "⚙️ 密钥 / Cookie 配置",
    sourcesLabel: "数据源 (勾谁看谁 & 扫谁)：",
    btnSelectAll: "全选",
    srcX: "𝕏 推荐/关注 & 热榜联动",
    srcHf: "🤗 HuggingFace 飙升榜",
    srcGh: "📦 GitHub 暴涨新库",
    srcRd: "👽 Reddit 实测热帖",
    srcHn: "🟧 HN 极客手搓",
    btnStarred: "⭐ 收藏夹",
    optJudge18: "Jev 精判 Top 18 条",
    optJudge26: "Jev 精判 Top 26 条",
    optJudge40: "Jev 精判 Top 40 条",
    btnScan: "⚡ 立即扫描已勾选源",
    btnScanBusy: "⏳ 正在多源抓取 + Jev 裁判打分中...",
    scanHint: "勾选上方数据源实时过滤列表；扫描仅抓新帖与 Jev 打分，中文翻译按需手动点击触发",
    catAll: "全部赛道",
    catMedia: "🎬 视频·生图·语音·3D",
    catModel: "🧠 开源模型 & 权重",
    catLocal: "⚡ 低显存部署 / 白嫖算力",
    catWild: "🛠️ AI 实战野生项目",
    catAgent: "🤖 Agent / 自动化工具",
    searchPlaceholder: "搜项目名、模型、ComfyUI、GGUF、TTS、Agent...",
    chkReady: "🟢 只看立即可玩/已开源",
    chkVideo: "🎬 只看带演示视频",
    time24h: "时间：24小时内",
    time3d: "时间：近 3 天",
    time7d: "时间：近 7 天",
    timeAll: "时间：全部历史",
    sortScore: "排序：Jev 分数 (高 → 低)",
    sortCombo: "排序：综合爆款度 (Jev + 多源热度)",
    sortBookmarks: "排序：干货收藏比 / Star 热度",
    sortLatest: "排序：发布时间最新",
    loadingFeed: "正在连接情报库...",
    modalTitle: "配置密钥与 X 登录 Cookie",
    modalTip: "留空的项不会覆盖你现有的已保存配置（云端模式下自动加密存入 Supabase）。",
    lblAdminPwd: "管理员操作口令 (对应 Vercel 环境变量 RADAR_ADMIN_PASSWORD，留空不改)",
    lblJevKey: "官方 TypeSafe Jev API Key (console.typesafe.ai)",
    lblXAuth: "X (Twitter) Cookie: auth_token (40位)",
    lblXCt0: "X (Twitter) Cookie: ct0 (160位)",
    lblOrKey: "OpenRouter API Key (默认调用 DeepSeek V4 Flash 手动翻译中文)",
    btnSave: "保存并生效",
    btnCancel: "取消",
    noSourceEmpty: "未勾选任何数据源 — 请在上方勾选至少 1 个源头（如 📦 GitHub 暴涨新库）即可立即显示对应项目。",
    noItemsEmpty: "当前筛选下暂无条目 — 点击上方「⚡ 立即扫描已勾选源」一键抓取并由 Jev 判分入库！",
    zeroItems: "0 个精选项目",
    counterFmt: (total, p, tp) => `共 ${total} 条 · 第 ${p}/${tp} 页`,
    pageInfoFmt: (s, e, total, ps) =>
      `正在显示第 <strong>${s}-${e}</strong> 条 · 共 <strong>${total}</strong> 个精选项目（每页 ${ps} 条）`,
    prevPage: "← 上一页",
    nextPage: "下一页 →",
    btnTrPageEmpty: "🌐 翻译本页",
    btnTrPageAllDone: "✓ 本页已全译",
    btnTrPageCount: (n) => `🌐 翻译本页 (${n}条)`,
    btnTranslating: "⏳ 翻译中...",
    btnCardTr: "🌐 译",
    btnCardTrTitle: "用 DeepSeek 提炼为中文",
    btnCardShowRaw: "原",
    btnCardShowRawTitle: "切换查看原文标题与摘要",
    btnCardShowZh: "译",
    btnCardShowZhTitle: "切换查看已翻译的中文提炼",
    starOn: "★ 已藏",
    starOff: "☆ 收藏",
    videoPill: "▶ 视频演示",
    rawDetails: (who) => `展开原帖全文 (${who})`,
    origSource: "↗ 原帖来源",
    videoDirect: "🎬 视频直链",
    scoreJev: (s) => `Jev ${s}分`,
    scoreSig: (s) => `初筛 ${s}分`,
    bmLabel: (cnt, ratio) => `🔖 收藏 ${cnt}${ratio ? ` (收藏率 ${ratio}%)` : ""}`,
    dlLabel: (cnt) => `⬇ 下载 ${cnt}`,
    catLabels: {
      IMAGE_VIDEO_AUDIO: "🎬 视觉·视频·音频·3D",
      MODEL_WEIGHTS: "🧠 开源模型/权重",
      LOCAL_HACK: "⚡ 低显存/白嫖算力",
      WILD_PROJECT: "🛠️ AI野生实战项目",
      AGENT_TOOL: "🤖 Agent/新工具",
      PENDING: "⏳ 待精判",
    },
    playLabels: {
      READY_NOW: "🟢 立即可玩/已开源",
      DEMO_PAPER: "🟡 演示/论文先行",
      WAITLIST_HYPE: "⚪ 早期预告",
      PENDING: "待评估",
    },
  },
  en: {
    brandTitle: "AI Tech Radar",
    brandSub: "5-Source Zero-Keyword Discovery · Bookmark Ratio Signal · 1st-Reply Link Rescue · TypeSafe Jev Judge",
    stJev: "Jev Judge",
    stX: "X Cookie",
    stZh: "DeepSeek ZH",
    btnSettings: "⚙️ Keys & Cookies",
    sourcesLabel: "Sources (Filter & Scan):",
    btnSelectAll: "Select All",
    srcX: "𝕏 For You / Following & Linked",
    srcHf: "🤗 HuggingFace Trending",
    srcGh: "📦 GitHub Surging Repos",
    srcRd: "👽 Reddit Top AI",
    srcHn: "🟧 Hacker News Show HN",
    btnStarred: "⭐ Starred",
    optJudge18: "Jev Judge Top 18",
    optJudge26: "Jev Judge Top 26",
    optJudge40: "Jev Judge Top 40",
    btnScan: "⚡ Scan Selected Sources",
    btnScanBusy: "⏳ Fetching Sources & Running Jev Judge...",
    scanHint: "Check/uncheck sources above to filter live; Scan fetches & scores items, Chinese digest is triggered manually",
    catAll: "All Tracks",
    catMedia: "🎬 Video · Image · Audio · 3D",
    catModel: "🧠 Open Models & Weights",
    catLocal: "⚡ Low-VRAM & Free GPU",
    catWild: "🛠️ Wild AI Builds",
    catAgent: "🤖 Agents & DevTools",
    searchPlaceholder: "Search repos, models, ComfyUI, GGUF, TTS, Agent...",
    chkReady: "🟢 Ready / Open-Source Only",
    chkVideo: "🎬 With Demo Video",
    time24h: "Time: Last 24h",
    time3d: "Time: Last 3 Days",
    time7d: "Time: Last 7 Days",
    timeAll: "Time: All Time",
    sortScore: "Sort: Jev Score (High → Low)",
    sortCombo: "Sort: Viral Combo (Jev + Multi-Source)",
    sortBookmarks: "Sort: Bookmark Ratio / Stars",
    sortLatest: "Sort: Latest Published",
    loadingFeed: "Connecting to intelligence database...",
    modalTitle: "API Keys & X Session Cookies",
    modalTip: "Empty fields keep your existing saved credentials unchanged (persisted in Supabase in cloud mode).",
    lblAdminPwd: "Admin Password (matches RADAR_ADMIN_PASSWORD on Vercel; blank keeps current)",
    lblJevKey: "Official TypeSafe Jev API Key (console.typesafe.ai)",
    lblXAuth: "X (Twitter) Cookie: auth_token (40 chars)",
    lblXCt0: "X (Twitter) Cookie: ct0 (160 chars)",
    lblOrKey: "OpenRouter API Key (Uses DeepSeek V4 Flash for manual Chinese translation)",
    btnSave: "Save & Apply",
    btnCancel: "Cancel",
    noSourceEmpty: "No sources selected — check at least 1 source above (e.g. 📦 GitHub Surging Repos) to display items.",
    noItemsEmpty: "No items match current filters — click '⚡ Scan Selected Sources' above to fetch & score fresh projects!",
    zeroItems: "0 items",
    counterFmt: (total, p, tp) => `${total} items · Page ${p}/${tp}`,
    pageInfoFmt: (s, e, total, ps) =>
      `Showing <strong>${s}-${e}</strong> of <strong>${total}</strong> items (${ps} / page)`,
    prevPage: "← Prev",
    nextPage: "Next →",
    btnTrPageEmpty: "🌐 Translate Page",
    btnTrPageAllDone: "✓ Page Translated",
    btnTrPageCount: (n) => `🌐 Translate Page (${n})`,
    btnTranslating: "⏳ Translating...",
    btnCardTr: "🌐 ZH",
    btnCardTrTitle: "Translate into Chinese via DeepSeek",
    btnCardShowRaw: "Raw",
    btnCardShowRawTitle: "Switch card to original post text",
    btnCardShowZh: "ZH",
    btnCardShowZhTitle: "Switch card to saved Chinese digest",
    starOn: "★ Starred",
    starOff: "☆ Star",
    videoPill: "▶ Video Demo",
    rawDetails: (who) => `View Full Raw Post (${who})`,
    origSource: "↗ Source Post",
    videoDirect: "🎬 Direct Video",
    scoreJev: (s) => `Jev ${s}`,
    scoreSig: (s) => `Sig ${s}`,
    bmLabel: (cnt, ratio) => `🔖 ${cnt}${ratio ? ` (${ratio}% saved)` : ""}`,
    dlLabel: (cnt) => `⬇ ${cnt}`,
    catLabels: {
      IMAGE_VIDEO_AUDIO: "🎬 Vision · Video · Audio · 3D",
      MODEL_WEIGHTS: "🧠 Open Models / Weights",
      LOCAL_HACK: "⚡ Low-VRAM / Free GPU",
      WILD_PROJECT: "🛠️ Wild AI Project",
      AGENT_TOOL: "🤖 Agent / DevTool",
      PENDING: "⏳ Unjudged",
    },
    playLabels: {
      READY_NOW: "🟢 Ready / Open-Source",
      DEMO_PAPER: "🟡 Demo / Paper",
      WAITLIST_HYPE: "⚪ Early Teaser",
      PENDING: "Pending",
    },
  },
};

const SOURCE_BADGE_EN = {
  "X 为你推荐": "X For You",
  "X 关注时间线": "X Following",
  "X 热榜联动": "X Cross-Trending",
  "X 开源高热": "X Open-Weights",
  "HuggingFace 飙升": "HF Trending",
  "HF Space 试玩榜": "HF Space",
  "GitHub 暴涨新库": "GitHub Surging",
  "HN 极客手搓": "Show HN",
};

const state = {
  uiLang: localStorage.getItem("ai_radar_ui_lang") === "en" ? "en" : "zh",
  starredOnly: false,
  category: "all",
  readyOnly: false,
  videoOnly: false,
  q: "",
  sort: "score",
  hours: 72,
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 1,
  currentItems: [],
  // Per-card language override: stores card IDs explicitly toggled away from default
  cardModeOverrides: {},
};

function t() {
  return I18N[state.uiLang] || I18N.zh;
}

function applyStaticI18n() {
  const dict = t();
  document.documentElement.lang = state.uiLang === "en" ? "en" : "zh-CN";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (dict[key] !== undefined) el.textContent = dict[key];
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (dict[key] !== undefined) el.placeholder = dict[key];
  });
  document.querySelectorAll("#ui-lang-switch .lang-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.uiLang === state.uiLang);
  });
}

function getCheckedSources() {
  return Array.from(document.querySelectorAll(".source-toggle input:checked")).map((el) => el.value);
}

function esc(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function updateCounts(sc) {
  if (!sc) return;
  for (const k of ["x", "huggingface", "github", "reddit", "hackernews", "starred"]) {
    const el = document.getElementById(`cnt-${k}`);
    if (el && sc[k] !== undefined) el.textContent = sc[k];
  }
}

async function apiPost(url, bodyObj) {
  const buildHeaders = () => {
    const h = { "Content-Type": "application/json" };
    const pwd = localStorage.getItem("ai_radar_admin_pwd") || "";
    if (pwd) h["X-Admin-Password"] = pwd;
    return h;
  };
  let res = await fetch(url, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(bodyObj || {}),
  });
  if (res.status === 401) {
    const promptMsg =
      state.uiLang === "en"
        ? "This server is protected by RADAR_ADMIN_PASSWORD. Enter your admin password once:"
        : "已开启公网防刷保护，请输入你在 Vercel 设置的管理员口令 (RADAR_ADMIN_PASSWORD)：";
    const entered = window.prompt(promptMsg, "");
    if (!entered || !entered.trim()) {
      throw new Error(state.uiLang === "en" ? "Admin password required (401)" : "未输入管理员口令，操作已取消");
    }
    localStorage.setItem("ai_radar_admin_pwd", entered.trim());
    res = await fetch(url, {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(bodyObj || {}),
    });
  }
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`HTTP ${res.status}: ${errText.slice(0, 120)}`);
  }
  return res.json();
}

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const d = await res.json();
    const dbLabel = document.getElementById("st-db-label");
    if (dbLabel) {
      dbLabel.textContent = d.storage_backend === "supabase" ? "Supabase" : "SQLite";
    }
    document.getElementById("st-jev").classList.toggle("ok", !!d.has_jev_key);
    document.getElementById("st-x").classList.toggle("ok", !!d.has_x_cookie);
    document.getElementById("st-zh").classList.toggle("ok", !!d.has_openrouter_key);
    updateCounts(d.source_counts);
  } catch (e) {
    console.error(e);
  }
}

function updateTranslatePageButton() {
  const btn = document.getElementById("btn-translate-page");
  if (!btn) return;
  const dict = t();
  if (!state.currentItems.length) {
    btn.disabled = true;
    btn.textContent = dict.btnTrPageEmpty;
    return;
  }
  const untranslated = state.currentItems.filter((x) => !(x.zh_translated && x.zh_title));
  if (untranslated.length === 0) {
    btn.disabled = true;
    btn.textContent = dict.btnTrPageAllDone;
  } else {
    btn.disabled = false;
    btn.textContent = dict.btnTrPageCount(untranslated.length);
  }
}

function renderPagination(total, page, totalPages, pageSize) {
  const bar = document.getElementById("pagination-bar");
  if (!bar) return;
  const dict = t();
  if (!total || total <= 0) {
    bar.classList.add("hidden");
    bar.innerHTML = "";
    return;
  }

  bar.classList.remove("hidden");
  const startIdx = (page - 1) * pageSize + 1;
  const endIdx = Math.min(total, page * pageSize);

  const pages = [];
  if (totalPages <= 7) {
    for (let p = 1; p <= totalPages; p++) pages.push(p);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    const winStart = Math.max(2, page - 1);
    const winEnd = Math.min(totalPages - 1, page + 1);
    for (let p = winStart; p <= winEnd; p++) pages.push(p);
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  const pageBtns = pages
    .map((p) => {
      if (p === "...") return `<span class="page-dots">…</span>`;
      const activeCls = p === page ? " active" : "";
      return `<button class="page-btn${activeCls}" type="button" data-page="${p}">${p}</button>`;
    })
    .join("");

  bar.innerHTML = `
    <div class="page-info">${dict.pageInfoFmt(startIdx, endIdx, total, pageSize)}</div>
    <div class="page-controls">
      <button class="page-btn" type="button" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>${esc(dict.prevPage)}</button>
      ${pageBtns}
      <button class="page-btn" type="button" data-page="${page + 1}" ${page >= totalPages ? "disabled" : ""}>${esc(dict.nextPage)}</button>
    </div>
  `;
}

function renderCardsFromState() {
  const grid = document.getElementById("cards-grid");
  const dict = t();
  document.getElementById("result-counter").textContent =
    state.total > 0 ? dict.counterFmt(state.total, state.page, state.totalPages) : dict.zeroItems;

  if (!state.currentItems.length) {
    const checked = getCheckedSources();
    const msg = !state.starredOnly && checked.length === 0 ? dict.noSourceEmpty : dict.noItemsEmpty;
    grid.innerHTML = `<div class="empty-state">${esc(msg)}</div>`;
    renderPagination(0, 1, 1, state.pageSize);
    updateTranslatePageButton();
    return;
  }

  grid.innerHTML = state.currentItems.map(renderCard).join("");
  renderPagination(state.total, state.page, state.totalPages, state.pageSize);
  updateTranslatePageButton();
}

async function loadItems() {
  const grid = document.getElementById("cards-grid");
  const checked = getCheckedSources();
  const dict = t();

  if (!state.starredOnly && checked.length === 0) {
    state.currentItems = [];
    state.total = 0;
    state.totalPages = 1;
    renderCardsFromState();
    return;
  }

  const params = new URLSearchParams();
  if (state.starredOnly) {
    params.set("starred", "true");
    params.set("source", "all");
  } else {
    params.set("source", checked.length === 5 ? "all" : checked.join(","));
  }
  params.set("category", state.category);
  if (state.readyOnly) params.set("playability", "READY_NOW");
  if (state.videoOnly) params.set("has_video", "true");
  if (state.q) params.set("q", state.q);
  params.set("sort", state.sort);
  params.set("hours", String(state.hours));
  params.set("page", String(state.page));
  params.set("page_size", String(state.pageSize));

  try {
    const res = await fetch(`/api/items?${params.toString()}`);
    const data = await res.json();
    updateCounts(data.source_counts);
    state.currentItems = data.items || [];
    state.total = data.total ?? state.currentItems.length;
    state.page = data.page || 1;
    state.totalPages = data.total_pages || 1;
    renderCardsFromState();
  } catch (err) {
    state.currentItems = [];
    state.total = 0;
    grid.innerHTML = `<div class="empty-state">Error: ${esc(err.message)}</div>`;
    renderPagination(0, 1, 1, state.pageSize);
    updateTranslatePageButton();
  }
}

function formatRelativeAge(ts) {
  if (!ts) return "";
  const diffSec = Math.max(0, Math.floor(Date.now() / 1000) - Number(ts));
  if (state.uiLang === "en") {
    if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))}m ago`;
    if (diffSec < 86400) return `${(diffSec / 3600).toFixed(1).replace(/\.0$/, "")}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  }
  if (diffSec < 3600) return `${Math.max(1, Math.floor(diffSec / 60))}分钟前`;
  if (diffSec < 86400) return `${(diffSec / 3600).toFixed(1).replace(/\.0$/, "")}小时前`;
  return `${Math.floor(diffSec / 86400)}天前`;
}

function renderMetrics(item) {
  const dict = t();
  const m = item.metrics || {};
  const parts = [];
  if (item.author_handle || item.author) {
    parts.push(`<span>👤 ${esc(item.author_handle || item.author)}</span>`);
  }
  const ageStr = formatRelativeAge(item.created_at_ts);
  if (ageStr) {
    parts.push(`<span>🕒 ${esc(ageStr)}</span>`);
  }
  if (m.stars !== undefined) {
    parts.push(`<span class="bm-highlight">★ ${Number(m.stars).toLocaleString()} Stars</span>`);
  }
  if (m.bookmarks) {
    parts.push(
      `<span class="bm-highlight">${esc(dict.bmLabel(Number(m.bookmarks).toLocaleString(), m.bookmark_ratio))}</span>`
    );
  }
  if (m.likes) {
    parts.push(`<span>❤️ ${Number(m.likes).toLocaleString()}</span>`);
  }
  if (m.downloads) {
    parts.push(`<span>${esc(dict.dlLabel(Number(m.downloads).toLocaleString()))}</span>`);
  }
  if (m.points) {
    parts.push(`<span>▲ ${m.points} pts · 💬 ${m.comments || 0}</span>`);
  }
  return parts.join("");
}

function proxyMediaUrl(rawUrl) {
  if (!rawUrl) return "";
  return `/api/media?url=${encodeURIComponent(rawUrl)}`;
}

function extractRawHighlights(it) {
  const rawTitle = (it.raw_title || "").trim();
  const lines = String(it.raw_text || "")
    .split(/\r?\n/)
    .map((ln) => ln.trim())
    .filter((ln) => ln && ln !== rawTitle);
  return lines.slice(0, 3).map((ln) => (ln.length > 125 ? `${ln.slice(0, 125)}…` : ln));
}

function localizeBadge(b) {
  if (state.uiLang !== "en") return b;
  return SOURCE_BADGE_EN[b] || b;
}

function localizeLinkLabel(lk) {
  const raw = lk.label || "";
  if (state.uiLang !== "en") return raw;
  return raw
    .replace("HF Space 在线试玩", "HF Space Demo")
    .replace("HF 模型权重", "HF Model")
    .replace("项目官网 / 试玩", "Website / Demo");
}

function renderCard(it) {
  const dict = t();
  const finalScore = it.jev_evaluated ? Math.round(it.jev_score) : Math.round(it.signal_score);
  const scoreCls = finalScore >= 78 ? "score-badge high" : "score-badge";
  const scoreLabel = it.jev_evaluated ? dict.scoreJev(finalScore) : dict.scoreSig(finalScore);

  const playKey = it.jev_playability || "PENDING";
  const playLabel = dict.playLabels[playKey] || playKey;
  const catLabel = dict.catLabels[it.jev_category] || it.jev_category;

  const badges = (it.sources_merged && it.sources_merged.length ? it.sources_merged : [it.source_badge])
    .map((b) => `<span class="src-tag">${esc(localizeBadge(b))}</span>`)
    .join("");

  const hasZh = !!(it.zh_translated && it.zh_title);
  // Default card display follows UI language (zh -> Chinese if translated; en -> Raw English), unless user clicked card toggle
  const override = state.cardModeOverrides[it.id]; // "zh" | "raw" | undefined
  const showZh = hasZh && (override ? override === "zh" : state.uiLang === "zh");

  const title = showZh ? it.zh_title : it.raw_title || it.zh_title || "Untitled AI Project";
  const bulletArr = showZh ? it.zh_highlights || [] : extractRawHighlights(it);
  const highlights = bulletArr.map((h) => `<li>${esc(h)}</li>`).join("");

  const proxiedImg = proxyMediaUrl(it.image_url);
  const proxiedVid = proxyMediaUrl(it.video_url);

  let mediaHtml = "";
  if (proxiedVid) {
    mediaHtml = `
      <div class="media-box has-video">
        <span class="video-pill">${esc(dict.videoPill)}</span>
        <video
          controls
          preload="metadata"
          playsinline
          poster="${esc(proxiedImg)}"
          src="${esc(proxiedVid)}"
          onplay="const p=this.parentElement.querySelector('.video-pill');if(p)p.style.display='none';"
          onerror="const box=this.parentElement;if('${esc(proxiedImg)}'){box.innerHTML='<img loading=\\'lazy\\' src=\\'${esc(proxiedImg)}\\' alt=\\'preview\\' onerror=\\'this.parentElement.style.display=&quot;none&quot;\\' />';}else{box.style.display='none';}"
        ></video>
      </div>`;
  } else if (proxiedImg) {
    mediaHtml = `<div class="media-box"><img loading="lazy" src="${esc(proxiedImg)}" alt="preview" onerror="this.parentElement.style.display='none'" /></div>`;
  }

  const deliverableBtns = (it.project_links || [])
    .slice(0, 4)
    .map(
      (lk) =>
        `<a class="link-btn primary-deliverable" href="${esc(lk.url)}" target="_blank" rel="noopener">🔗 ${esc(
          localizeLinkLabel(lk)
        )}</a>`
    )
    .join("");

  const videoDl = proxiedVid
    ? `<a class="link-btn" href="${esc(proxiedVid)}" target="_blank" rel="noopener">${esc(dict.videoDirect)}</a>`
    : "";

  let trActionBtn = "";
  if (!hasZh) {
    trActionBtn = `<button class="card-tr-btn" data-tr-id="${esc(it.id)}" type="button" title="${esc(
      dict.btnCardTrTitle
    )}">${esc(dict.btnCardTr)}</button>`;
  } else if (showZh) {
    trActionBtn = `<button class="card-raw-btn" data-toggle-card-lang="${esc(
      it.id
    )}" data-target-mode="raw" type="button" title="${esc(dict.btnCardShowRawTitle)}">${esc(
      dict.btnCardShowRaw
    )}</button>`;
  } else {
    trActionBtn = `<button class="card-raw-btn active" data-toggle-card-lang="${esc(
      it.id
    )}" data-target-mode="zh" type="button" title="${esc(dict.btnCardShowZhTitle)}">${esc(
      dict.btnCardShowZh
    )}</button>`;
  }

  return `
    <article class="radar-card">
      <div class="card-top">
        <span class="${scoreCls}">${esc(scoreLabel)}</span>
        <span class="play-badge play-${esc(playKey)}">${esc(playLabel)}</span>
        <span class="cat-tag">${esc(catLabel)}</span>
        ${badges}
        <span class="card-actions">
          ${trActionBtn}
          <button class="star-btn ${it.starred ? "starred" : ""}" data-star-id="${esc(it.id)}" type="button">
            ${esc(it.starred ? dict.starOn : dict.starOff)}
          </button>
        </span>
      </div>

      <h2 class="card-title">${esc(title)}</h2>
      ${highlights ? `<ul class="highlights-list">${highlights}</ul>` : ""}
      ${mediaHtml}

      <div class="metrics-row">${renderMetrics(it)}</div>

      <details class="raw-details">
        <summary>${esc(dict.rawDetails(it.author || localizeBadge(it.source_badge)))}</summary>
        <pre>${esc(it.raw_text)}</pre>
      </details>

      <div class="links-footer">
        ${deliverableBtns}
        ${it.original_url ? `<a class="link-btn" href="${esc(it.original_url)}" target="_blank" rel="noopener">${esc(dict.origSource)}</a>` : ""}
        ${videoDl}
      </div>
    </article>
  `;
}

async function translateItemsByIds(ids, triggerBtn) {
  if (!ids || !ids.length) return;
  const dict = t();
  const log = document.getElementById("scan-log");
  const oldLabel = triggerBtn ? triggerBtn.textContent : "";
  if (triggerBtn) {
    triggerBtn.disabled = true;
    triggerBtn.textContent = dict.btnTranslating;
  }
  log.textContent =
    state.uiLang === "en"
      ? `Translating ${ids.length} item(s) into Chinese via DeepSeek...`
      : `正在调用 DeepSeek 翻译提炼 ${ids.length} 条项目...`;

  try {
    const d = await apiPost("/api/translate", { ids });
    const map = d.results || {};
    for (const it of state.currentItems) {
      if (map[it.id]) {
        it.zh_title = map[it.id].zh_title;
        it.zh_highlights = map[it.id].zh_highlights;
        it.zh_translated = 1;
        // Show Chinese immediately on translated card even if user was in EN mode!
        state.cardModeOverrides[it.id] = "zh";
      }
    }
    renderCardsFromState();
    log.textContent =
      state.uiLang === "en"
        ? `✅ Translated ${d.translated || 0} item(s) into Chinese and saved to database`
        : `✅ 已手动完成 ${d.translated || 0} 条中文提炼并永久入库（可点卡片右上角「原」随时对照原文）`;
  } catch (e) {
    log.textContent = state.uiLang === "en" ? `❌ Translation error: ${e.message}` : `❌ 翻译失败: ${e.message}`;
    if (triggerBtn) {
      triggerBtn.disabled = false;
      triggerBtn.textContent = oldLabel;
    }
  }
}

async function triggerScan() {
  const dict = t();
  const btn = document.getElementById("btn-scan");
  const log = document.getElementById("scan-log");
  const checkedSources = getCheckedSources();
  if (!checkedSources.length) {
    alert(state.uiLang === "en" ? "Please select at least 1 data source!" : "请至少勾选 1 个数据源！");
    return;
  }
  const maxJudge = parseInt(document.getElementById("max-judge-select").value, 10) || 26;

  btn.disabled = true;
  btn.textContent = dict.btnScanBusy;
  log.textContent =
    state.uiLang === "en"
      ? `Fetching ${checkedSources.length} source(s), rescuing hidden links & running official TypeSafe Jev...`
      : `正在并发拉取 ${checkedSources.length} 个源头、穿透评论区隐藏链接并调用官方 Jev 打分（不自动消耗翻译额度）...`;

  try {
    const d = await apiPost("/api/scan", { sources: checkedSources, max_judge: maxJudge });
    const newJ = d.jev_judged_new ?? 0;
    const oldJ = d.jev_judged_backlog ?? 0;
    log.textContent =
      state.uiLang === "en"
        ? `✅ Scan complete (${d.elapsed_sec}s): Fetched ${d.total_fetched} · New ${d.new_inserted} · Rescued links ${d.rescued_comment_links} · Jev judged ${d.jev_judged} (${newJ} new + ${oldJ} backlog, filtered ${d.noise_filtered} noise)`
        : `✅ 扫描完成 (${d.elapsed_sec}s)：抓回 ${d.total_fetched} 条 · 新增入库 ${d.new_inserted} 条 · 抠出隐藏链接 ${d.rescued_comment_links} 个 · Jev 精判 ${d.jev_judged} 条 (优先评新帖 ${newJ} 条 + 补评旧帖 ${oldJ} 条，剔除水贴 ${d.noise_filtered} 条)`;
    updateCounts(d.source_counts);
    state.page = 1;
    await loadItems();
  } catch (e) {
    log.textContent = state.uiLang === "en" ? `❌ Scan failed: ${e.message}` : `❌ 扫描出错: ${e.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = t().btnScan;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  applyStaticI18n();
  const starToggleBtn = document.getElementById("btn-starred-toggle");

  // Global UI Language Switch (中文 / EN)
  document.getElementById("ui-lang-switch").addEventListener("click", (e) => {
    const btn = e.target.closest("[data-ui-lang]");
    if (!btn) return;
    const nextLang = btn.dataset.uiLang;
    if (nextLang === state.uiLang) return;
    state.uiLang = nextLang;
    localStorage.setItem("ai_radar_ui_lang", nextLang);
    state.cardModeOverrides = {};
    applyStaticI18n();
    renderCardsFromState();
  });

  // Source toggle: immediately filters the list AND controls scan scope
  document.querySelectorAll(".source-toggle input").forEach((inp) => {
    inp.addEventListener("change", () => {
      inp.closest(".source-toggle").classList.toggle("checked", inp.checked);
      if (state.starredOnly) {
        state.starredOnly = false;
        starToggleBtn.classList.remove("active");
      }
      state.page = 1;
      loadItems();
    });
  });

  document.getElementById("btn-select-all-sources").addEventListener("click", () => {
    document.querySelectorAll(".source-toggle input").forEach((inp) => {
      inp.checked = true;
      inp.closest(".source-toggle").classList.add("checked");
    });
    state.starredOnly = false;
    starToggleBtn.classList.remove("active");
    state.page = 1;
    loadItems();
  });

  starToggleBtn.addEventListener("click", () => {
    state.starredOnly = !state.starredOnly;
    starToggleBtn.classList.toggle("active", state.starredOnly);
    state.page = 1;
    loadItems();
  });

  document.getElementById("btn-scan").addEventListener("click", triggerScan);

  document.getElementById("btn-translate-page").addEventListener("click", (e) => {
    const ids = state.currentItems
      .filter((x) => !(x.zh_translated && x.zh_title))
      .map((x) => x.id);
    translateItemsByIds(ids, e.currentTarget);
  });

  // Category chips
  document.getElementById("category-chips").addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (!btn) return;
    document.querySelectorAll("#category-chips .chip").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.category = btn.dataset.cat;
    state.page = 1;
    loadItems();
  });

  document.getElementById("chk-ready-only").addEventListener("change", (e) => {
    state.readyOnly = e.target.checked;
    state.page = 1;
    loadItems();
  });

  document.getElementById("chk-video-only").addEventListener("change", (e) => {
    state.videoOnly = e.target.checked;
    state.page = 1;
    loadItems();
  });

  document.getElementById("time-select").addEventListener("change", (e) => {
    state.hours = parseInt(e.target.value, 10) || 0;
    state.page = 1;
    loadItems();
  });

  document.getElementById("sort-select").addEventListener("change", (e) => {
    state.sort = e.target.value;
    state.page = 1;
    loadItems();
  });

  let searchTimer = null;
  document.getElementById("search-input").addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.q = e.target.value.trim();
      state.page = 1;
      loadItems();
    }, 240);
  });

  // Pagination click delegation
  document.getElementById("pagination-bar").addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-page]");
    if (!btn || btn.disabled) return;
    const targetPage = parseInt(btn.dataset.page, 10);
    if (!targetPage || targetPage === state.page) return;
    state.page = targetPage;
    await loadItems();
    document.querySelector(".filter-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  // Card actions: single-card manual translate, raw/zh toggle, star
  document.getElementById("cards-grid").addEventListener("click", async (e) => {
    const trBtn = e.target.closest("[data-tr-id]");
    if (trBtn) {
      await translateItemsByIds([trBtn.dataset.trId], trBtn);
      return;
    }

    const toggleBtn = e.target.closest("[data-toggle-card-lang]");
    if (toggleBtn) {
      const cid = toggleBtn.dataset.toggleCardLang;
      state.cardModeOverrides[cid] = toggleBtn.dataset.targetMode;
      renderCardsFromState();
      return;
    }

    const btn = e.target.closest("[data-star-id]");
    if (!btn) return;
    const id = btn.dataset.starId;
    try {
      const d = await apiPost("/api/star", { id });
      if (d.ok) {
        const target = state.currentItems.find((x) => x.id === id);
        if (target) target.starred = d.starred ? 1 : 0;
        const dict = t();
        btn.classList.toggle("starred", !!d.starred);
        btn.textContent = d.starred ? dict.starOn : dict.starOff;
        loadStatus();
      }
    } catch (err) {
      console.error(err);
    }
  });

  // Settings modal
  const modal = document.getElementById("settings-modal");
  document.getElementById("btn-open-settings").addEventListener("click", () => modal.classList.remove("hidden"));
  document.getElementById("btn-close-settings").addEventListener("click", () => modal.classList.add("hidden"));
  document.getElementById("btn-cancel-settings").addEventListener("click", () => modal.classList.add("hidden"));

  document.getElementById("btn-save-settings").addEventListener("click", async () => {
    const adminVal = (document.getElementById("inp-admin-pwd")?.value || "").trim();
    if (adminVal) {
      localStorage.setItem("ai_radar_admin_pwd", adminVal);
    }
    const payload = {
      typesafe_api_key: document.getElementById("inp-jev-key").value,
      twitter_auth_token: document.getElementById("inp-x-auth").value,
      twitter_ct0: document.getElementById("inp-x-ct0").value,
      openrouter_api_key: document.getElementById("inp-or-key").value,
    };
    const hasServerUpdates = Object.values(payload).some((v) => v && v.trim());
    try {
      if (hasServerUpdates) {
        await apiPost("/api/settings", payload);
      }
      modal.classList.add("hidden");
      await loadStatus();
    } catch (err) {
      alert(err.message);
    }
  });

  loadStatus();
  loadItems();
});
