from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router as api_router
from .core.config import get_settings
from .core.database import SessionLocal
from .services.bootstrap import init_db
from .services.assessment_bootstrap import bootstrap_assessment_questions
from .services.ingest import ingest_service


settings = get_settings()
app = FastAPI(title=settings.project_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event() -> None:
    init_db()
    # Bootstrap assessment questions
    db = SessionLocal()
    try:
        bootstrap_assessment_questions(db)
    finally:
        db.close()
    # Ensure datastore loaded on startup
    from .services.melvin import melvin_service  # noqa: F401

    _ = melvin_service


@app.post("/ingest", tags=["system"])
def ingest_data() -> dict:
    ingest_service.ingest()
    return {"status": "ok"}


app.include_router(api_router, prefix=settings.api_prefix)

frontend_override = settings.dict().get("frontend_dist")
if frontend_override:
    FRONTEND_DIST = Path(frontend_override)
else:
    FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    async def missing_frontend():
        return JSONResponse({"message": "Frontend not built. Run npm run build inside frontend/."})


@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if FRONTEND_DIST.exists():
        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    return JSONResponse({"message": "Frontend not built."})

