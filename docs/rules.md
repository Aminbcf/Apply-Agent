# Coding Guidelines for AI Agents

*Version: 1.0 – Updated 2026-05-19*

These rules are designed to help **AI agents** write code that is **correct, high‑quality, reliable, and maintainable**. They synthesize best‑practice recommendations from industry sources and the broader AI‑agent community.

---

## 1. Scope & Architecture

- **Single‑Responsibility** – Each agent should have **one clear purpose** (e.g., generate a React component, update a configuration file). Avoid “god‑agents” that try to do everything. [¹]
- **Modular Composition** – Build pipelines of *micro‑agents* that hand‑off work via well‑defined contracts (JSON schema, Pydantic models). [¹][²]
- **Deterministic Core** – Use traditional code for deterministic tasks (file I/O, calculations, database writes). Reserve LLM reasoning for natural‑language‑heavy steps only. [²][⁴]

---

## 2. Communication Contracts

- **Strict Schemas** – Define input and output schemas for every agent. Use **JSON Schema** or **Pydantic** models and validate them at runtime. [⁸]
- **No Free‑Form Text** – Never rely on raw, unstructured text for inter‑agent communication; always parse into structured data. [⁸]

---

## 3. Code Quality & Style

- **Linting & Formatting** – Enforce a consistent style with tools like **ESLint**, **Prettier**, **flake8**, or **Black**. Include linting in CI. [⁹]
- **Naming Conventions** – Use descriptive, lower‑camelCase for functions, PascalCase for classes, and clear variable names.
- **Self‑Documenting Code** – Write expressive code; add **docstrings** and **inline comments** only when the intent isn’t obvious.
- **DRY & SRP** – Avoid duplicated logic; extract reusable helpers into shared libraries.

---

## 4. Testing & Verification

- **Unit Tests** – Each generated function must have at least one unit test covering happy‑path and edge cases. Aim for ≥80 % coverage. [¹][¹³]
- **Integration Tests** – Validate the end‑to‑end flow where the agent’s output is consumed by another component.
- **Automated CI** – Run the full test suite on every push; block merges on failures.
- **Human‑in‑the‑Loop Review** – Treat AI‑generated code as a **pull request** that requires human review before merging. [¹¹]

---

## 5. Error Handling & Resilience

- **Explicit Exceptions** – Raise typed exceptions for predictable errors; never swallow stack traces.
- **Retries & Back‑off** – For external API calls, implement exponential back‑off and circuit‑breaker patterns. [¹⁰]
- **Graceful Degradation** – If an agent fails, fallback to a safe default or surface a clear error to the user.

---

## 6. Observability & Logging

- **Structured Logs** – Emit JSON‑structured logs that include timestamps, agent ID, decision reason, and tool usage. [¹³]
- **Tracing** – Correlate logs across agents with a unique request ID to trace end‑to‑end execution.

---

## 7. Security & Sanitization

- **Input Validation** – Sanitize all external inputs, especially when generating code that will be executed. [⁹]
- **Avoid Code Injection** – Never concatenate raw user strings into exec/eval calls without strict validation.

---

## 8. Dependency Management

- **Pin Versions** – Use lockfiles (`package-lock.json`, `requirements.txt`) and audit dependencies regularly.
- **Minimal Surface** – Only include libraries the agent truly needs; prefer standard‑library solutions when feasible.

---

## 9. Documentation & Knowledge Sharing

- **README Updates** – Whenever an agent adds or modifies functionality, update the project README with usage examples.
- **Change Log** – Record every semantic version bump with a concise description of what changed.
- **Skill Files** – Store recurring patterns (e.g., preferred logging format, error‑handling template) in markdown **skill** files that agents can read before coding. [⁵][⁶]

---

## 10. Continuous Integration & Deployment

- **Static Analysis** – Run linters, type checkers, and security scanners in CI.
- **Automated Release** – Tag releases only after all checks pass and a human reviewer signs off.

---

## 11. Review Checklist (for human reviewers)

| ✅ Item | Description |
|--------|-------------|
| **Scope** | Agent does one thing; no hidden responsibilities. |
| **Schema** | Input/output conform to defined JSON/Pydantic schema. |
| **Tests** | Unit & integration tests present and passing. |
| **Lint** | Code passes linting and formatting checks. |
| **Logs** | Structured logs emitted for key actions. |
| **Security** | No raw exec/eval, inputs sanitized. |
| **Docs** | README/CHANGELOG updated if needed. |

## Sensitive Information & Secret Management

