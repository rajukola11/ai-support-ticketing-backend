from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.tickets.routes import router as tickets_router
from app.core.config import get_settings

settings = get_settings()


# -----------------------------
# Lifespan (startup / shutdown)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"🚀 Starting AI Support Ticketing API [{settings.ENV}]")
    yield
    # Shutdown
    print("👋 Shutting down AI Support Ticketing API")


# -----------------------------
# App instance
# -----------------------------
app = FastAPI(
    title="AI Support Ticketing API",
    description="Backend API for an AI-powered support ticketing system.",
    version="0.1.0",
    lifespan=lifespan,
    # Hide docs in production
    docs_url="/docs" if settings.ENV != "production" else None,
    redoc_url="/redoc" if settings.ENV != "production" else None,
)


# -----------------------------
# CORS Middleware
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Routers
# -----------------------------
app.include_router(auth_router)
app.include_router(tickets_router)


# -----------------------------
# Health Check
# -----------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "env": settings.ENV,
        "version": "0.1.0",
    }