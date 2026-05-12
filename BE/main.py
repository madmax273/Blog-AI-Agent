from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.logging import Logger, configure_app_logging
from config.settings import settings
from database import models
from database.connection import engine
from app.api.v1.api import router as api_router

# -----------------------------------------------------------------------------
# Initialize logger instance
# -----------------------------------------------------------------------------
logger = Logger()

# -----------------------------------------------------------------------------
# Application Lifespan Events
# Handles startup and shutdown events for the FastAPI application
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executes application startup and shutdown logic.

    Startup Tasks:
    - Configure logging
    - Initialize database connection
    - Create database tables

    Shutdown Tasks:
    - Graceful application shutdown logging
    """

    # -------------------------------------------------------------------------
    # STARTUP EVENTS
    # -------------------------------------------------------------------------
    try:
        # Configure logging system
        configure_app_logging(
            settings.LOG_LEVEL,
            settings.LOG_DIR
        )

        logger.info("Logging configured successfully")
        logger.info(
            f"Starting {settings.APP_NAME} v{settings.APP_VERSION}"
        )

    except Exception as e:
        # Logging setup failure is critical
        print(f"Failed to configure logging: {e}")
        raise

    # -------------------------------------------------------------------------
    # Database Initialization
    # -------------------------------------------------------------------------
    try:
        logger.info("Initializing database connection...")

        # Create tables if they don't exist
        models.Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully")

    except Exception as e:
        logger.exception(f"Database initialization failed: {e}")

        # Stop application startup if DB connection fails
        raise RuntimeError(
            "Application startup aborted due to database failure"
        ) from e

    logger.info("Application startup completed successfully")

    # Application runs here
    yield

    # -------------------------------------------------------------------------
    # SHUTDOWN EVENTS
    # -------------------------------------------------------------------------
    try:
        logger.info("Application shutting down gracefully...")

    except Exception as e:
        print(f"Shutdown logging failed: {e}")


# -----------------------------------------------------------------------------
# FastAPI Application Initialization
# -----------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)


# -----------------------------------------------------------------------------
# CORS Middleware Configuration
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Register API Routers
# -----------------------------------------------------------------------------

app.include_router(api_router, prefix="/api/v1")


# -----------------------------------------------------------------------------
# Root Endpoint
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    """
    Root endpoint for API health/welcome message.
    """

    start_time = time.perf_counter()

    try:
        logger.info("Root endpoint accessed")

        response = {
            "message": "Welcome to Blog API"
        }

        response_time = time.perf_counter() - start_time

        logger.log_request(
            method="GET",
            endpoint="/",
            status_code=200,
            response_time=response_time
        )

        return response

    except Exception as e:
        logger.error(f"Root endpoint failed: {e}")

        return {
            "status": "error",
            "message": "Internal server error"
        }


# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """
    Health check endpoint used for:
    - Monitoring
    - Docker/Kubernetes probes
    - Load balancer health checks
    """

    start_time = time.perf_counter()

    try:
        logger.info("Health check endpoint accessed")

        response = {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION
        }

        response_time = time.perf_counter() - start_time

        logger.log_request(
            method="GET",
            endpoint="/health",
            status_code=200,
            response_time=response_time
        )

        return response

    except Exception as e:
        logger.exception(f"Health check failed: {e}")

        return {
            "status": "unhealthy",
            "message": "Health check failed"
        }


# -----------------------------------------------------------------------------
# Local Development Entry Point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("Starting Uvicorn development server...")

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )

    except Exception as e:
        logger.exception(f"Failed to start server: {e}")