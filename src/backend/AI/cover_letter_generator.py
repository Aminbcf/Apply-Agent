import json
import logging
import os
import shlex
import subprocess  # nosec B404
import shutil
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def _escape_latex(text: str) -> str:
    replacements = {
        "\\": r"\\textbackslash{}",
        "%": r"\\%",
        "$": r"\\$",
        "#": r"\\#",
        "_": r"\\_",
        "{": r"\\{",
        "}": r"\\}",
        "~": r"\\textasciitilde{}",
        "^": r"\\^{}",
        "&": r"\\&",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def generate_cover_letter(job: Dict[str, Any], skills: Dict[str, List[str]], evidence: List[Dict[str, Any]], candidate: Dict[str, Any], llm, omit_address: bool = True, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a prompt from the provided structured inputs and call the provided LLM-like object.

    Parameters
    - job: dict with keys like `title`, `company`, `location`.
    - skills: dict with `req_skills` and `pref_skills` lists.
    - evidence: list of evidence dicts (id, summary, metric, source_id).
    - candidate: dict with `name`, `city`, `phone`, `email`.
    - llm: object with a `generate(prompt: str, max_tokens: int = None) -> str` method.
    - omit_address: when True omit candidate address for online forms.
    - constraints: optional dict e.g. {"max_paragraphs":3}

    Returns dict: {"text": str, "used_evidence": [ids], "prompt": str}
    """
    constraints = constraints or {}
    max_paragraphs = constraints.get("max_paragraphs", 3)

    # Load system prompt from the RAG instructions file (if available)
    system_prompt = ""
    try:
        base = os.path.dirname(__file__)
        instr_path = os.path.join(base, "Cover-letter-Examples", "Instructions.md")
        if os.path.exists(instr_path):
            with open(instr_path, "r", encoding="utf8") as fh:
                system_prompt = fh.read()
    except Exception:
        logger.exception("Failed to load cover letter instructions")
        system_prompt = ""

    # Build compact JSON context to inject into the prompt
    ctx = {
        "job": job,
        "skills": skills,
        "evidence": evidence[:2],
        "candidate": {k: candidate.get(k) for k in ("name", "city", "phone", "email")},
        "constraints": {"max_paragraphs": max_paragraphs},
    }

    # Compose final prompt: include system instructions then the JSON context
    prompt_parts = []
    if system_prompt:
        prompt_parts.append("SYSTEM_INSTRUCTIONS:\n" + system_prompt)
    prompt_parts.append("You are an expert Career Coach and Cover Letter Writer.\nUse ONLY the JSON context below to write a single-page, professional cover letter.\nInclude inline citations for any factual claim using [source:SOURCE_ID].\n\nCONTEXT_JSON:\n")
    prompt_parts.append(json.dumps(ctx, ensure_ascii=False, indent=2))
    prompt_parts.append("\n\nGenerate the cover letter now.")
    prompt = "\n\n".join(prompt_parts)

    # Call the LLM (assumed to be synchronous)
    # The llm object is expected to implement `generate(prompt, max_tokens=None)`
    if not hasattr(llm, "generate"):
        raise ValueError("llm must provide a generate(prompt, max_tokens=None) method")

    raw = llm.generate(prompt, max_tokens=4096)

    # Basic post-processing: ensure no [UNVERIFIED] markers remain
    text = raw.replace("[UNVERIFIED]", "")

    used = [e.get("id") for e in evidence[:2]]

    return {"text": text.strip(), "used_evidence": used, "prompt": prompt}


def build_latex_and_render_pdf(cover_text: str, candidate: Dict[str, Any], output_stem: str, execute_pdf: bool = True) -> str:
    """
    Create a simple LaTeX document containing the cover letter and optionally run pdflatex/xelatex to produce a PDF.

    - cover_text: full letter plain text (may contain citation markers like [source:...])
    - candidate: dict with name, city, phone, email
    - output_stem: path without extension where .tex/.pdf will be written (e.g. './out/letter')
    - execute_pdf: if True, attempt to run a LaTeX engine to produce PDF

    Returns path to the generated PDF when executed, otherwise to the .tex file.
    """
    out_dir = os.path.dirname(output_stem) or "."
    os.makedirs(out_dir, exist_ok=True)
    tex_path = output_stem + ".tex"

    header_lines = []
    if candidate.get("name"):
        header_lines.append(candidate.get("name"))
    if candidate.get("city") or candidate.get("phone") or candidate.get("email"):
        contact = " | ".join(filter(None, [candidate.get("city"), candidate.get("phone"), candidate.get("email")]))
        header_lines.append(contact)

    header = "\\\\\n".join(header_lines)

    safe_body = _escape_latex(cover_text)

    tex = (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[margin=1in]{geometry}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage{lmodern}\n"
        "\\begin{document}\n"
        "\\thispagestyle{empty}\n"
        f"{_escape_latex(header)}\\\\\n\\vspace{{0.5cm}}\n"
        "\\noindent\n"
        f"{safe_body}\n"
        "\\end{document}\n"
    )

    with open(tex_path, "w", encoding="utf8") as f:
        f.write(tex)

    if not execute_pdf:
        return tex_path

    # Try pdflatex then xelatex
    engines = ["pdflatex", "xelatex"]
    cmd = None
    for eng in engines:
        if shutil.which(eng):
            cmd = eng
            break

    if cmd is None:
        raise RuntimeError("No LaTeX engine found (pdflatex or xelatex). Install TeX or run with execute_pdf=False")

    # Run the engine twice to resolve layout
    for _ in range(2):
        completed = subprocess.run([cmd, "-interaction=nonstopmode", "-output-directory", out_dir, tex_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # nosec: cmd is hardcoded to pdflatex|xelatex, tex_path is safe
        if completed.returncode != 0:
            raise RuntimeError(f"LaTeX failed (engine={cmd}): {completed.stderr.decode(errors='replace')}" )

    pdf_path = output_stem + ".pdf"
    if os.path.exists(pdf_path):
        return pdf_path
    return tex_path
