from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # xAI
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    # Override via env XAI_MODEL if xAI publishes a different id (e.g. "grok-4.3").
    xai_model: str = "grok-4-latest"
    xai_zero_data_retention: bool = False

    # App
    cors_origins: str = "http://localhost:3000"
    max_upload_mb: int = 50
    chunk_tokens: int = 800
    chunk_overlap_tokens: int = 120
    top_k: int = 6

    # OCR
    ocr_enabled: bool = True
    ocr_lang: str = "eng"
    ocr_dpi: int = 300

    # Storage
    data_dir: str = "./data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
