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

    # ── LLM provider routing ─────────────────────────────────
    # "local"    → load Qwen LoRA model from disk (requires GPU)
    # "external" → proxy to any OpenAI-compatible API endpoint
    llm_provider: str = Field(default="local", alias="LLM_PROVIDER")

    # ── External API (OpenAI-compatible endpoint) ────────────
    # User controls all three fields — no predefined provider list.
    # Example: OpenRouter → https://openrouter.ai/api/v1
    #          Groq       → https://api.groq.com/openai/v1
    #          OpenAI     → https://api.openai.com/v1
    external_api_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="EXTERNAL_API_BASE_URL",
    )
    external_api_key: str = Field(default="", alias="EXTERNAL_API_KEY")
    external_api_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="EXTERNAL_API_MODEL",
    )
    external_api_timeout: int = Field(default=120, alias="EXTERNAL_API_TIMEOUT")

    # ── Local model optimisations (Qwen 1.5B LoRA) ──────────
    # 4-bit BitsAndBytes quantization — reduces VRAM from ~3.5 GB → ~1.2 GB.
    # Requires bitsandbytes>=0.43 and a CUDA GPU.
    llm_quantize_4bit: bool = Field(default=True, alias="LLM_QUANTIZE_4BIT")
    # Generation length — raised from 256 so full CVs / cover letters are produced.
    llm_max_new_tokens: int = Field(default=4096, alias="LLM_MAX_NEW_TOKENS")
    # torch.compile speedup (first-call overhead ~30 s; subsequent calls ~20% faster).
    llm_use_torch_compile: bool = Field(default=False, alias="LLM_USE_TORCH_COMPILE")

    # ── RAG tuning ───────────────────────────────────────────
    # Maximum number of past accepted/confirmed jobs used as few-shot examples.
    rag_few_shot_limit: int = Field(default=3, alias="RAG_FEW_SHOT_LIMIT")
    # Maximum characters of each example CV / cover letter injected into prompt.
    rag_example_max_chars: int = Field(default=800, alias="RAG_EXAMPLE_MAX_CHARS")

    # Phase 7 – Job‑match & LaTeX PDF generation
    latex_output_dir: Path = Field(default_factory=lambda: BASE_DIR.parent / "data" / "latex")
    max_job_history: int = 100
    pdflatex_timeout_seconds: int = 60

    @property
    def database_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.database_path.as_posix()}"

    @property
    def is_external_provider(self) -> bool:
        """True when requests should be routed to the external API adapter."""
        return self.llm_provider.lower() == "external"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
