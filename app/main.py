from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import os
import asyncio

from app.api.endpoints import router as api_router
from app.db.mongodb import connect_to_mongodb
from app.core.config import settings
from app.core.scheduler import Scheduler

# Configure loguru
logger.add(
    "logs/proxy_service.log",
    rotation="10 MB",
    retention="1 week",
    level="INFO"
)

# Create logs directory if not exists
os.makedirs("logs", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(api_router, prefix="/api", tags=["proxies"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Proxy Service...")
    await connect_to_mongodb()
    
    # Start scheduler in background
    asyncio.create_task(Scheduler.start())

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)