- **Never embed absolute host paths or device‑specific information** in source files, markdown, or logs. Use placeholders like `<project_root>` or environment variables.
- **Secrets in `.env`** – Store API keys, passwords, and other credentials in a `.env` file. Add `.env` to `.gitignore` and provide an `.env.example` with placeholder keys.
- **Access via environment variables** – Use a loader (e.g., `python-dotenv` or `dotenv` for Node) to read secrets at runtime. Do not hard‑code them.
- **Agent responsibility** – Before generating code, agents must check that no secret or host‑specific data is written directly; replace with appropriate placeholders or environment variable references.
- **Review checklist addition** – Add a checklist item:
  | **Secrets** | Ensure no secrets or host‑specific data are hard‑coded; use `.env` and placeholders. |

## Backend Unit Test Use Cases

- **Fast, deterministic tests** – Avoid invoking external LLMs, embeddings, or network services. Use mocks/stubs for any AI‑model calls.
- **Mock LLM/Embedding APIs** – Provide lightweight fixtures that return static responses (e.g., dummy JSON, short strings) so unit tests run in milliseconds.
- **Database fixtures** – Use in‑memory SQLite or temporary databases; clean up after each test to keep isolation.
- **Business‑logic scenarios** – Test core functions such as request routing, data validation, session‑log handling, and memory merging.
- **Error‑handling paths** – Simulate failures of external services (timeouts, API errors) to verify graceful degradation.
- **Boundary cases** – Verify handling of empty inputs, large payloads, and special characters without triggering heavy processing.
- **Coverage goals** – Aim for >=80 % coverage of backend modules while keeping test runtime <5 seconds.

---

## References

