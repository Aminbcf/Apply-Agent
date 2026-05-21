import abc
import json
from pathlib import Path
from typing import List

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


class LLMAdapter(abc.ABC):
    """Abstract interface for LLM models.

    Subclasses must implement :meth:`generate` which receives a full prompt and returns the generated text.
    """

    @abc.abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for the given *prompt*.
        """
        raise NotImplementedError


class QwenAdapter(LLMAdapter):
    """Adapter that loads the fine‑tuned Qwen LoRA model from the repository.

    The model files reside in ``src/backend/AI/llm/final_lora_adapter``.
    ``transformers`` will automatically pick up the safetensors, tokenizer JSON, and chat template.
    """

    def __init__(self) -> None:
        model_dir = Path(__file__).parent / "final_lora_adapter"
        # Load tokenizer and model from the local directory.
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(model_dir, device_map="auto", trust_remote_code=True)
        # Use a text‑generation pipeline for simplicity.
        self.generator = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer, torch_dtype=self.model.dtype)

    def generate(self, prompt: str) -> str:
        # The pipeline returns a list of dicts with 'generated_text'.
        result = self.generator(prompt, max_new_tokens=256, return_full_text=False)[0]
        return result["generated_text"].strip()


def load_prompt(scenario: str) -> str:
    """Load the system prompt for a given scenario from a markdown file.

    The files are expected at ``src/backend/AI/llm/prompts/{scenario}.md``.
    """
    prompt_path = Path(__file__).parent / "prompts" / f"{scenario}.md"
    if not prompt_path.is_file():
        raise FileNotFoundError(f"Prompt file for scenario '{scenario}' not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def get_system_prompt(scenario: str) -> str:
    """Return a system prompt tailored to the given RAG scenario.

    Supported scenarios: ``cv``, ``cover_letter``, ``interview_prep``.
    """
    try:
        return load_prompt(scenario)
    except FileNotFoundError:
        # Fallback to a generic prompt if the file is missing
        return "You are an AI assistant."



def get_related_documents(scenario: str) -> List[str]:
    """Placeholder for retrieving documents relevant to the scenario.

    In a full implementation this would query the SQLite DB for CV entries, cover‑letter examples,
    or interview prep materials. Here we return an empty list to keep the function lightweight.
    """
    return []


def build_prompt(scenario: str, user_query: str) -> str:
    """Compose the full prompt with system message, retrieved context, and user query.
    """
    system = get_system_prompt(scenario)
    docs = get_related_documents(scenario)
    context = "\n".join(docs)
    if context:
        return f"{system}\n\nContext:\n{context}\n\nUser: {user_query}"
    return f"{system}\n\nUser: {user_query}"
