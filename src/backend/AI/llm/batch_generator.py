"""batch_generator.py

Runs the multi-batch generation pipeline for CV and cover letters.
"""

import asyncio
from AI.llm.llm_interface import build_rag_prompt, generate_json, LLMAdapter, ExternalApiAdapter

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
    prompt = build_rag_prompt("cover_letter", cv_ctx, job_ctx, few_shot, example_files)
    
    full_text = ""
    is_external = isinstance(llm, ExternalApiAdapter)
    
    try:
        if is_external:
            async for chunk in llm.agenerate_stream(prompt):
                full_text += chunk
                yield "token", chunk
        else:
            # We must run synchronous stream generation in a thread
            loop = asyncio.get_event_loop()
            queue: asyncio.Queue[str | None] = asyncio.Queue()

            def _run():
                try:
                    for chunk in llm.generate_stream(prompt):
                        loop.call_soon_threadsafe(queue.put_nowait, chunk)
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, None)

            # Fire and forget thread
            import threading
            threading.Thread(target=_run, daemon=True).start()

            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                full_text += chunk
                yield "token", chunk
                
    except Exception as exc:
        logger.exception("Cover letter streaming failed")
        yield "error", str(exc)

    yield "done", "cover_letter"
    yield "final", full_text
