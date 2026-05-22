"""Tests for ExternalApiAdapter, QwenAdapter fallback, and build_rag_prompt.

All tests are fully mocked — no real HTTP calls, no model loading.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── build_rag_prompt ─────────────────────────────────────────────────────────

class TestBuildRagPrompt:
    def test_injects_cv_context(self, tmp_path, monkeypatch):
        """Placeholder variables in the template are replaced with JSON context."""
        from AI.llm.llm_interface import build_rag_prompt

        cv_ctx = {"name": "Alice", "skills": ["Python"]}
        prompt = build_rag_prompt("cv", cv_context=cv_ctx)
        # The cv_context_json placeholder should be replaced
        assert "Alice" in prompt
        assert "Python" in prompt

    def test_injects_job_context(self, tmp_path, monkeypatch):
        from AI.llm.llm_interface import build_rag_prompt

        job_ctx = {"title": "ML Engineer", "company": "Acme"}
        prompt = build_rag_prompt("cover_letter", job_context=job_ctx)
        assert "ML Engineer" in prompt
        assert "Acme" in prompt

    def test_none_context_renders_null(self):
        from AI.llm.llm_interface import build_rag_prompt

        prompt = build_rag_prompt("cv", cv_context=None, job_context=None)
        assert "null" in prompt  # JSON null is injected

    def test_unknown_scenario_uses_fallback(self):
        from AI.llm.llm_interface import build_rag_prompt

        prompt = build_rag_prompt("nonexistent_scenario")
        # Should not raise; falls back to generic prompt
        assert len(prompt) > 0

    def test_few_shot_examples_injected(self):
        from AI.llm.llm_interface import build_rag_prompt

        examples = [{"source_id": "past_application_1", "cv_text_snippet": "Engineered X"}]
        prompt = build_rag_prompt("cv", few_shot_examples=examples)
        assert "past_application_1" in prompt

    def test_legacy_build_prompt_shim(self):
        """build_prompt shim must not raise and must include user query."""
        from AI.llm.llm_interface import build_prompt

        result = build_prompt("cv", "What skills should I highlight?")
        assert "What skills should I highlight?" in result


# ── get_llm_adapter factory ───────────────────────────────────────────────────

class TestGetLlmAdapterFactory:
    def test_returns_external_when_provider_is_external(self):
        from AI.llm.llm_interface import ExternalApiAdapter, get_llm_adapter

        mock_settings = MagicMock()
        mock_settings.is_external_provider = True
        mock_settings.external_api_base_url = "https://api.example.com/v1"
        mock_settings.external_api_key = "sk-test"
        mock_settings.external_api_model = "gpt-4o"
        mock_settings.external_api_timeout = 30

        adapter = get_llm_adapter(mock_settings)
        assert isinstance(adapter, ExternalApiAdapter)

    def test_warns_when_key_is_empty(self, caplog):
        import logging
        from AI.llm.llm_interface import get_llm_adapter

        mock_settings = MagicMock()
        mock_settings.is_external_provider = True
        mock_settings.external_api_base_url = "https://api.example.com/v1"
        mock_settings.external_api_key = ""
        mock_settings.external_api_model = "gpt-4o"
        mock_settings.external_api_timeout = 30

        with caplog.at_level(logging.WARNING, logger="AI.llm.llm_interface"):
            get_llm_adapter(mock_settings)

        assert any("empty" in r.message.lower() for r in caplog.records)


# ── ExternalApiAdapter ────────────────────────────────────────────────────────

class TestExternalApiAdapter:
    """Uses httpx mock so no real network calls are made."""

    def _make_adapter(self):
        from AI.llm.llm_interface import ExternalApiAdapter

        return ExternalApiAdapter(
            base_url="https://fake.openrouter.ai/api/v1",
            api_key="sk-test",
            model="openai/gpt-4o-mini",
            timeout=10,
        )

    def _chat_response_json(self, content: str) -> dict:
        return {
            "choices": [{"message": {"content": content}}]
        }

    def test_generate_returns_content(self):
        import httpx
        from AI.llm.llm_interface import ExternalApiAdapter

        adapter = self._make_adapter()
        fake_response = MagicMock(spec=httpx.Response)
        fake_response.is_success = True
        fake_response.json.return_value = self._chat_response_json("Hello from GPT")

        with patch.object(adapter._httpx.Client, "__enter__") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.post.return_value = fake_response

            result = adapter.generate("Say hello")

        assert result == "Hello from GPT"

    def test_generate_raises_on_error_status(self):
        import httpx
        from AI.llm.llm_interface import ExternalApiAdapter, ExternalApiError

        adapter = self._make_adapter()
        fake_response = MagicMock(spec=httpx.Response)
        fake_response.is_success = False
        fake_response.status_code = 401
        fake_response.text = "Unauthorized"

        with patch.object(adapter._httpx.Client, "__enter__") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_client.post.return_value = fake_response
            with pytest.raises(ExternalApiError) as exc_info:
                adapter.generate("test")

        assert exc_info.value.status == 401

    def test_parse_sse_line_extracts_delta(self):
        from AI.llm.llm_interface import ExternalApiAdapter

        line = 'data: {"choices":[{"delta":{"content":"hello"}}]}'
        result = ExternalApiAdapter._parse_sse_line(line)
        assert result == "hello"

    def test_parse_sse_line_ignores_done(self):
        from AI.llm.llm_interface import ExternalApiAdapter

        result = ExternalApiAdapter._parse_sse_line("data: [DONE]")
        assert result == ""

    def test_parse_sse_line_ignores_non_data(self):
        from AI.llm.llm_interface import ExternalApiAdapter

        result = ExternalApiAdapter._parse_sse_line("event: ping")
        assert result == ""

    def test_generate_stream_yields_tokens(self):
        from AI.llm.llm_interface import ExternalApiAdapter

        adapter = self._make_adapter()

        sse_lines = [
            'data: {"choices":[{"delta":{"content":"To"}}]}',
            'data: {"choices":[{"delta":{"content":"ken"}}]}',
            "data: [DONE]",
        ]

        mock_resp_ctx = MagicMock()
        mock_resp_ctx.__enter__ = MagicMock(return_value=mock_resp_ctx)
        mock_resp_ctx.__exit__ = MagicMock(return_value=False)
        mock_resp_ctx.is_success = True
        mock_resp_ctx.iter_lines.return_value = iter(sse_lines)

        mock_client_ctx = MagicMock()
        mock_client_ctx.__enter__ = MagicMock(return_value=mock_client_ctx)
        mock_client_ctx.__exit__ = MagicMock(return_value=False)
        mock_client_ctx.stream.return_value = mock_resp_ctx

        with patch.object(adapter._httpx, "Client", return_value=mock_client_ctx):
            tokens = list(adapter.generate_stream("prompt"))

        assert tokens == ["To", "ken"]
