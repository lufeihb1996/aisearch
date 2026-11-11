import os
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
IS_VERCEL: bool = bool(os.environ.get("VERCEL"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "AI Tech Radar"
    APP_VERSION: str = "1.1.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8096

    # Supabase Cloud Database (auto-detected from Vercel Supabase Integration or manual env vars)
    SUPABASE_URL: Optional[str] = None
    NEXT_PUBLIC_SUPABASE_URL: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # Optional write-protection password for public Vercel deployments
    RADAR_ADMIN_PASSWORD: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None

    # AI & Social Credentials
    TYPESAFE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "deepseek/deepseek-v4-flash"

    TWITTER_AUTH_TOKEN: Optional[str] = None
    TWITTER_CT0: Optional[str] = None


settings = Settings()

# In-memory cache populated from Supabase `public.radar_settings` when running in cloud mode
_runtime_overrides: Dict[str, str] = {}


def apply_runtime_overrides(kv: Dict[str, str]) -> None:
    if not kv:
        return
    for k, v in kv.items():
        val = (v or "").strip()
        if not val:
            continue
        _runtime_overrides[k] = val
        if hasattr(settings, k):
            setattr(settings, k, val)


def get_system_proxy() -> Optional[str]:
    if IS_VERCEL:
        return None
    proxies = urllib.request.getproxies()
    return proxies.get("https") or proxies.get("http") or None


def _read_dotenv_key(var_name: str) -> str:
    if not IS_VERCEL and ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, v = s.split("=", 1)
                    if k.strip() == var_name and v.strip():
                        return v.strip()
        except Exception:
            pass
    return ""


def get_supabase_url() -> str:
    for key_name in ("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"):
        val = (
            _read_dotenv_key(key_name)
            or getattr(settings, key_name, None)
            or os.environ.get(key_name, "")
        )
        if val and str(val).strip():
            return str(val).strip().rstrip("/")
    return ""


def get_supabase_server_key() -> str:
    for key_name in ("SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY"):
        val = (
            _read_dotenv_key(key_name)
            or getattr(settings, key_name, None)
            or os.environ.get(key_name, "")
        )
        if val and str(val).strip():
            return str(val).strip()
    return ""


def is_supabase_enabled() -> bool:
    return bool(get_supabase_url() and get_supabase_server_key())


def get_admin_password() -> str:
    for key_name in ("RADAR_ADMIN_PASSWORD", "ADMIN_PASSWORD"):
        val = (
            _runtime_overrides.get(key_name)
            or _read_dotenv_key(key_name)
            or getattr(settings, key_name, None)
            or os.environ.get(key_name, "")
        )
        if val and str(val).strip():
            return str(val).strip()
    return ""


def get_typesafe_api_key() -> str:
    return (
        _runtime_overrides.get("TYPESAFE_API_KEY")
        or _read_dotenv_key("TYPESAFE_API_KEY")
        or settings.TYPESAFE_API_KEY
        or os.environ.get("TYPESAFE_API_KEY", "")
    ).strip()


def get_openrouter_api_key() -> str:
    if _runtime_overrides.get("OPENROUTER_API_KEY"):
        return _runtime_overrides["OPENROUTER_API_KEY"].strip()
    dotenv_val = _read_dotenv_key("OPENROUTER_API_KEY")
    if dotenv_val:
        return dotenv_val
    key = (settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")).strip()
    if key:
        return key
    if sys.platform == "win32" and not IS_VERCEL:
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as reg_key:
                val, _ = winreg.QueryValueEx(reg_key, "OPENROUTER_API_KEY")
                if val and str(val).strip():
                    return str(val).strip()
        except Exception:
            pass
    return ""
