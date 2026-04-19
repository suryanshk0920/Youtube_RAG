"""
TubeQuery API
=============
FastAPI backend. Run with:
    uvicorn api.main:app --reload

from the tubequery/ directory.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.routers import chat, ingest, sources
from api.routers import sessions
from api.routers import profile
from api.routers import kbs
from api.routers import subscription
from api.schemas import HealthResponse
from middleware.redis_rate_limit import RedisRateLimitMiddleware
from services.redis_service_production import get_production_redis_service, close_production_redis_service
import config

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# ── Application Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("🚀 Starting TubeQuery API...")
    
    # Initialize Redis service
    try:
        redis_service = await get_production_redis_service()
        logger.info("✅ Redis service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis service: {e}")
        # Continue without Redis - fallback mechanisms will handle it
    
    # Create data directories
    os.makedirs(config.CHROMA_DIR, exist_ok=True)
    os.makedirs(config.DATA_DIR, exist_ok=True)
    logger.info("📁 Data directories created")
    
    logger.info("🎉 TubeQuery API startup complete")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down TubeQuery API...")
    try:
        await close_production_redis_service()
        logger.info("✅ Redis service closed successfully")
    except Exception as e:
        logger.error(f"❌ Error closing Redis service: {e}")
    
    logger.info("👋 TubeQuery API shutdown complete")

# ── App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="TubeQuery API",
    description="YouTube RAG backend — ingest videos, ask questions, get cited answers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Rate Limiting ────────────────────────────────────────────────────
app.add_middleware(RedisRateLimitMiddleware, default_requests_per_minute=60)

# ── CORS ─────────────────────────────────────────────────────────────
# In production, replace "*" with your Next.js domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(sources.router)
app.include_router(sessions.router)
app.include_router(profile.router)
app.include_router(kbs.router)
app.include_router(subscription.router)


# ── Health check ─────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    return HealthResponse(status="ok")


# ── Redis Health Check ──────────────────────────────────────────────
@app.get("/health/redis", tags=["health"])
async def redis_health():
    """Comprehensive Redis health check with performance metrics."""
    try:
        redis_service = await get_production_redis_service()
        health_info = await redis_service.health_check()
        
        # Determine HTTP status based on health
        if health_info["status"] == "unhealthy":
            raise HTTPException(status_code=503, detail=health_info)
        elif health_info["status"] == "degraded":
            # Return 200 but with warning status
            return {**health_info, "warning": "Service is degraded but operational"}
        
        return health_info
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis service is unavailable"
            }
        )


# ── System Metrics ──────────────────────────────────────────────────
@app.get("/metrics", tags=["monitoring"])
async def system_metrics():
    """Get comprehensive system metrics for monitoring."""
    try:
        redis_service = await get_production_redis_service()
        redis_metrics = await redis_service.get_metrics()
        
        return {
            "api": {
                "status": "healthy",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "redis": redis_metrics,
            "database": {
                "status": "healthy",  # Could add actual DB health check
                "provider": "supabase"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {
            "api": {
                "status": "healthy",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "redis": {
                "status": "unavailable",
                "error": str(e)
            },
            "database": {
                "status": "healthy",
                "provider": "supabase"
            }
        }
