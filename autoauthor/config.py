"""autoauthor/config.py — 통합 설정 관리"""
import os
import importlib.util
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AutoAuthorConfig:
    # Naver
    naver_client_id: str = ""
    naver_client_secret: str = ""
    use_naver_openapi: bool = True
    naver_ad_customer_id: str = ""
    naver_ad_license: str = ""
    naver_ad_secret: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    # TMDB
    tmdb_api_key: str = ""
    tmdb_read_access_token: str = ""

    # YouTube
    youtube_api_key: str = ""

    # Optional sources
    enable_watcha_pedia: bool = True
    enable_theqoo: bool = False  # 기본 비활성

    # Pipeline
    request_delay: float = 1.0
    output_dir: str = "results"
    db_path: str = "data/autoauthor.db"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "exaone3.5:7.8b"


def load_config() -> AutoAuthorConfig:
    """mvforrest_seo_config.py + 환경변수에서 설정 로드"""
    cfg = AutoAuthorConfig()

    # 1) 기존 config 파일에서 로드
    try:
        spec = importlib.util.find_spec("mvforrest_seo_config")
        if spec and spec.origin:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            cfg.naver_client_id = getattr(mod, "NAVER_CLIENT_ID", cfg.naver_client_id)
            cfg.naver_client_secret = getattr(mod, "NAVER_CLIENT_SECRET", cfg.naver_client_secret)
            cfg.use_naver_openapi = getattr(mod, "USE_NAVER_OPENAPI", cfg.use_naver_openapi)
            cfg.gemini_api_key = getattr(mod, "GEMINI_API_KEY", cfg.gemini_api_key)
            cfg.gemini_model = getattr(mod, "GEMINI_MODEL", cfg.gemini_model)
            cfg.tmdb_api_key = getattr(mod, "TMDB_API_KEY", cfg.tmdb_api_key)
            cfg.tmdb_read_access_token = getattr(mod, "TMDB_READ_ACCESS_TOKEN", cfg.tmdb_read_access_token)
    except Exception:
        pass

    # 2) 환경변수 오버라이드 (dotenv 지원)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    env_map = {
        "NAVER_CLIENT_ID": "naver_client_id",
        "NAVER_CLIENT_SECRET": "naver_client_secret",
        "NAVER_AD_CUSTOMER_ID": "naver_ad_customer_id",
        "NAVER_AD_LICENSE": "naver_ad_license",
        "NAVER_AD_SECRET": "naver_ad_secret",
        "GEMINI_API_KEY": "gemini_api_key",
        "TMDB_API_KEY": "tmdb_api_key",
        "TMDB_READ_ACCESS_TOKEN": "tmdb_read_access_token",
        "YOUTUBE_API_KEY": "youtube_api_key",
        "OLLAMA_BASE_URL": "ollama_base_url",
        "OLLAMA_MODEL": "ollama_model",
    }
    for env_key, attr in env_map.items():
        val = os.environ.get(env_key)
        if val:
            setattr(cfg, attr, val)

    return cfg
