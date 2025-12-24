## Melvin Project

Melvin is an open-source Magic: The Gathering rules assistant that combines the Comprehensive Rules, Oracle card data, historical rulings, and the live Scryfall API to answer judge questions, detect infinite loops, and suggest card interactions. All development and deployment will run inside Docker for reproducibility.

### Documentation
- `docs/README.md` – overview of the documentation hub.
- `docs/development.md` – requirements, architecture vision, and engineering backlog.
- `docs/deployment.md` – containerization/deployment strategy.
- `docs/journal.md` – running log of decisions and outstanding questions.
- `docs/setup.md` – plan for the setup/deployment automation script.

### Data Layout
- Raw datasets live under `data/raw/` (not tracked in git due to size). The launch script will try to download the Scryfall dumps automatically; if it cannot (offline environments), place these files manually:
  - `MagicCompRules 20251114.txt`
  - `oracle-cards-20251221100301.json` (download via `GET https://api.scryfall.com/bulk-data`)
  - `rulings-20251221100031.json` (same endpoint)
- Curated reference blurbs live under `data/reference/` and are versioned with the repo. These contain onboarding summaries (e.g., “How to Play Magic” and “Commander rules overview”) that the ingestion job folds into Melvin’s knowledge base alongside the Comprehensive Rules.
- Derived artifacts (embeddings, caches) will later live under `data/processed/` (to be generated via scripts).

### Quick Start
Prereqs: Docker + Docker Compose plugin, Node.js/npm, curl.

```bash
./scripts/melvin.sh launch
# -> prompts for dataset locations (if not already under data/raw/), admin credentials,
#    generates secrets, builds frontend, starts Docker services, and prints http://localhost:8001.
```

Use the printed URL to submit a user request, log in as the admin to approve users, and begin chatting with Melvin.
Note: the first question you ask will lazily spin up the model + Chroma stores and may take extra time while Ollama and embeddings warm up; subsequent calls are faster.

Start with the documentation hub when onboarding or planning new work.
# melvin
