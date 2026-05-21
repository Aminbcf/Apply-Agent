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
import subprocess
import uuid
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

DocType = Literal["cv", "cover"]


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
