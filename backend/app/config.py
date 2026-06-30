from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    database_url: str = ""

    frontend_origin: str = "http://localhost:3000"

    max_file_mb: int = 10
    max_source_chars: int = 12000
    max_chunks_per_source: int = 10
    embedding_batch_size: int = 1

    db_pool_min_size: int = 1
    db_pool_max_size: int = 1

    debug_timing: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()