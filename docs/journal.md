# Project Journal

## 2025-??-?? (initial setup)
- Repository currently references the key datasets (`MagicCompRules 20251114.txt`, `oracle-cards-20251221100301.json`, `rulings-20251221100031.json`) stored locally under `data/raw/` (not tracked in git due to size).
- Goal clarified: build "Melvin" AI assistant leveraging those datasets plus Scryfall API to answer MTG rules questions and spot infinite loops.
- Constraint: rely solely on free/open-source tooling; deployment must use Docker with Ollama hosting the eventual LLM.
- Deployment hardware identified: HP EliteDesk 800 G3 DM (Intel i5-6500T, 16 GB RAM, 500 GB SSD).
- MVP interaction surface decided: web-based chat UI hosted alongside the API.
- Requirement update: users must authenticate and maintain multiple saved conversations with Melvin.
- Added requirement: local password-based auth plus an admin control panel to approve new user accounts.
- New decision: central setup/deployment script (`scripts/melvin.sh`) will manage secrets, env vars, and lifecycle commands; code hosted on GitHub.
- Password policy set (≥8 chars w/ upper, lower, number, symbol); account requests queue for admin approval handled via UI/CLI, first admin created by setup script.
- Clarified that users check approval status by retrying login; engineering team owns schema design choices to ensure secure storage and auditing.
- No formal deadlines; goal is to reach a working MVP ASAP while making pragmatic choices (e.g., heuristic-based loop detection sized for the hardware, on-host rotating backups).
- Documentation system established (`docs/README.md`, `development.md`, `deployment.md`, `journal.md`).

## 2025-??-?? (MVP bootstrap)
- Implemented FastAPI backend with auth, conversation storage, admin approval workflow, and heuristic retrieval over the MTG datasets.
- Added Postgres + MongoDB via docker-compose, SQLAlchemy models, and initial admin bootstrap logic.
- Built React + Tailwind SPA (account request/login, chat UI, admin queue) bundled with Vite and served from the API container.
- Created interactive `scripts/melvin.sh launch` command that prompts for admin credentials, generates secrets, builds frontend, starts containers, and outputs the local URL for onboarding.
- README/docs updated with new quick-start instructions and setup details.
- Added auto-download of Scryfall bulk data (cards + rulings) to `scripts/melvin.sh launch`; manual placement only needed when offline.

## 2025-??-?? (startup stability)
- Upgraded Chromadb to a pydantic-2-compatible release to unblock backend image builds.
- Made the LLM/vectorstore service lazy-loaded so API healthchecks are not blocked by model downloads or Chroma initialization; first question now performs the heavy load.
- Added retry/backoff around DB initialization to tolerate slow Postgres startup in docker-compose.
- Documented the first-request warm-up behavior and added a TODO to offer an optional pre-warm step during setup.

## Open Questions
- When will the identified deployment server be available for continuous hosting?
- Do we need password rotation/reset tooling beyond the current policy (e.g., admin-triggered resets, forced changes)?
- Backup cadence/retention expectations beyond the default 7-day on-host rotation.
- Expected delivery milestones or MVP deadline (still unspecified; working ASAP remains the guidance).

Add new dated entries whenever noteworthy work is done or blockers are discovered.
