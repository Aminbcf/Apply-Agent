# AGENTS Guidance Document

## Purpose

This file provides **clear guidance for the language model (LLM) agents** that operate within the Apply‑Agent project. It defines the entry points, references to essential documentation, and the workflow for using persistent session memory.

## Entry Point for LLM Agents

- The **primary location** for LLM‑driven operations is the project root directory (`<project_root>`).
- Agents should **always start by loading** the following markdown resources:
  1. **`docs/rules.md`** – Contains the comprehensive coding guidelines, architecture principles, and the **Session Memory & Persistent Logs** section.
  2. **`docs/skills/coding-standards/SKILL.md`** – Enforces code quality, maintainability, formatting, and a strict test coverage minimum (>= 80%).
  3. **`docs/memory.md`** – (if present) aggregates important insights across sessions. Agents must read this file at the beginning of each session to recall shared standards and reusable patterns.
  4. **`logs/`** directory – Holds per‑session logs (`session_<timestamp>.md`). Agents may consult recent logs for context when resuming work.

## How Agents Should Use the Documentation

1. **Load Rules**
   ```python
   with open('docs/rules.md', 'r', encoding='utf-8') as f:
       RULES = f.read()
   ```
   - Parse the **"Session Memory & Persistent Logs"** subsection to understand how to create, update, and finalize session logs.
2. **Persist Knowledge**
   - After completing a logical step, append relevant information to the active session log (`logs/session_<id>.md`).
   - When the session ends, call the helper `finalize_session('docs/memory.md')` (implemented by the project) to merge important entries into `memory.md`.
3. **Reference Guidelines**
   - Before generating any code, consult the **Review Checklist** in `docs/rules.md` to ensure compliance with style, testing, security, and logging standards.

## Session Lifecycle Helpers (provided by the project)

- `init_session_log()`: Creates a new session markdown file in `logs/` and writes the start timestamp and a unique session ID.
- `finalize_session(memory_path: str)`: Analyzes the session log, extracts entries marked as **important**, and appends them to the specified `memory.md` file, then closes the session.

> **NOTE**: Agents must **never overwrite** existing logs or memory entries without explicit intent. Use append‑only operations unless a cleanup is required.

## Checklist for LLM Agents

| ✅ Item | Description |
|--------|-------------|
| **Load Rules** | Read `docs/rules.md` at session start. |
| **Maintain Log** | Record every action in `logs/session_<id>.md`. |
| **Persist Memory** | Merge critical insights into `docs/memory.md` via `finalize_session`. |
| **Follow Guidelines** | Verify output against the checklist in `docs/rules.md`. |

---

*This file is intentionally lightweight so that any LLM agent can quickly locate the core documentation and follow the prescribed workflow.*
