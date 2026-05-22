"""LaTeX compilation utility for the Apply-Agent job-match scenario.

Writes a LaTeX source string to a temporary .tex file and runs ``pdflatex``
twice (second pass resolves cross-references) to produce a PDF.

Usage::

    from utils.latex_renderer import LatexRenderer, LatexRenderError
    from config import settings

    renderer = LatexRenderer(settings.latex_output_dir)
    pdf_path = renderer.render(latex_source, job_id="abc123", doc_type="cv")
"""

from __future__ import annotations

import logging
import re
import subprocess  # nosec B404
import uuid
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

DocType = Literal["cv", "cover"]

TEMPLATE_DIR = Path(__file__).parent / "latex_templates"


class LatexRenderError(RuntimeError):
    """Raised when ``pdflatex`` fails or times out."""


class LatexRenderer:
    """Compile a LaTeX source string into a PDF file.

    Parameters
    ----------
    output_dir:
        Root directory where .tex and .pdf files are stored.
        Created automatically if it does not exist.
    timeout:
        Maximum seconds to wait for a single ``pdflatex`` run.
    """

    def __init__(self, output_dir: Path, timeout: int = 60) -> None:
        self.output_dir = Path(output_dir)
        self.timeout = timeout
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ────────────────────────────────────────────

    def render(self, latex_source: str, job_id: str, doc_type: DocType) -> Path:
        """Write *latex_source* to disk and compile it to a PDF.

        Parameters
        ----------
        latex_source:
            Full LaTeX document string (``\\documentclass`` … ``\\end{document}``).
        job_id:
            UUID string of the related :class:`JobApplication` record.
            Used to derive a stable, unique filename.
        doc_type:
            Either ``"cv"`` or ``"cover"`` – determines the filename suffix.

        Returns
        -------
        Path
            Absolute path to the generated PDF file.

        Raises
        ------
        LatexRenderError
            If ``pdflatex`` exits with a non-zero return code or times out.
        """
        job_dir = self._job_dir(job_id)
        tex_path = job_dir / f"{doc_type}.tex"
        pdf_path = job_dir / f"{doc_type}.pdf"

        # Write source
        tex_path.write_text(latex_source, encoding="utf-8")
        logger.info("LaTeX source written: %s", tex_path)

        # Compile twice so cross-references resolve
        for pass_num in (1, 2):
            logger.debug("pdflatex pass %d for job_id=%s doc_type=%s", pass_num, job_id, doc_type)
            self._run_pdflatex(tex_path, job_dir)

        if not pdf_path.exists():
            raise LatexRenderError(
                f"pdflatex succeeded but PDF not found at expected path: {pdf_path}"
            )

        logger.info("PDF generated: %s", pdf_path)
        return pdf_path

    def render_from_markdown(
        self,
        markdown_text: str,
        template_type: DocType,
        job_id: str,
        user_info: dict | None = None,
    ) -> Path:
        """Convert markdown text to LaTeX via a template and compile to PDF.

        Parameters
        ----------
        markdown_text:
            User-edited document in markdown format.
        template_type:
            ``"cv"`` or ``"cover"`` — determines which LaTeX template to use.
        job_id:
            UUID string for the job application.
        user_info:
            Optional dict with keys ``name``, ``email``, ``phone``, ``location``.

        Returns
        -------
        Path
            Absolute path to the generated PDF file.
        """
        user_info = user_info or {}

        # Load the template
        template_name = "cv_template.tex" if template_type == "cv" else "cover_letter_template.tex"
        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            raise LatexRenderError(f"Template not found: {template_path}")

        template = template_path.read_text(encoding="utf-8")

        # Convert markdown to LaTeX body
        latex_body = self._markdown_to_latex(markdown_text)

        # Inject placeholders
        latex_source = template.replace("{{CONTENT}}", latex_body)
        latex_source = latex_source.replace("{{CANDIDATE_NAME}}", _escape_latex(user_info.get("name", "")))
        latex_source = latex_source.replace("{{CANDIDATE_EMAIL}}", _escape_latex(user_info.get("email", "")))
        latex_source = latex_source.replace("{{CANDIDATE_PHONE}}", _escape_latex(user_info.get("phone", "")))
        latex_source = latex_source.replace("{{CANDIDATE_LOCATION}}", _escape_latex(user_info.get("location", "")))

        return self.render(latex_source, job_id, template_type)

    # ── Internal helpers ──────────────────────────────────────

    def _job_dir(self, job_id: str) -> Path:
        """Return (and create) the per-job subdirectory."""
        job_dir = self.output_dir / str(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def _run_pdflatex(self, tex_path: Path, output_dir: Path) -> None:
        """Execute ``pdflatex`` as a subprocess.

        Parameters
        ----------
        tex_path:
            Absolute path to the ``.tex`` source file.
        output_dir:
            Directory where auxiliary and output files are written.

        Raises
        ------
        LatexRenderError
            On non-zero exit code or timeout.
        """
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",   # never pause for user input
            "-halt-on-error",             # abort on first error
            f"-output-directory={output_dir}",
            str(tex_path),
        ]

        try:
            result = subprocess.run(  # nosec B603
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise LatexRenderError(
                f"pdflatex timed out after {self.timeout}s for {tex_path}"
            ) from exc
        except FileNotFoundError as exc:
            raise LatexRenderError(
                "pdflatex executable not found. "
                "Please install a LaTeX distribution (e.g. MiKTeX or TeX Live)."
            ) from exc

        if result.returncode != 0:
            # Include the last 40 lines of the log to help diagnose failures
            log_tail = "\n".join((result.stdout or "").splitlines()[-40:])
            raise LatexRenderError(
                f"pdflatex exited with code {result.returncode}.\n"
                f"--- log tail ---\n{log_tail}"
            )

    @staticmethod
    def _process_heading(stripped: str, result: list) -> bool:
        if stripped.startswith("### "):
            result.append(f"\\subsection*{{{_escape_latex(stripped[4:])}}}")
            return True
        if stripped.startswith("## "):
            result.append(f"\\section*{{{_escape_latex(stripped[3:])}}}")
            return True
        if stripped.startswith("# "):
            result.append(f"\\section*{{{_escape_latex(stripped[2:])}}}")
            return True
        return False

    @staticmethod
    def _markdown_to_latex(md_text: str) -> str:
        """Convert basic markdown to LaTeX body content.

        Supports: headings (## → \\section), bold, italic, bullet lists,
        numbered lists, and paragraphs.
        """
        ENUMERATE_PATTERN = r"^\d+\.\s"
        lines = md_text.split("\n")
        result = []
        in_itemize = False
        in_enumerate = False

        for line in lines:
            stripped = line.strip()

            # Close open lists if line is not a list item
            if not stripped.startswith(("- ", "* ")) and in_itemize:
                result.append("\\end{itemize}")
                in_itemize = False
            if not re.match(ENUMERATE_PATTERN, stripped) and in_enumerate:
                result.append("\\end{enumerate}")
                in_enumerate = False

            if LatexRenderer._process_heading(stripped, result):
                continue
                
            # Bullet lists
            if stripped.startswith(("- ", "* ")):
                if not in_itemize:
                    result.append("\\begin{itemize}[nosep]")
                    in_itemize = True
                item_text = _apply_inline_formatting(_escape_latex(stripped[2:]))
                result.append(f"  \\item {item_text}")
            # Numbered lists
            elif re.match(ENUMERATE_PATTERN, stripped):
                if not in_enumerate:
                    result.append("\\begin{enumerate}[nosep]")
                    in_enumerate = True
                item_text = _apply_inline_formatting(_escape_latex(re.sub(ENUMERATE_PATTERN, "", stripped)))
                result.append(f"  \\item {item_text}")
            # Empty line = paragraph break
            elif not stripped:
                result.append("")
            # Normal paragraph
            else:
                result.append(_apply_inline_formatting(_escape_latex(stripped)))

        # Close any open lists
        if in_itemize:
            result.append("\\end{itemize}")
        if in_enumerate:
            result.append("\\end{enumerate}")

        return "\n".join(result)


def _escape_latex(text: str) -> str:
    """Escape LaTeX special characters in plain text."""
    replacements = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\^{}",
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    return text


def _apply_inline_formatting(text: str) -> str:
    """Convert markdown inline formatting to LaTeX.

    Handles **bold** → \\textbf{} and *italic* → \\textit{}.
    """
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"__(.+?)__", r"\\textbf{\1}", text)
    # Italic: *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"\\textit{\1}", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\\textit{\1}", text)
    return text

