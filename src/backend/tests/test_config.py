import os
import pathlib
# pyrefly: ignore [missing-import]
import pytest
from config import Settings, get_settings

def test_settings_defaults(tmp_path, monkeypatch):
    # Ensure that env file is not required for defaults
    monkeypatch.delenv('APP_NAME', raising=False)
    # Create a temporary .env file with no content
    env_path = tmp_path / ".env"
    env_path.write_text("")
    # Monkeypatch BASE_DIR to point to tmp_path's parent
    # Settings uses BASE_DIR.parent for .env location; we simulate by setting env var for path
    monkeypatch.setenv('PYTHONPATH', str(tmp_path))
    # Instantiate settings
    settings = Settings(_env_file=env_path)
    assert settings.app_name == "Apply-Agent API"
    # Database path should be relative to project root / data / apply_agent.db
    expected_db_path = pathlib.Path(__file__).resolve().parents[3] / "data" / "apply_agent.db"
    assert settings.database_path == expected_db_path
    # Ensure default CORS origins are set
    assert "http://localhost:5173" in settings.cors_origins

def test_get_settings_caching():
    s1 = get_settings()
    s2 = get_settings()
    # lru_cache should return the same instance
    assert s1 is s2
