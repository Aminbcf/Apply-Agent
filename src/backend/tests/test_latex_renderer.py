"""Unit tests for LatexRenderer (Phase 7).

All subprocess calls are mocked so pdflatex is never actually invoked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from utils.latex_renderer import LatexRenderError, LatexRenderer


SAMPLE_LATEX = r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
"""


@pytest.fixture()
def tmp_renderer(tmp_path: Path) -> LatexRenderer:
    """LatexRenderer pointing at a temporary directory."""
    return LatexRenderer(output_dir=tmp_path / "latex_out", timeout=10)


# ── Successful render ──────────────────────────────────────────

class TestRenderSuccess:
    def test_tex_file_written(self, tmp_renderer: LatexRenderer) -> None:
        """Verify the .tex source is written to disk before pdflatex is called."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Manually create a fake PDF so the existence check passes
            job_id = "test-job-1"
            fake_pdf = tmp_renderer._job_dir(job_id) / "cv.pdf"
            fake_pdf.parent.mkdir(parents=True, exist_ok=True)
            fake_pdf.write_bytes(b"%PDF-1.4")

            tmp_renderer.render(SAMPLE_LATEX, job_id=job_id, doc_type="cv")

            tex_file = tmp_renderer._job_dir(job_id) / "cv.tex"
            assert tex_file.exists()
            assert "Hello World" in tex_file.read_text()

    def test_returns_pdf_path(self, tmp_renderer: LatexRenderer) -> None:
        """render() must return the absolute path to the compiled PDF."""
        job_id = "test-job-2"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Pre-create the PDF so existence check passes
            fake_pdf = tmp_renderer._job_dir(job_id) / "cv.pdf"
            fake_pdf.parent.mkdir(parents=True, exist_ok=True)
            fake_pdf.write_bytes(b"%PDF-1.4")

            result = tmp_renderer.render(SAMPLE_LATEX, job_id=job_id, doc_type="cv")

        assert result == fake_pdf
        assert result.suffix == ".pdf"

    def test_pdflatex_called_twice(self, tmp_renderer: LatexRenderer) -> None:
        """render() must invoke pdflatex exactly twice (two-pass compile)."""
        job_id = "test-job-3"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            fake_pdf = tmp_renderer._job_dir(job_id) / "cover.pdf"
            fake_pdf.parent.mkdir(parents=True, exist_ok=True)
            fake_pdf.write_bytes(b"%PDF-1.4")

            tmp_renderer.render(SAMPLE_LATEX, job_id=job_id, doc_type="cover")

        assert mock_run.call_count == 2

    def test_output_dir_created_automatically(self, tmp_path: Path) -> None:
        """LatexRenderer must create the output directory on init."""
        new_dir = tmp_path / "brand_new_dir"
        assert not new_dir.exists()
        LatexRenderer(output_dir=new_dir)
        assert new_dir.exists()


# ── Failure cases ──────────────────────────────────────────────

class TestRenderFailure:
    def test_nonzero_exit_raises(self, tmp_renderer: LatexRenderer) -> None:
        """Non-zero pdflatex exit code must raise LatexRenderError."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="! Undefined control sequence.\n",
                stderr="",
            )
            with pytest.raises(LatexRenderError, match="exited with code 1"):
                tmp_renderer.render(SAMPLE_LATEX, job_id="fail-job", doc_type="cv")

    def test_timeout_raises(self, tmp_renderer: LatexRenderer) -> None:
        """subprocess.TimeoutExpired must be re-raised as LatexRenderError."""
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="pdflatex", timeout=10)):
            with pytest.raises(LatexRenderError, match="timed out"):
                tmp_renderer.render(SAMPLE_LATEX, job_id="timeout-job", doc_type="cv")

    def test_missing_pdflatex_raises(self, tmp_renderer: LatexRenderer) -> None:
        """FileNotFoundError (pdflatex not installed) → LatexRenderError."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(LatexRenderError, match="not found"):
                tmp_renderer.render(SAMPLE_LATEX, job_id="no-bin-job", doc_type="cv")

    def test_missing_pdf_after_success_raises(self, tmp_renderer: LatexRenderer) -> None:
        """If pdflatex succeeds but PDF is absent, raise LatexRenderError."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            # Do NOT create the fake PDF file
            with pytest.raises(LatexRenderError, match="PDF not found"):
                tmp_renderer.render(SAMPLE_LATEX, job_id="ghost-pdf", doc_type="cv")


# ── Per-job directory isolation ────────────────────────────────

class TestJobDirIsolation:
    def test_separate_jobs_get_separate_dirs(self, tmp_renderer: LatexRenderer) -> None:
        dir_a = tmp_renderer._job_dir("job-a")
        dir_b = tmp_renderer._job_dir("job-b")
        assert dir_a != dir_b
        assert dir_a.exists()
        assert dir_b.exists()
