from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session

from database import create_db_and_tables, engine, seed_database
from routers import cases, detect


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed_database(session)
    yield


app = FastAPI(
    title="Deepfake Detective API",
    description="Backend for the UNESCO MIL Hackathon 2026 — Deepfake Detective",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
# In production, restrict origins to your Vercel domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to ["https://your-app.vercel.app"] before submission
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(cases.router)
app.include_router(detect.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "app": "Deepfake Detective API"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
