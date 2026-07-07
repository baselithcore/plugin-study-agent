# Study Agent

> University Study Assistant plugin for [BaselithCore](https://github.com/baselithcore/baselithcore).

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](#license)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](./manifest.yaml)
[![Readiness](https://img.shields.io/badge/readiness-stable-brightgreen.svg)](./manifest.yaml)
[![Tenancy](https://img.shields.io/badge/tenancy-personal-purple.svg)](./manifest.yaml)

Study Agent turns BaselithCore into a full study companion: create a course
per subject, drop in your notes and slides, and get AI-generated flashcards,
a Feynman-method tutor, a concept deconstructor with an interactive concept
map, multi-episode narrated podcasts, and a voice-enabled oral exam simulator
that adapts its questioning in real time via Monte Carlo Tree Search.

---

## At a glance

| Aspect            | Value                                                              |
| ------------------ | ------------------------------------------------------------------- |
| Version            | 0.1.0 (stable)                                                     |
| Tenancy            | `personal` — each user's subjects/documents/flashcards/sessions are private, even on a shared deployment |
| Entry point        | `plugin:StudyAgentPlugin`                                          |
| HTTP routes        | 35 under `/api/study-agent`                                        |
| Frontend           | React 18 + Vite + TypeScript, served as a SPA at `/study-agent`     |
| Persistence        | PostgreSQL (own tables, `study_*` prefix, tenant-scoped)            |
| Required resources | `llm`, `postgres`                                                   |
| Python deps        | `paddleocr>=3.0.0`, `pymupdf>=1.24.0`                               |
| Tests              | 36 (unit), mocked LLM/DB                                            |

---

## Features

- **Course management.** One subject per exam/course, with a folder-based
  file manager (drag & drop upload, bulk move/delete, nested folders).
- **Document ingestion with OCR fallback.** Native text extraction for
  PDF/DOCX/PPTX; falls back to PaddleOCR (page-render via PyMuPDF) for
  scanned PDFs and images.
- **Flashcards with SM-2 spaced repetition.** AI-generated from uploaded
  material, reviewed with the classic SuperMemo-2 scheduling algorithm.
- **Voice-enabled oral exam simulator.** An `OralExamPlanner` runs MCTS
  search over the syllabus to pick the next question (theory / application /
  trick / hint) based on the student's running topic scores and the chosen
  professor personality (*amichevole*, *equo*, *scrupoloso*). Live mode
  supports speech-to-text answers and text-to-speech questions.
- **Active Study toolkit:**
    - *Feynman method* — explain a concept in your own words, get evaluated
    on gaps, inaccuracies, and strengths.
    - *Concept Deconstructor* — cheat sheet, likely exam questions, mnemonic
    hooks, and an interactive, pannable/zoomable concept map.
    - *Podcast generator* — multi-episode narrated lessons synthesized via
    the core voice service, generated and streamed episode-by-episode.
- **Subject-level tutoring chat.** Retrieval over your uploaded documents,
  answered with source attribution.
- **Knowledge Graph integration.** Registers `study_subject` /
  `study_flashcard` entities and a `STUDY_CONTAINS` relationship.
- **Debug/telemetry panel.** Inspect MCTS search traces live from the UI.

---

## Repository layout

```text
study_agent/
├── manifest.yaml           # Marketplace metadata (name, tenancy, deps, integrity hash)
├── plugin.py               # StudyAgentPlugin entry point (Agent + Router + Graph)
├── agent.py                # StudyAgent: LLM-backed tutoring/flashcards/podcast/exam logic
├── router.py                # FastAPI routes (subjects, files, flashcards, sessions, podcasts)
├── persistence.py           # StudyDAO — tenant-scoped Postgres access + schema migrations
├── mcts_engine.py            # OralExamPlanner — MCTS-driven adaptive questioning
├── debug_tracker.py         # In-memory trace log for the debug panel
├── models.py                 # Pydantic request/response models
├── tests/                    # 36 unit tests (mocked LLM/DB)
├── static/                   # Built SPA output (index.html + assets/) — generated, not source
└── ui/                        # React + Vite + TypeScript frontend source
    └── src/
        ├── api/               # Typed fetch client, one module per resource
        ├── components/        # Shared UI primitives (Button, Modal, Tabs, ...)
        └── pages/              # Dashboard, CourseDetail (Files/Flashcards/ActiveStudy/OralHistory), OralExamLive, TutoringChat
```

---

## Installation

```bash
# From the baselithcore repo root
pip install -e ".[dev]"

# Plugin-specific Python deps (OCR)
pip install paddleocr>=3.0.0 pymupdf>=1.24.0

# Build the frontend once (repeat after any change under ui/src)
cd plugins/study_agent/ui
npm install
npm run build
```

Enable it in `configs/plugins.yaml`:

```yaml
study-agent:
  enabled: true
```

`postgres` and `llm` must be configured (see the main
[BaselithCore README](../../README.md)) — the plugin creates and migrates
its own `study_*` tables on startup.

---

## Frontend development

```bash
cd plugins/study_agent/ui
npm run dev          # Vite dev server with hot reload, proxies API calls to :8000
npm run build         # Production build -> ../static/ (index.html + assets/)
npm run typecheck     # tsc -b, no emit
```

The build output in `static/` is what actually ships — `ui/node_modules/`
and `ui/dist/` are git-ignored. The core auto-mounts the SPA at
`/study-agent` whenever `static/index.html` exists, with client-side routing
handled by `react-router-dom` (`basename="/study-agent"`).

---

## Tenancy

Declared `tenancy: personal` in `manifest.yaml`: every subject, document,
folder, flashcard, oral session, and podcast is scoped to the authenticated
user via `core.context.resolve_plugin_tenant_key`, not shared across the
deployment. See [Multi-Tenancy](../../mkdocs-site/docs/advanced/multi-tenancy.md)
for the underlying mechanism.

---

## Testing

```bash
python -m pytest plugins/study_agent/tests/ -v -o addopts=""
```

All persistence and LLM calls are mocked — no live Postgres/LLM needed to
run the suite.

---

## Marketplace publication

```bash
# One-time: compute/refresh the manifest integrity hash after any change
# to the plugin's Python source (required — a stale hash fails to load)
baselith plugin sign plugins/study_agent

# Validate structure + manifest before shipping (uses the directory name,
# not the manifest `name:` — the local-plugin CLI resolves by directory)
baselith plugin validate study_agent

# Authenticate once (saves your marketplace API key)
baselith plugin marketplace login

# Publish
baselith plugin marketplace publish plugins/study_agent
```

## License

MIT — see the root [BaselithCore license](../../LICENSE) unless a
plugin-specific `LICENSE` file is added.
