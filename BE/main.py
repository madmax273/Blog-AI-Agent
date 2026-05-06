from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from config.settings import settings
from config.logging import Logger, configure_app_logging
logger = Logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Configure logging
    configure_app_logging(settings.LOG_LEVEL, settings.LOG_DIR)
    
    logger.info("Application startup completed")
    yield
    
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    start_time = time.time()
    logger.info("Root endpoint accessed")
    
    response = {"message": "Welcome to Blog API"}
    
    response_time = time.time() - start_time
    logger.log_request("GET", "/", 200, response_time)
    
    return response


@app.get("/health")
async def health_check():
    start_time = time.time()
    logger.info("Health check endpoint accessed")
    
    response = {"status": "healthy"}
    
    response_time = time.time() - start_time
    logger.log_request("GET", "/health", 200, response_time)
    
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
