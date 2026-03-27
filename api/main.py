"""api/main.py — AutoAuthor FastAPI 서비스"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from autoauthor.db.connection import init_db
    init_db()
    print("✅ AutoAuthor API 시작")
    yield
    print("👋 AutoAuthor API 종료")

app = FastAPI(
    title="AutoAuthor API",
    version="6.0.0",
    description="한국 콘텐츠 블로거를 위한 AI 기획 자동화",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers import trends, pipeline as pipeline_router
app.include_router(trends.router)
app.include_router(pipeline_router.router)

@app.get("/")
async def root():
    return {"service": "AutoAuthor", "version": "6.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}
