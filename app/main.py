from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import Base, engine
from app.core.config import settings
from app.core.logger import get_logger
from app.api.v1.endpoints import auth, notes
from app.api.v1.endpoints.user import router as users_router


logger = get_logger(__name__)

app = FastAPI(
    title="SOAPify",
    version=settings.VERSION,
)


@app.on_event("startup")
def startup_event():
    logger.info("Starting SOAPify backend")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ensured")
    except Exception:
        logger.exception("Database table creation failed")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(notes.router, prefix="/api/v1/notes", tags=["Notes"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])


@app.get("/")
def root():
    return {"status": "ok", "service": "SOAPify"}


@app.get("/health")
def health():
    status = {
        "api": "ok",
        "db": "unknown",
        "llm": "unknown",
    }

    # Database health
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["db"] = "ok"
    except Exception as e:
        status["db"] = f"error: {str(e)}"

    # LLM health (logical, not physical)
    if settings.LLM_PROVIDER == "ollama":
        status["llm"] = "ollama (local)"
    else:
        status["llm"] = "groq (cloud)"

    return status
