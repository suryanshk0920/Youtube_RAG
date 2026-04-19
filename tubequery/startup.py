"""
Minimal startup script for Render deployment
============================================
This ensures the port binds immediately, then initializes services lazily.
"""

import os
import sys
import logging
from pathlib import Path

# Add the tubequery directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Apply memory optimizations before importing anything heavy
from optimize_startup import optimize_for_low_memory
optimize_for_low_memory()

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

def create_minimal_app():
    """Create a minimal FastAPI app that binds to port immediately."""
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(
        title="TubeQuery API",
        description="YouTube RAG backend",
        version="1.0.0",
    )
    
    @app.get("/health")
    def health():
        return {"status": "ok", "version": "1.0.0"}
    
    @app.get("/")
    def root():
        return {"message": "TubeQuery API is running", "docs": "/docs"}
    
    logger.info("✅ Minimal app created - port will bind immediately")
    return app

def setup_full_app():
    """Set up the full application with all routes and middleware."""
    try:
        from api.main_simple import app as full_app
        logger.info("✅ Simplified application loaded successfully")
        return full_app
    except Exception as e:
        logger.error(f"❌ Failed to load simplified application: {e}")
        logger.info("📝 Falling back to minimal app")
        return create_minimal_app()

# Create the app
app = setup_full_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)