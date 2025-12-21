## Melvin Project

Melvin is an open-source Magic: The Gathering rules assistant that combines the Comprehensive Rules, Oracle card data, historical rulings, and the live Scryfall API to answer judge questions, detect infinite loops, and suggest card interactions. All development and deployment will run inside Docker for reproducibility.

### Documentation
- `docs/README.md` – overview of the documentation hub.
- `docs/development.md` – requirements, architecture vision, and engineering backlog.
- `docs/deployment.md` – containerization/deployment strategy.
- `docs/journal.md` – running log of decisions and outstanding questions.
- `docs/setup.md` – plan for the setup/deployment automation script.

### Data Layout
- Raw datasets live under `data/raw/` (not tracked in git due to size). Copy the following files into that folder before running the stack:
  - `MagicCompRules 20251114.txt`
  - `oracle-cards-20251221100301.json`
  - `rulings-20251221100031.json`
- Derived artifacts (embeddings, caches) will later live under `data/processed/` (to be generated via scripts).

### Quick Start
Prereqs: Docker + Docker Compose plugin, Node.js/npm, curl.

```bash
./scripts/melvin.sh launch
# -> prompts for admin credentials, generates secrets, builds frontend,
#    starts the stack, and prints http://localhost:8001 (API) with Postgres on host port 8004
```

Use the printed URL to submit a user request, log in as the admin to approve users, and begin chatting with Melvin.

Start with the documentation hub when onboarding or planning new work.
# melvin
