import os
import shutil
import tempfile
import importlib.util
from pathlib import Path

# Load cover_letter_generator module by file path to avoid importing the package
mod_path = Path(__file__).resolve().parent / "cover_letter_generator.py"
spec = importlib.util.spec_from_file_location("cover_letter_generator_local", str(mod_path))
cover_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cover_mod)
generate_cover_letter = cover_mod.generate_cover_letter
build_latex_and_render_pdf = cover_mod.build_latex_and_render_pdf


class MockLLM:
    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt: str, max_tokens: int = None) -> str:
        # capture prompt for assertions and return deterministic text
        self.last_prompt = prompt
        return (
            "Dear Hiring Manager,\n\n"
            "I am excited to apply for the position. My recent work reduced deployment time by 30% [source:cv_1].\n\n"
            "Sincerely,\nJohn Doe"
        )


def test_generate_cover_letter_and_tex(tmp_path):
    job = {"title": "AI Engineer", "company": "Acme", "location": "Remote"}
    skills = {"req_skills": ["LLMs", "RAG"], "pref_skills": ["DevOps"]}
    evidence = [{"id": "cv_1", "summary": "Reduced deployment time by 30%", "metric": "30%", "source_id": "cv_1"}]
    candidate = {"name": "John Doe", "city": "Paris, France", "phone": "(555) 123-4567", "email": "john@example.com"}

    llm = MockLLM()
    out = generate_cover_letter(job, skills, evidence, candidate, llm)
    assert "reduced deployment time" in out["text"].lower()
    # ensure system prompt from Instructions.md was loaded into the LLM prompt
    assert llm.last_prompt is not None
    assert "Retrieval-Augmented Generation" in llm.last_prompt or "RAG" in llm.last_prompt

    out_stem = str(tmp_path / "cover_letter")
    tex_path = build_latex_and_render_pdf(out["text"], candidate, out_stem, execute_pdf=False)
    assert os.path.exists(tex_path)

    # If pdflatex exists, try to render a PDF as a smoke test
    if shutil.which("pdflatex") or shutil.which("xelatex"):
        pdf_path = build_latex_and_render_pdf(out["text"], candidate, out_stem, execute_pdf=True)
        assert pdf_path.endswith(".pdf") and os.path.exists(pdf_path)
