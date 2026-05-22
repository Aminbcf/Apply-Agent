"""LLM adapter layer for Apply-Agent.

Public API
----------
- :class:`LLMAdapter`         – abstract base for all adapters
- :class:`LlamaCppAdapter`    – local fine-tuned Qwen model (GGUF format)
- :class:`ExternalApiAdapter` – any OpenAI-compatible REST endpoint
- :func:`get_llm_adapter`     – factory: returns the correct adapter from settings
- :func:`build_rag_prompt`    – compose a full prompt with all RAG context blocks
- :func:`build_prompt`        – legacy shim (calls build_rag_prompt with empty context)
- :func:`get_system_prompt`   – load a raw system-prompt template from prompts/
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import AsyncGenerator, Generator, List, Optional

logger = logging.getLogger(__name__)

# ── Abstract base ─────────────────────────────────────────────────────────────


class LLMAdapter(abc.ABC):
    """Abstract interface for LLM models.

    All adapters must implement :meth:`generate` (sync) and may override
    :meth:`generate_stream` for true token-by-token streaming.
    """

    @abc.abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a complete response for *prompt* and return it."""
        raise NotImplementedError

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Yield tokens incrementally.

        Default falls back to non-streaming :meth:`generate` in a single chunk.
        Subclasses should override for real streaming.
        """
        yield self.generate(prompt)

    async def agenerate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Async variant of :meth:`generate_stream` for use inside async contexts.

        Default runs the sync generator in a thread so the event loop is not blocked.
        """
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[Optional[str]] = asyncio.Queue()

        def _run():
            try:
                for token in self.generate_stream(prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, token)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token


# ── Local Qwen LoRA adapter ───────────────────────────────────────────────────


class QwenAdapter(LLMAdapter):
    """Load the fine-tuned Qwen LoRA model from the local directory.

    Applies 4-bit BitsAndBytes quantization when ``settings.llm_quantize_4bit``
    is *True* (requires ``bitsandbytes>=0.43`` and a CUDA GPU).

    The model directory is ``src/backend/AI/llm/final_lora_adapter``.
    """

    def __init__(self) -> None:
        from config import settings  # noqa: PLC0415 – avoid circular at module level

        import torch  # noqa: PLC0415
        from peft import PeftModel  # noqa: PLC0415
        from transformers import (  # noqa: PLC0415
            AutoModelForCausalLM,
            AutoTokenizer,
            TextIteratorStreamer,
            pipeline,
        )

        self._TextIteratorStreamer = TextIteratorStreamer
        self._settings = settings

        model_dir = Path(__file__).parent / "final_lora_adapter"

        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True)  # nosec B615

        # Read the base model ID from the adapter config
        with open(model_dir / "adapter_config.json", "r", encoding="utf-8") as fh:
            adapter_cfg = json.load(fh)
        base_model_id: str = adapter_cfg.get("base_model_name_or_path", "Qwen/Qwen2.5-1.5B-Instruct")

        device_map = "auto" if torch.cuda.is_available() else "cpu"
        logger.info("QwenAdapter: device_map=%s quantize_4bit=%s", device_map, settings.llm_quantize_4bit)

        # Build quantization config for 4 GB VRAM
        quantization_config = None
        if settings.llm_quantize_4bit and torch.cuda.is_available():
            try:
                from transformers import BitsAndBytesConfig  # noqa: PLC0415
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,  # saves ~0.5 GB extra
                )
                logger.info("QwenAdapter: 4-bit BitsAndBytes quantization enabled")
            except ImportError:
                logger.warning(
                    "bitsandbytes not installed – loading model at full precision. "
                    "Install with: pip install bitsandbytes>=0.43"
                )

        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            quantization_config=quantization_config,
            device_map=device_map,
            trust_remote_code=True,
        )
        self.model = PeftModel.from_pretrained(base_model, model_dir)

        # Optional torch.compile for ~20 % inference speed-up
        if settings.llm_use_torch_compile:
            try:
                import torch._dynamo  # noqa: PLC0415
                self.model = torch.compile(self.model, mode="reduce-overhead")
                logger.info("QwenAdapter: torch.compile enabled")
            except Exception:  # noqa: BLE001
                logger.warning("torch.compile not available – skipping")

        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            dtype=getattr(self.model, "dtype", None),
        )
        self._max_new_tokens = settings.llm_max_new_tokens

    def generate(self, prompt: str) -> str:
        result = self.generator(
            prompt,
            max_new_tokens=self._max_new_tokens,
            max_length=None,
            return_full_text=False,
        )[0]
        return result["generated_text"].strip()

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Yield tokens incrementally via :class:`~transformers.TextIteratorStreamer`."""
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        streamer = self._TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        generation_kwargs = {
            **inputs,
            "max_new_tokens": self._max_new_tokens,
            "streamer": streamer,
        }

        thread = threading.Thread(
            target=self.model.generate,
            kwargs=generation_kwargs,
            daemon=True,
        )
        thread.start()

        for token in streamer:
            if token:
                yield token

        thread.join(timeout=120)


# ── Local GGUF adapter (llama.cpp) ─────────────────────────────────────────────

class LlamaCppAdapter(LLMAdapter):
    """Load the fine-tuned model via llama.cpp for maximum speed.
    
    Expects a .gguf file (e.g. model.gguf) in the final_lora_adapter directory.
    """
    def __init__(self) -> None:
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is required for LlamaCppAdapter. "
                "Install with: pip install llama-cpp-python"
            ) from exc
            
        from config import settings
        
        model_dir = Path(__file__).parent / "final_lora_adapter"
        gguf_path = model_dir / "model.gguf"
        
        if not gguf_path.exists():
            raise FileNotFoundError(
                f"GGUF model not found at {gguf_path}. "
                "Please run scripts/export_to_gguf.py to convert your fine-tuned model."
            )
            
        logger.info("LlamaCppAdapter: Loading %s", gguf_path)
        
        self.model = Llama(
            model_path=str(gguf_path),
            n_gpu_layers=-1, # Offload all layers to GPU if possible
            n_ctx=8192,
            verbose=False,
        )
        self._max_new_tokens = settings.llm_max_new_tokens
        self._lock = threading.Lock()

    def generate(self, prompt: str) -> str:
        with self._lock:
            result = self.model.create_completion(
                prompt=prompt,
                max_tokens=self._max_new_tokens,
                stream=False,
                repeat_penalty=1.1,
                stop=["[[[", "[[source:", "<|im_end|>"]
            )
        return result["choices"][0]["text"].strip()

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        with self._lock:
            stream = self.model.create_completion(
                prompt=prompt,
                max_tokens=self._max_new_tokens,
                stream=True,
                repeat_penalty=1.1,
                stop=["[[[", "[[source:", "<|im_end|>"]
            )
            for chunk in stream:
                token = chunk["choices"][0].get("text", "")
                if token:
                    yield token

# ── External API adapter ──────────────────────────────────────────────────────


class ExternalApiError(RuntimeError):
    """Raised when the external API returns an error response."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"ExternalAPI HTTP {status}: {message}")
        self.status = status


