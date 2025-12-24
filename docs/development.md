# Development Guide

## Project Summary
Melvin is an AI rules assistant for Magic: The Gathering. It must answer judge-style questions using:
- `MagicCompRules 20251114.txt` (Comprehensive Rules snapshot).
- `oracle-cards-20251221100301.json` (Oracle card database dump).
- `rulings-20251221100031.json` (Historic rulings dump).
- Scryfall bulk data endpoint (`GET https://api.scryfall.com/bulk-data`) used to download/update Oracle cards and rulings dumps on demand (store results under `data/raw/`).
- Live data from the Scryfall REST API for freshness gaps.
The assistant also needs to analyze card interactions, detect infinite loops, and recommend plays or rulings.

## Guiding Principles
1. Favor free/open-source models, tooling, and libraries.
2. Keep responses grounded by citing retrieved rule/card text.
3. Support explainability for suggested combos or loops.
4. Design everything for Docker-based deployment from the start.
5. Work iteratively toward a shippable MVP as quickly as possible; there are no formal deadlines, but velocity matters.

## Current Architecture Sketch
- **Data ingestion**: Python pipelines that normalize card IDs/names and chunk rules text for embedding.
- **Vector store**: Open-source option such as FAISS/Chroma/Qdrant for retrieval-augmented generation (RAG).
- **LLM**: Self-hosted instruct model (e.g., Llama 3 or Mistral) accessed via local runtime (Ollama/text-generation-webui) and exposed to the app through LangChain/LlamaIndex.
- **Reasoning layers**:
  - Retrieval chain pulling Comprehensive Rules, Oracle entries, and rulings independently.
  - Combo/loop analyzer that models mana changes, untap triggers, and resource deltas using lightweight heuristic graph search (resource delta tracking + circular dependency detection) tuned for the i5-6500T hardware.
- **Interface**: FastAPI/Flask service exposing a web chat UI for interacting with Melvin, including authenticated user accounts and multi-conversation history.
- **Frontend**: React + Tailwind SPA bundled by Vite and served from the FastAPI container; default UI already includes account request/login flow, conversation list, chat view, and admin queue.
- **Bootstrap tooling**: `scripts/melvin.sh` sets up secrets, builds the frontend, orchestrates docker-compose, and outputs the access URL.

## Tooling & Dependencies (planned)
- Python 3.11+ for ingestion, orchestration, and API service.
- LangChain or LlamaIndex for RAG pipelines.
- `requests` (or `httpx`) client for Scryfall API.
- `pydantic` for schema validation of Scryfall/JSON payloads.
- Vector DB library (decide once prototype chosen).
- Ollama runtime on deployment server to host the selected open LLM (model choice TBD once experiments confirm best fit for hardware).
- Datastores: PostgreSQL (auth/user/conversation metadata) and MongoDB (flexible conversation transcripts / derived artifacts).
- Git + GitHub for source control, PR workflows, and CI integration.
- Testing: `pytest` with fixture data + curated judge scenarios.

## Authentication & Account Management
- Local password auth with the following policy: minimum 8 characters containing uppercase, lowercase, number, and symbol.
- No email verification; new account requests are queued until an admin approves or denies them. Users must periodically attempt to log in to check their status (pending requests simply fail to authenticate until approved).
- Setup/deploy script must create the first admin account interactively (prompt + generated password).
- Admin control panel handles queue review, approvals, denials, and manual account management.
- Engineering team (you) owns database schema design for accounts, audit logs, and conversation storage, following best practices for security/compliance.

## Current Implementation Snapshot
- Backend FastAPI app live under `backend/app/` with data-loader-based responses (keyword heuristic), auth, conversation management, and admin queue endpoints.
- Database: SQLAlchemy models for users, account requests, conversations; runtime uses Postgres + MongoDB (messages) via docker-compose.
- Startup: DB initialization now retries with backoff to tolerate slower Postgres boot; LLM/vectorstore stack loads lazily on first request so the API can report healthy before heavy downloads occur.
- Frontend: React + Tailwind SPA (Vite) served by the backend; supports requesting accounts, logging in, listing/sending conversations, and administrative approvals.
- Bootstrap script: `scripts/melvin.sh launch` prompts for admin credentials, generates secrets, builds the frontend, starts docker-compose, and prints `http://localhost:8000`.

## Data Handling Notes
- Keep original dumps under `data/raw/` (local-only; gitignored due to size). Treat derived embeddings as build artifacts (ignored by git, reproduced via scripts under `data/processed/`).
- `scripts/melvin.sh launch` calls the Scryfall bulk API to refresh Oracle/rulings dumps automatically; if offline, drop those files into `data/raw/` manually.
- The setup script also ensures the configured Ollama model (`OLLAMA_MODEL`) is available by invoking `ollama pull` inside the Ollama container before starting the API.
- Curated teaching/reference blurbs (e.g., “How to Play MTG,” Commander rules digest) live under `data/reference/` and are included in the ingestion run so Melvin can cite them alongside the Comprehensive Rules.
- Implement chunk metadata linking back to source rule IDs and card identifiers.
- Cache Scryfall lookups to respect rate limits.
- The launch script automatically triggers the `/ingest` endpoint after the API becomes healthy so the latest raw/reference data are embedded at each run.

## Near-Term Engineering Tasks
- [ ] Define exact LLM hosting approach (model + runtime) that satisfies open-source constraint.
- [ ] Write ingestion script prototypes for each data source (current MVP uses a simple keyword matcher).
- [ ] Choose vector database and schema for multi-source retrieval.
- [x] Draft API contract for answering questions and reporting loop findings (initial FastAPI endpoints live under `/api/...`; will expand as RAG features mature).
- [ ] Plan evaluation harness with known judge questions + loop detection cases.
- [ ] Design auth + session storage (local password auth in Postgres, conversation history split across Postgres metadata and MongoDB transcripts).
- [x] Build admin control panel for approving/activating new user account requests (available in the React SPA).
- [x] Implement `scripts/melvin.sh` (or equivalent) to bootstrap environments, manage secrets, run docker-compose, and handle deployments (see docs/setup.md).
- [x] Implement user-request queue workflow (request submission, admin approval/denial; users reattempt login to check status).
- [x] Ensure the launch script seeds the initial admin account automatically via `/api/auth/bootstrap`.
- [ ] Draft relational + document database schemas (Postgres + MongoDB) covering auth, approvals, conversations, and auditing using industry-standard patterns (initial SQLAlchemy models exist; need ERD + migrations + documentation).
- [ ] Add a pre-warm step (optional flag) to build embeddings + pull Ollama model during setup so first-question latency stays predictable.

## Risks / Unknowns
- Model quality vs. hardware limits once all rule text is loaded.
- Loop detection accuracy may require iterative tuning of the heuristic graph search; more advanced solvers could be added later if hardware allows.
- Need clarity on acceptable latency for live queries hitting Scryfall.

## Requested Clarifications
- Target hardware: HP EliteDesk 800 G3 DM 35W, Intel i5-6500T (4 cores @ 2.5 GHz), 16 GB DDR4 RAM, 500 GB SSD.
- Web chat frontend: React + Tailwind CSS confirmed; need any additional requirements (routing, auth, persistence?).
- Accessibility requirements for the chat + admin views?
- Preferred UX for informing users about approval queue status (currently default: users manually retry login to see if approved).
- Backup retention expectations beyond the planned on-host rotation (see deployment doc).

Update this document as decisions land and tasks complete.
