# System Architecture

## Overview

Apply-Agent backend is built with **FastAPI** (Python) and powered by **SQLAlchemy (Async)** with a **SQLite** database. It leverages **Qwen/Qwen2.5-0.5B-Instruct** for LLM capabilities and uses local inference for data extraction, document generation, and RAG embeddings.

## Job-Match Scenario (Phase 7)

The Job-Match scenario represents the core workflow for evaluating a prospective job offer against the candidate's professional context. It seamlessly integrates rule-based NLP extraction, embedding similarity, LLM text generation, and LaTeX PDF compilation into an asynchronous, robust pipeline.

### Core Architecture Components

- **`ChecklistExtractor` (NLP):** A deterministic regex-based module that parses unstructured job descriptions into structured requirements (skills, education levels, minimum experience).
- **`MatchScorer` (Math/Embeddings):** Evaluates candidate context against the extracted checklist. It calculates 5 isolated scores:
  - `job_match` (20%) - Overall semantic alignment (Cosine Similarity).
  - `skill_match` (30%) - Direct requirement intersection.
  - `education_match` (15%) - Degree hierarchy comparison.
  - `experience_match` (20%) - Year bounds validation.
  - `objective_match` (15%) - Long-term career semantic alignment.
- **`LatexRenderer` (Subprocess):** Wraps `pdflatex` to safely compile raw LaTeX source text into PDFs, implementing security timeouts and dual-pass compilation (for references).
- **`JobMatchService` (Orchestrator):** The primary service facade. Orchestrates fetching data, calling the scorer, storing to DB, and launching the `LatexRenderer` inside FastAPI `BackgroundTasks`.

### REST Endpoints

The Job-Match workflow is exposed through a complete RESTful API under `/jobs`, designed for a polling frontend architecture.

| Endpoint | Method | Description | Returns |
| -------- | ------ | ----------- | ------- |
| `/jobs/evaluate` | POST | Triggers the job evaluation and kicks off PDF generation in the background. | `202 Accepted`, 5-dimension scores |
| `/jobs/{id}/status` | GET | Polls the current state of background PDF compilation (`processing: true/false`). | `200 OK`, PDF URLs & processing flag |
| `/jobs/{id}/download` | GET | Serves the generated PDF file (`cv` or `cover`) or raw LaTeX source code. | `200 OK`, `application/pdf` or JSON |
| `/jobs/{id}/status` | PATCH | Updates the workflow state (`accepted`, `rejected`, `pending`). Rejecting clears active RAG memory. | `200 OK` |
| `/jobs/{id}/latex` | PATCH | Stores user-modified LaTeX strings edited directly in the frontend UI. | `200 OK` |
| `/jobs/{id}/regenerate`| POST | Retriggers background compilation on the newly modified LaTeX source. | `202 Accepted` |

## Data Persistence

- Uses `SQLAlchemy` async sessions (`AsyncSession`).
- SQLite requires explicit `flag_modified` triggers for JSON column mutations (e.g. `dimension_scores`, `extracted_requirements`).
- When querying UUID columns in SQLite via SQLAlchemy, identifiers must be parsed to `uuid.UUID` before the query executes.
