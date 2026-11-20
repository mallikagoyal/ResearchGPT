"""ResearchGPT FastAPI application entrypoint."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.exceptions import (
    AlreadyExistsError,
    FileProcessingError,
    InvalidCredentialsError,
    NotFoundError,
    ResearchGPTError,
    UnauthorizedError,
    ValidationFailedError,
)
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered research document assistant with RAG-based chat.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Centralized exception handling ---
# Maps domain exceptions (raised by services/repositories) to HTTP responses,
# so route handlers never need to know about status codes for business errors.
_ERROR_STATUS_MAP: dict[type[ResearchGPTError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    AlreadyExistsError: status.HTTP_409_CONFLICT,
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    UnauthorizedError: status.HTTP_403_FORBIDDEN,
    ValidationFailedError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    FileProcessingError: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


@app.exception_handler(ResearchGPTError)
async def researchgpt_exception_handler(
    request: Request, exc: ResearchGPTError
) -> JSONResponse:
    """Translate domain exceptions into consistent JSON error responses."""
    status_code = _ERROR_STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
    logger.warning("%s: %s (path=%s)", type(exc).__name__, exc.message, request.url.path)
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all so unexpected errors never leak stack traces to clients."""
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


app.include_router(health_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup() -> None:
    """Log key configuration at startup (never log secrets)."""
    logger.info(
        "%s starting | env=%s | llm_provider=%s | embedding_model=%s",
        settings.APP_NAME,
        settings.APP_ENV,
        settings.LLM_PROVIDER,
        settings.EMBEDDING_MODEL_NAME,
    )
