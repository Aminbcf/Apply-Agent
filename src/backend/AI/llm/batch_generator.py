"""batch_generator.py

Runs the multi-batch generation pipeline for CV and cover letters.
"""

import asyncio
import logging

from AI.llm.llm_interface import build_rag_prompt, generate_json, LLMAdapter, ExternalApiAdapter
from AI.llm.cover_letter_assembler import assemble_cover_letter

logger = logging.getLogger(__name__)

def _can_run_parallel(is_external: bool) -> bool:
    if is_external:
        return True
    # Local models (LlamaCppAdapter) are forced sequential to prevent 
    # threading timeouts and memory/lock contention.
    return False


CV_SCHEMAS = {
    "header": {"name": "", "email": "", "phone": "", "linkedin": "", "github": "", "location": "", "title": ""},
    "summary": {"summary": ""},
    "experience": [{"company": "", "role": "", "location": "", "dates": "", "bullets": [""]}],
    "education": [{"institution": "", "degree": "", "field": "", "dates": "", "gpa": ""}],
    "skills": {"languages": [], "frameworks": [], "tools": [], "other": []},
    "projects": [{"name": "", "tech": "", "dates": "", "bullets": [""]}]
}

CL_SCHEMAS = {
    "hook": {"greeting": "", "hook": ""},
    "experience": {"experience_paragraph": ""},
    "value": {"value_proposition": ""},
    "closing": {"closing": ""}
}

_SECTION_BANNED_PHRASES = (
    "your experience paragraph here",
    "your value proposition paragraph here",
    "references",
    "références",
    "example json",
    "output schema",
    "instructions:",
    "hard guardrails",
)


def _chunk_text(text: str) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    if paragraphs:
        return [f"{paragraph}\n\n" for paragraph in paragraphs[:-1]] + [paragraphs[-1]]
    return [text]


async def _generate_section(llm: LLMAdapter, scenario: str, cv_ctx: dict, job_ctx: dict, few_shot: list, example_files: dict, schema: dict):
    prompt = build_rag_prompt(scenario, cv_ctx, job_ctx, few_shot, example_files)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, generate_json, llm, prompt, schema, 2)
    return _sanitize_section_result(result, schema)


def _sanitize_section_result(result, schema: dict):
    if not isinstance(result, dict):
        return schema

    cleaned = {}
    for key, default_value in schema.items():
        value = result.get(key, default_value)
        if isinstance(value, str):
            text = value.strip()
            lower_text = text.lower()
            if not text or any(phrase in lower_text for phrase in _SECTION_BANNED_PHRASES):
                cleaned[key] = ""
            else:
                cleaned[key] = text
        else:
            cleaned[key] = value
    return cleaned

async def generate_cv_sections(llm: LLMAdapter, cv_ctx: dict, job_ctx: dict, few_shot: list, example_files: dict):
    """
    Yields ("start", section_name), ("done", section_name), and finally ("final", sections_dict).
    """
    sections = {}
    batches = ["header", "summary", "experience", "education", "skills", "projects"]
    is_external = isinstance(llm, ExternalApiAdapter)
    run_parallel = _can_run_parallel(is_external)
    
    async def process_batch(section_name):
        scenario = f"cv_{section_name}"
        prompt = build_rag_prompt(scenario, cv_ctx, job_ctx, few_shot, example_files)
        schema = CV_SCHEMAS[section_name]
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, generate_json, llm, prompt, schema, 2)
        return section_name, result
        
    if run_parallel:
        # Run in parallel to save time
        for batch in batches:
            yield "start", batch
            
        tasks = [asyncio.create_task(process_batch(b)) for b in batches]
        for completed_task in asyncio.as_completed(tasks):
            section_name, result = await completed_task
            sections[section_name] = result
            yield "done", section_name
    else:
        # Sequential for local GPU to avoid memory issues
        for batch in batches:
            yield "start", batch
            section_name, result = await process_batch(batch)
            sections[section_name] = result
            yield "done", batch
            
    yield "final", sections


async def generate_cover_letter_stream(llm: LLMAdapter, cv_ctx: dict, job_ctx: dict, few_shot: list, example_files: dict):
    """
    Yields ("start", "cover_letter"), then ("token", text) as it streams,
    and finally ("final", full_text).
    """
    yield "start", "cover_letter"
    full_text = ""
    try:
        sections = {}
        for section_name in ["hook", "experience", "value", "closing"]:
            yield "start", section_name
            sections[section_name] = await _generate_section(
                llm,
                f"cl_{section_name}",
                cv_ctx,
                job_ctx,
                few_shot,
                example_files,
                CL_SCHEMAS[section_name],
            )
            yield "done", section_name

        full_text = assemble_cover_letter(sections)
        for chunk in _chunk_text(full_text):
            yield "token", chunk

    except Exception as exc:
        logger.exception("Cover letter streaming failed")
        yield "error", str(exc)

    yield "done", "cover_letter"
    yield "final", full_text
