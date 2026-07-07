# Study Agent UI

React 18 + Vite + TypeScript frontend for the `study_agent` plugin.

## Build

The build output is **not committed** (see `.gitignore`) — run this once after
checkout, and again whenever you change `src/`:

```bash
cd plugins/study_agent/ui
npm install
npm run build
```

This writes `index.html` and hashed `assets/*` directly into
`plugins/study_agent/static/`, where the core's `SPAStaticFiles` fallback
(`core/api/lifespan.py`) automatically serves it at `/study-agent/` once
`static/index.html` exists — no custom routing code needed. Generated
podcast audio in `static/podcasts/` is untouched by the build
(`emptyOutDir: false`).

## Dev server

```bash
npm run dev
```

Runs Vite on `http://localhost:5181` and proxies `/api/study-agent/*` and
`/plugins/study-agent/*` to a locally running `baselith run` (port 8000).

## Structure

- `src/api/` — fetch client + one `@tanstack/react-query` hook module per
  backend domain (subjects, files, flashcards, sessions, chat, activeStudy,
  podcasts, debug).
- `src/components/` — shared UI primitives (Button, Modal, Tabs, ...).
- `src/pages/` — one directory per route, each further split into
  sub-components/hooks so no file exceeds ~500 lines (repo convention, see
  root `CLAUDE.md`).
