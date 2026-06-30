from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    database_url: str = ""

    frontend_origin: str = "http://localhost:3000"
    max_file_mb: int = 25

    db_pool_min_size: int = 1
    db_pool_max_size: int = 5

    debug_timing: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    max_source_chars: int = 60000

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()