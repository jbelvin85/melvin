# Setup & Deployment Script Plan

We will author a single entrypoint script (working name: `scripts/melvin.sh`) that automates developer onboarding, environment initialization, and deployments. It will run on Debian-based hosts and inside CI/CD.

## Capabilities
1. **Environment bootstrap**
   - Prompt for and create `.env` files for API, frontend, and database services.
   - Generate initial secrets (JWT signing keys, password salts, admin bootstrap password) using `openssl`/`python -c`.
   - Create first admin account credentials (respecting password policy: ≥8 chars, uppercase, lowercase, number, symbol) and optionally display/store them securely.
   - Configure Docker `.env` files for compose.
2. **Dependency install**
   - Optionally install system prerequisites (Docker, Docker Compose plugin, Ollama) when running on fresh servers.
   - Create/activate Python virtualenvs for local tooling.
3. **Data management**
   - Download/update dataset snapshots if missing (rules, Oracle cards, rulings) and stage ingestion outputs.
4. **Lifecycle commands**
   - `dev`: run docker-compose with mounted code for hot reload of API/frontend.
   - `deploy`: build/tag/push production images, apply migrations, and restart services.
   - `logs`: tail aggregated logs for API, worker, Ollama, Postgres, MongoDB.
   - `shell`: drop into service containers for debugging.
5. **Admin helpers**
   - Create initial admin account if none exists and allow later rotations/reset.
   - Manage the user-request queue (list pending requests, approve/deny) from the CLI for emergency interventions.
   - Trigger backup jobs for Postgres/MongoDB and store artifacts locally or to a configured remote path.

## Current Implementation Status
- `scripts/melvin.sh` now orchestrates the entire lifecycle:
  - `launch` (default): verifies raw dataset files (prompts for their local paths if missing), prompts for admin credentials, generates the JWT secret, builds the React frontend, brings up Docker services, waits for the API health check, and prints the access URL plus admin username.
  - `dev`: rebuilds the frontend and runs `docker compose up` in the foreground (for local debugging).
  - `down`: stops the compose stack.
  - `logs [service]`: tails logs.
  - `backup`: runs Postgres/Mongo dumps into `./backups/<timestamp>/`.
- Remaining improvements: integrate admin CLI helpers (approve/deny requests), add secret rotation, integrate remote backup upload, and hook the script into CI/CD workflows.

## Prerequisites
- Docker + Docker Compose plugin installed on the host.
- Node.js + npm (used to install/build the frontend before containers start).
- curl (used for the health-check polling).
- `openssl` or Python 3 (already required) for secret generation.

## Implementation Notes
- Script should be idempotent so it can be re-run safely.
- Prefer Bash with small helper Python scripts for complex tasks.
- Keep secrets generation confined to local machine; never commit `.env` outputs.
- Integrate with GitHub workflows later for CI builds/tests.

Update this plan once scripting begins, noting finished commands and remaining gaps.
