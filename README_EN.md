<div align="center">

# 📡 AI Tech Radar (Cloud Edition)

**Zero-Keyword 5-Source AI Discovery · Bookmark-Ratio Signal · 1st-Reply Link Rescue · Vercel + Supabase Ready**

<p>
  <a href="./README.md"><img src="https://img.shields.io/badge/🇨🇳_简体中文-点击切换-334155?style=for-the-badge" alt="简体中文" /></a>
  <a href="./README_EN.md"><img src="https://img.shields.io/badge/🇬🇧_English-Active-06b6d4?style=for-the-badge" alt="English" /></a>
</p>

<p>
  <img src="https://img.shields.io/badge/Deploy-Vercel%20Serverless-000000?style=flat-square&logo=vercel" alt="Vercel" />
  <img src="https://img.shields.io/badge/Database-Supabase%20Postgres%20%2F%20SQLite-10b981?style=flat-square&logo=supabase" alt="Supabase / SQLite" />
  <img src="https://img.shields.io/badge/Judge-TypeSafe%20Jev%20System--1-f59e0b?style=flat-square" alt="TypeSafe Jev" />
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-64748b?style=flat-square" alt="MIT License" /></a>
</p>

</div>

---

## 🎯 Overview

**AI Tech Radar** is a 4-stage AI intelligence funnel built to surface genuinely playable **open-weights models, ComfyUI/video/audio workflows, low-VRAM GPU hacks, and indie AI builds** across **𝕏 (Twitter), HuggingFace, GitHub, Reddit, and Hacker News**.

This **Cloud Edition** runs natively on **Vercel Python Serverless + Supabase Postgres** (with RLS lockdown, single-round-trip Postgres RPC pagination, 3MB Range-clamped video streaming, and admin write protection), while preserving zero-config **local SQLite fallback** for local development.

---

## ☁️ Deploy on Vercel + Supabase (2 Minutes)

### Step 1: Import into Vercel
1. Push this repository to your GitHub account.
2. Import the repository at [vercel.com/new](https://vercel.com/new) (Vercel auto-detects **FastAPI** at `app/main.py` and reads [`vercel.json`](./vercel.json)).

### Step 2: Set Vercel Environment Variables

| Variable | Required | Description |
| :--- | :---: | :--- |
| `SUPABASE_URL` | **Yes** | Your Supabase Project URL (`https://<project-ref>.supabase.co`) |
| `SUPABASE_SECRET_KEY` | **Yes** | Server secret key `sb_secret_...` from **Supabase -> Settings -> API Keys** (legacy `SUPABASE_SERVICE_ROLE_KEY` `eyJ...` is also supported) |
| `RADAR_ADMIN_PASSWORD` | **Recommended** | Custom admin password protecting `POST /api/scan`, `/api/translate`, `/api/star`, and `/api/settings` on public URLs |
| `TYPESAFE_API_KEY` | Recommended | Official TypeSafe Jev key from [console.typesafe.ai](https://console.typesafe.ai) |
| `OPENROUTER_API_KEY` | Recommended | OpenRouter key ([openrouter.ai/keys](https://openrouter.ai/keys)) for manual DeepSeek Chinese digest |
| `TWITTER_AUTH_TOKEN` | Optional | X web cookie `auth_token` (40 chars; can also be updated anytime from the Web UI modal) |
| `TWITTER_CT0` | Optional | X web cookie `ct0` (160 chars; can also be updated anytime from the Web UI modal) |

Click **Deploy**! On first scan or translation in the browser, enter your `RADAR_ADMIN_PASSWORD` once—it is cached in `localStorage` automatically.

---

## 💻 Local Quickstart

```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
cp .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8096
```
Open **http://127.0.0.1:8096** (falls back to local SQLite automatically if `SUPABASE_*` variables are left empty).

---

## 📄 License
Released under the [MIT License](./LICENSE).
