<div align="center">

# 📡 AI 新物种猎手雷达 · AI Tech Radar (Cloud Edition)

**5 源无词捕获 · 书签收藏比提纯 · 评论区一楼穿透 · TypeSafe Jev 硬核终审 · Vercel + Supabase 云原生版**

<p>
  <a href="./README.md"><img src="https://img.shields.io/badge/🇨🇳_简体中文-当前阅读-06b6d4?style=for-the-badge" alt="简体中文" /></a>
  <a href="./README_EN.md"><img src="https://img.shields.io/badge/🇬🇧_English-Click_to_Switch-334155?style=for-the-badge" alt="English" /></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Deploy-Vercel%20Serverless-000000?style=flat-square&logo=vercel" alt="Vercel" />
  <img src="https://img.shields.io/badge/Database-Supabase%20Postgres%20%2F%20SQLite-10b981?style=flat-square&logo=supabase" alt="Supabase / SQLite" />
  <img src="https://img.shields.io/badge/Judge-TypeSafe%20Jev%20System--1-f59e0b?style=flat-square" alt="TypeSafe Jev" />
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-64748b?style=flat-square" alt="MIT License" /></a>
</p>

</div>

---

## 🎯 项目简介

**AI Tech Radar** 是一套专为 AI 极客与独立开发者设计的 **5 源无词捕获与硬核提纯雷达**。支持 **Vercel Serverless + Supabase Postgres 云端随时随地访问**，同时也完整兼容 **本地一键 SQLite 零配置运行**。

1. **5 大高信号源头共振**：同时捕获 **𝕏（推荐流 + 关注流 + 热榜词反查）**、**HuggingFace 实时飙升榜**、**GitHub 近 12 天暴涨新库**、**Reddit 三大 AI 社区热帖** 与 **Hacker News `Show HN`**，同一仓库跨平台出现自动合并徽章并提权。
2. **X 评论区一楼穿透**：自动识别主贴只放视频、把真仓库藏在一楼回复里的推文，调用 `TweetDetail` 抠回隐藏 GitHub / HuggingFace 链接（已入库旧帖自动跳过）。
3. **TypeSafe Jev 四维终审 + 新帖绝对优先**：每次扫描优先精判刚入库的新帖，自动剔除 `NOISE` 水贴与纯营销号，已判条目永久不重复计费。
4. **按需手动翻译 + 公网防刷保护**：扫描过程 **0 翻译 Token 消耗**；点击单卡 `🌐 译` 或顶部 `🌐 翻译本页` 按需调用 `deepseek/deepseek-v4-flash` 提炼中文看点，并支持配置 `RADAR_ADMIN_PASSWORD` 防止公网访客盗刷额度。

---

## ☁️ 部署到 Vercel + Supabase（2 分钟上云）

本项目已内置 [`vercel.json`](./vercel.json)（锁定东京 `hnd1` 节点与 60s 函数超时）和纯 Python HTTPS PostgREST 存储引擎（零 C 扩展编译依赖，秒级构建）。

### 第 1 步：导入 GitHub 仓库到 Vercel
1. 将本仓库推送到你的 GitHub；
2. 打开 [vercel.com/new](https://vercel.com/new)，导入该 GitHub 仓库（Framework Preset 保持自动识别的 **FastAPI** 即可）。

### 第 2 步：在 Vercel 填写环境变量（Environment Variables）

在 Vercel 项目部署页面的 **Environment Variables** 中填入以下变量：

| 变量名 | 是否必填 | 说明与获取方式 |
| :--- | :---: | :--- |
| `SUPABASE_URL` | **必填** | 你的 Supabase 项目地址（如 `https://<project-ref>.supabase.co`） |
| `SUPABASE_SECRET_KEY` | **必填** | Supabase **Settings -> API Keys** 中的 `sb_secret_...` 密钥（或填 `SUPABASE_SERVICE_ROLE_KEY` 旧版 `eyJ...` 密钥均可） |
| `RADAR_ADMIN_PASSWORD` | **强烈推荐** | 自定义一个管理员口令（如 `my-radar-888`）。设置后，所有人可浏览列表，但触发**扫描 / 翻译 / 收藏 / 改配置**时需校验口令，防止陌生人消耗你的 API 额度 |
| `TYPESAFE_API_KEY` | 推荐 | [console.typesafe.ai](https://console.typesafe.ai) 官方 Jev 裁判密钥（也可部署后在网页弹窗保存进云端库） |
| `OPENROUTER_API_KEY` | 推荐 | [openrouter.ai/keys](https://openrouter.ai/keys) 密钥，用于手动点击中文提炼 |
| `TWITTER_AUTH_TOKEN` | 可选 | X 网页版 Cookie 中的 `auth_token`（40位，启用 𝕏 源时填写，支持网页弹窗随时更新） |
| `TWITTER_CT0` | 可选 | X 网页版 Cookie 中的 `ct0`（160位，启用 𝕏 源时填写，支持网页弹窗随时更新） |

点击 **Deploy**，约 30 秒即可获得全球可访问的 HTTPS 雷达终端！首次点击「扫描」或「翻译」时输入一次你的 `RADAR_ADMIN_PASSWORD`，浏览器会自动记住，之后与本地丝滑一致。

---

## 💻 本地开发运行（自动支持 Supabase 或 SQLite）

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 2. 复制环境变量模板（不填 SUPABASE_* 时自动降级使用本地 SQLite）
cp .env.example .env

# 3. 启动本地服务
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8096
```
浏览器打开：**http://127.0.0.1:8096**（Windows 用户也可直接双击 `start-ai-radar.bat`）。

---

## 📂 项目结构

```text
AI-Tech-Radar/
├── app/
│   ├── api/routes.py                # REST API + 公网口令守卫 + Vercel 3MB 视频分片流式代理
│   ├── core/
│   │   ├── config.py                # 环境变量 & Supabase 云端动态配置热同步
│   │   ├── supabase_store.py        # 纯 Python PostgREST + Postgres RPC 高速云端引擎
│   │   └── database.py              # Supabase / 本地 SQLite 双模无缝路由层
│   ├── services/                    # 5 源抓取器、一楼评论穿透、收藏率初筛、Jev 终审与 DeepSeek 提炼
│   ├── static/ & templates/         # 中英双语极客雷达前端界面
│   └── main.py                      # FastAPI & Vercel Serverless 入口
├── vercel.json                      # Vercel 函数时长 (60s) 与区域 (hnd1) 配置
├── .vercelignore                    # Vercel 打包瘦身规则
├── .env.example                     # 环境变量模板（零真实密钥）
└── requirements.txt                 # 极简纯 Python 依赖清单
```

---

## 📄 开源协议
基于 [MIT License](./LICENSE) 开源。
