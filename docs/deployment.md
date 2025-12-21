# Deployment & Operations

## Targets
- Package the entire service inside Docker images for reproducible local dev and server deployment.
- Support at least two stages: `dev` (local docker-compose) and `prod` (HP EliteDesk 800 G3 DM server with Intel i5-6500T CPU, 16 GB RAM, 500 GB SSD).

## Containerization Plan
1. **Base image**: Start from an official Python slim image (3.11+) plus system libs needed for vector DB/LLM runtimes.
2. **Layering**:
   - Install Python dependencies via `pip`/`uv` using a locked requirements file.
   - Add project source, data ingestion scripts, and entrypoints.
   - Provide optional stage for downloading / mounting LLM weights (likely via volume or init container to avoid bloated images).
   - Bundle compiled React + Tailwind assets during the build so the API container can serve them.
3. **Services**:
   - `api`: FastAPI/Flask app exposing chat + analysis endpoints. It will also serve the built React + Tailwind static bundle for simplicity (single container to deploy/redeploy).
   - `vector-db`: container for the chosen DB if it runs as a separate service (e.g., Qdrant). For embedded stores (FAISS/Chroma), this may remain in-process.
   - `ollama`: hosts the selected LLM; expose Ollama’s HTTP API to the app container.
   - `postgres`: stores user accounts, authentication artifacts, and high-level conversation metadata.
   - `mongodb`: stores conversation transcripts, loop-graph artifacts, and other document-style data.
   - `worker` (optional): handles heavy ingestion / scheduled updates so the API stays responsive.
   - Admin features (React-based or integrated into the main frontend) run within the same container to manage account approvals.
4. **docker-compose** will orchestrate multi-service dev setup; production will rely on the same compose file or a translated Kubernetes manifest once needed.
5. **Setup script**: `scripts/melvin.sh` (see `docs/setup.md`) orchestrates env var/secrets generation, admin bootstrap, frontend build, docker-compose lifecycle, logs, and backups.

## Deployment Workflow (initial sketch)
0. Code is managed on GitHub; developers work through feature branches + PRs.
1. Run `./scripts/melvin.sh launch` on new environments to prompt for admin credentials, build the frontend, and boot Docker services.
2. Developer builds and tags Docker image locally as needed (`docker build -t melvin-api:dev .`) for CI/CD or remote deployments.
3. Run tests inside the container to ensure deterministic behavior.
4. Push to container registry (to be decided) for deployment server consumption.
5. Deployment server pulls tagged image, runs migrations/ingestion jobs, then restarts services with minimal downtime.

## Configuration & Secrets
- Use environment variables for Scryfall rate-limit tuning, cache directories, and service ports.
- Store API keys (if any future external services) outside the repo and inject them at runtime through Docker secrets or env files ignored by git.
- Password policy enforced by the API: minimum 8 characters with uppercase, lowercase, numeric, and symbol characters; setup script generates compliant defaults.
- Backups: `scripts/melvin.sh backup` will dump Postgres and MongoDB, compress the archives, and rotate them under `/var/backups/melvin` (daily snapshots, keep latest 7) to fit within the server’s 500 GB SSD.
- Host ports: API exposed on `http://localhost:8000`, Postgres published on host port `8004` (mapped to container `5432`) to avoid conflicts with system Postgres.

## Observability
- Include structured logging (JSON) from the API container.
- Export minimal health metrics (request counts, retrieval latency, loop-analysis stats) via `/health` or `/metrics` endpoints.
- Capture ingestion failures/logs so they can be requested from the deployment server as needed.
- Track admin actions (approvals/denials) and unsuccessful login attempts so queued users who keep checking back have audit coverage.

## Outstanding Items / Questions
- Need to choose target registry and hosting stack (Docker Swarm, Kubernetes, plain Docker service?).
- Confirm whether the i5-6500T/16 GB box will run everything (Ollama + vector DB + API + frontend) or if we should offload components.
- Determine how model weights will be synced to the server securely.
- Implement password reset tooling (CLI/UI) and finalize backup cadence/retention for Postgres + MongoDB.
- Design UX around audit logs (account approvals, failed logins) and expose them for admins.

Update this document as soon as decisions are made or issues arise during containerization.