class ExternalApiAdapter(LLMAdapter):
    """Proxy to any OpenAI-compatible REST API.

    The user fully controls ``base_url``, ``model``, and ``api_key`` —
    works with OpenRouter, Groq, OpenAI, Mistral, Ollama, etc.

    Parameters
    ----------
    base_url:
        Root URL of the OpenAI-compatible endpoint (no trailing slash needed).
        Example: ``https://openrouter.ai/api/v1``
    api_key:
        Bearer token / secret key for the provider.
    model:
        Model identifier as the provider expects it.
        Example: ``openai/gpt-4o-mini``, ``llama-3-8b-instruct``
    timeout:
        Request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 120,
    ) -> None:
        try:
            import httpx  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "httpx is required for ExternalApiAdapter. "
                "Install with: pip install httpx>=0.27"
            ) from exc

        self._httpx = httpx
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        logger.info(
            "ExternalApiAdapter: base_url=%s model=%s",
            self._base_url,
            self._model,
        )

    # ── Sync generate ──────────────────────────────────────────

    def generate(self, prompt: str) -> str:
        """Send a blocking chat-completion request and return the full response."""
        payload = self._build_payload(prompt, stream=False)
        headers = self._build_headers()

        with self._httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
        if not resp.is_success:
            raise ExternalApiError(resp.status_code, resp.text[:500])

        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    # ── Sync streaming ─────────────────────────────────────────

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Yield tokens from the provider's SSE stream synchronously."""
        payload = self._build_payload(prompt, stream=True)
        headers = self._build_headers()

        with self._httpx.Client(timeout=self._timeout) as client:
            with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if not resp.is_success:
                    raise ExternalApiError(resp.status_code, "Stream request failed")
                for line in resp.iter_lines():
                    token = self._parse_sse_line(line)
                    if token:
                        yield token

    # ── Async streaming ────────────────────────────────────────

    async def agenerate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """True async token streaming — no thread overhead."""
        payload = self._build_payload(prompt, stream=True)
        headers = self._build_headers()

        async with self._httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if not resp.is_success:
                    raise ExternalApiError(resp.status_code, "Async stream failed")
                async for line in resp.aiter_lines():
                    token = self._parse_sse_line(line)
                    if token:
                        yield token

    # ── Helpers ────────────────────────────────────────────────

    def _build_payload(self, prompt: str, stream: bool) -> dict:
        return {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
        }

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/apply-agent",  # required by some providers
            "X-Title": "Apply-Agent",
        }

    @staticmethod
    def _parse_sse_line(line: str) -> str:
        """Extract delta content from a single SSE ``data:`` line."""
        if not line.startswith("data:"):
            return ""
        raw = line[len("data:"):].strip()
        if raw == "[DONE]":
            return ""
        try:
            chunk = json.loads(raw)
            delta = chunk["choices"][0].get("delta", {})
            return delta.get("content", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            return ""


# ── Factory ───────────────────────────────────────────────────────────────────


def get_llm_adapter(settings=None) -> LLMAdapter:
    """Return the correct adapter based on ``settings.llm_provider``.

    When ``llm_provider == "external"``, constructs :class:`ExternalApiAdapter`
    from the configured base URL, key, and model.
    Otherwise constructs :class:`QwenAdapter` (loads local LoRA model).

    Parameters
    ----------
    settings:
        A :class:`~config.Settings` instance.  If *None*, imports the
        module-level singleton automatically.
    """
    if settings is None:
        from config import settings as _s  # noqa: PLC0415
        settings = _s

    if settings.is_external_provider:
        if not settings.external_api_key:
            logger.warning(
                "LLM_PROVIDER=external but EXTERNAL_API_KEY is empty. "
                "Requests will likely fail with HTTP 401."
            )
        return ExternalApiAdapter(
            base_url=settings.external_api_base_url,
            api_key=settings.external_api_key,
            model=settings.external_api_model,
            timeout=settings.external_api_timeout,
        )

    return LlamaCppAdapter()



# ── Prompt builder ────────────────────────────────────────────────────────────


def get_system_prompt(scenario: str) -> str:
    """Load the raw system-prompt template for *scenario* from ``prompts/``."""
    prompt_path = Path(__file__).parent / "prompts" / f"{scenario}.md"
    if not prompt_path.is_file():
        logger.warning("Prompt file not found for scenario '%s'; using generic fallback.", scenario)
        return "You are a helpful AI assistant specialised in job applications."
    return prompt_path.read_text(encoding="utf-8").strip()


def build_rag_prompt(
    scenario: str,
    cv_context: Optional[dict] = None,
    job_context: Optional[dict] = None,
    few_shot_examples: Optional[List[dict]] = None,
    example_files: Optional[dict] = None,
) -> str:
    """Compose a full RAG prompt by injecting all context blocks into the template.

    Parameters
    ----------
    scenario:
        One of ``"cv"``, ``"cover_letter"``, ``"job_match"``.
    cv_context:
        Structured candidate profile dict (from :func:`~AI.llm.rag_service.retrieve_cv_context`).
    job_context:
        Structured job dict (from :func:`~AI.llm.rag_service.retrieve_job_context`).
    few_shot_examples:
        List of past accepted job dicts (from :func:`~AI.llm.rag_service.retrieve_few_shot_examples`).
    example_files:
        Dict with keys ``"cv_examples"``, ``"cover_letter_examples"``, ``"cover_letter_instructions"``
        (from :func:`~AI.llm.rag_service.retrieve_example_files`).
    """
    template = get_system_prompt(scenario)

    def _json(obj) -> str:
        if obj is None:
            return "null"
        return json.dumps(obj, ensure_ascii=False, indent=2)

    files = example_files or {}

    replacements = {
        "{cv_context_json}": _json(cv_context),
        "{job_context_json}": _json(job_context),
        "{few_shot_examples_json}": _json(few_shot_examples or []),
        "{cv_examples}": files.get("cv_examples", ""),
        "{cover_letter_examples}": files.get("cover_letter_examples", ""),
        "{cover_letter_instructions}": files.get("cover_letter_instructions", ""),
    }

    prompt = template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    return prompt


def build_prompt(scenario: str, user_query: str) -> str:
    """Legacy compatibility shim.

    Builds a minimal prompt without RAG context — retained so existing
    callers (tests, old routers) do not break.  New code should call
    :func:`build_rag_prompt` directly.
    """
    system = get_system_prompt(scenario)
    return f"{system}\n\nUser: {user_query}"


def get_related_documents() -> List[str]:
    """Deprecated placeholder — returns empty list.

    Use :func:`~AI.llm.rag_service.retrieve_cv_context` and friends instead.
    """
    return []


def _parse_json(raw: str, default_schema: dict | list) -> dict | list:
    """Extract and parse JSON from raw LLM output, with fallbacks."""
    raw = raw.strip()
    
    # Remove markdown fences
    if raw.startswith("```json"):
        raw = raw[len("```json"):].strip()
    elif raw.startswith("```"):
        raw = raw[3:].strip()
    if raw.endswith("```"):
        raw = raw[:-3].strip()
        
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
        
    # Try to find the first JSON-like block
    start_char = "{" if isinstance(default_schema, dict) else "["
    end_char = "}" if isinstance(default_schema, dict) else "]"
    
    start_idx = raw.find(start_char)
    end_idx = raw.rfind(end_char)
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(raw[start_idx:end_idx+1])
        except json.JSONDecodeError:
            pass
            
    # All parsing failed, return default
    logger.debug("JSON parse failed. Raw output: %s", raw)
    return default_schema


def generate_json(llm: LLMAdapter, prompt: str, schema_example: dict | list, max_retries: int = 2) -> dict | list:
    """Generate JSON from the LLM, retrying on parse failure."""
    for attempt in range(max_retries + 1):
        try:
            raw_response = llm.generate(prompt)
            return _parse_json(raw_response, schema_example)
        except Exception as e:
            logger.warning("LLM generation failed on attempt %d: %s", attempt + 1, e)
            if attempt == max_retries:
                return schema_example
    return schema_example

