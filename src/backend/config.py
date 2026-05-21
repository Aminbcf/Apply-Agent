from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Apply-Agent API"
    database_path: Path = Field(default_factory=lambda: BASE_DIR.parent / "data" / "apply_agent.db")
    llm_provider: str = "placeholder"
    llm_model_name: str = "qwen"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:1420",
            "tauri://localhost",
        ]
    )
    cache_size: int = 128

    cv_upload_max_bytes: int = 5 * 1024 * 1024
    debug_mode: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.database_path.as_posix()}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