1. **Modular Agent Design** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGlIMW_owSDOcRzBfxK0Ma65Pseuyf3QdxJkkl8LD8r9BsBnw2fFsgILyhy_yy3Lict0tZs5wrdFiiCtNx5Hw0huxh-q-qoCMR8yU9yhc1KxPAGHGvjS0-1LteWitee5fZdu82INNOn-jltpTx-1Z7e15ayI4mr
2. **Multi‑Agent Micro‑services** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFclsMEjRhYGR_N1g7daEegDTiFGN0NpaSuAsPLI64eyTM3E3SC4Lm75VCTaAn3Hg-6PY9XUeKwM4SF2cGp1AlZ55eOkKjW8uKxIC6Wsm6297JUsKPWGnUx0mH-7pWuZ-9uqMY0iym4Y5rm5yFu61BRJAYcx8FHNIxJb-qXi19Cl5pa2KCL-j-gMNg92MwZwr-h3Twflqs05WIUroCc
3. **Human‑in‑the‑Loop** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFknxfM3-ljPhLuUzi7ow_UeaHY49IyF7oXHyHnrygz3soQRvqsvvRO071gG7mUHcdkv9t0AyH32i5O8HoGYqo332rE7MFLnQjGFg8x5sRka6V8l5WPsrv5t94IOk6jHg6UVOOz0j8kyuFH_plDdNU6zxn9T6VH-4kr_g8ZqAZJt1o=
4. **Deterministic vs LLM** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFK3GZGz4K0bwyx3YSKKYseZ0o8yPik_IobN68D_ivVa9hRe5B1srz6GFOpW9lA8xIK5yA7J8kOBEV2DTOvamvjWocfImExMNgfzelFf8gQKe3g3SmT4wxoVQnbQmZVlevb997aeR_A7g2jR09jyU2p1Ys97R7Fdtj1La6Q1kGzOrGlMq80nR8=
5. **Skill Files & Templates** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFf1Czsn_ucbWdDOdXb7PH8UlMvZWWoeAX4u3Ml53hslj1-HP3axyymU5vcX36Ssd_jsRJQDUxAZkHhJO2O44pgYzhpJPjaaYJtk3GpBwy1lfVOT5Rcr5Wmz2CyjIKH0E8jIEcbXapVp-Kd821-pjFRrEYSWnokObaiND4eklNlaHykJlbyvdyY_sk7nOr8EKcZvtG9bA==
6. **Agent Coding Guidelines** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF1u_el7Mz1OlAKhMm-KwOPRze6FKCS2jHzlh0-pNZ849TdmPrxZ7gQEHQWNJkbHF3rzljJB95i8iBsAqg-c2u4xnAOH2xVwBJJWU_NZ3RE7enp-8W1dzNLDdmTgArUS3AhgvIZnNvoZnUPbmMRZtuBegVDJLUBsKqtkWmMSqeeM1EAWgej1sTQz20=
7. **Clean Code Principles** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGVUnbN0-mWEcFzpI5aOVDIaZElp-qp6hyd2sEgdq2thCo_7rnkfFjMyagJTUQDPUl7Iwt9nc7lYkfSoL-VlDEqcHgNg8DHnOOr9Wngma9lV4QZSASRXtpeiOi9mutIUyGGM_g6BtpNiffjy7wL4vOx4eAncaZ_-UAAm6k5XuNR
8. **Structured Output Formats** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH6humNS2iU8yGebNIiDqJlgqNj9ToSPuNhhI-fyGIktxMaPaazBy7LYgBxsNsBYe_A_j5n-g8wpaj34xW9U-SEEtJSwbi1rW1vJlLYjGX7N4uQfaBvoj64l1eUux-Soi712uFlbuBUQKFfKbHRnIxrDFXmztYxCAqAOio=
9. **Lint & Code Style** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGVUnbN0-mWEcFzpI5aOVDIaZElp-qp6hyd2sEgdq2thCo_7rnkfFjMyagJTUQDPUl7Iwt9nc7lYkfSoL-VlDEqcHgNg8DHnOOr9Wngma9lV4QZSASRXtpeiOi9mutIUyGGM_g6BtpNiffjy7wL4vOx4eAncaZ_-UAAm6k5XuNR
10. **Resilience Patterns** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF-XTXUTOQoZ6hM-lFuy6oU1IA2evhuz8VUEDpdYHJLqJfHAFFDGnNtDmanyVTbGbxWi91Ig2wfC5l_P35VOR1PjTZ6DrTc10OonTqqNytzW3Z0itwKPdA8m4h69IAVnN2VWNlRiK-LNVAWnboOU9iNqRlYN3zJaN1IOqPuu51hMpPztQRy56pWcnsGoAJnbmHJfaDzcyjJV5vpGS3dwK7S1dsyPIdT4LePjLta2aYo
11. **PR Review Process** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQETqX78pPOE8Xqb5VyBy1jIs7yNJXzlkpRLj3y_0YKh8RQYb7xhK_WmiC7HuDsYMovZJUntxL28YX2elpxd-v21a3AlHxJApX9ILgJONQASlrOcmBov42WtiP-lR8vlORMTWRvB5460cNVbx3NUgv3GhluR8UMovpRh
12. **Human‑in‑the‑Loop** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH8WOTSucqk5XM78_UAaBwwiabUltGpnY57XxVL5slTCGEKyQduN5Lp2EiDDcMl8kb2HlhMKMakloLJQg_9pYWa38KftGuiessIMil6pyqPWNq8nwVUaPRD6NAgRwVM8ZKjSL8otyGD71Hk_bYA8et6FDY8Vh-qx1K7tT1HDFVsUTt0_YC-alxAtotNbD6Ilrc=
13. **Observability** – https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHhQug2T3DwLbTUgNdSg_7ipLLmfN3_tnp5I0Zt6-XkClMAV-RgGi-X7MoErYL8ol6CejFdWKDHp9E88xw_bM7qQyLKGw-wjXclNovSxyqewa47vpehnNaKEnCpDnTbe16Et8fZXRGfyM15C_rI_6RxXC8qKZwM804eP1hK3iOEKoN-tfJ13ASSGZzDpNbPv-7yngbQXzRLwf6jREc5Jg==

## 12. Session Memory & Persistent Logs

- **Session Log File Creation** – When an agent session starts, automatically create a markdown file `session_<timestamp>.md` in the `logs/` directory. The file should record:
  - Session start time and unique session ID.
  - Actions performed (e.g., file edits, generated code snippets).
  - Decisions made, including rationale and any prompts used.
  - Updated knowledge or learned patterns.
- **Continuous Updates** – Append to the same session log throughout the session. Use clear headings for each major step (e.g., `### File Edited: utils.py`).
- **Memory Persistence** – At session end, finalize the log and merge any *important* entries into a persistent `memory.md` file that aggregates crucial insights, reusable templates, and reference snippets across sessions.
- **Loading on Restart** – On a new session, the agent should read `memory.md` to recall past decisions, style guidelines, and shared utilities, ensuring continuity and avoiding duplicated effort.
- **Structure of `memory.md`** – Organize by category (e.g., `# Coding Standards`, `# Common Utilities`, `# Learned Patterns`). Each entry must be atomic and include a source reference (session ID and timestamp).
- **Automation Hooks** – Implement helper functions `init_session_log()` and `finalize_session(memory_path)` that agents can call without manual intervention.
- **Review Checklist Update** – Add a checklist item:
  | **Memory** | Ensure session changes are persisted to `memory.md` for future sessions. |

---
