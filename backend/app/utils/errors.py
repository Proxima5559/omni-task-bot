from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class VoiceRejected(AppError):
    """Voice message refused up-front (too long / too big)."""


class QueueUnavailable(AppError):
    status_code = 503


class TransientError(Exception):
    """Temporary failure (network, 429, 5xx) -> worker retries."""


class PermanentError(Exception):
    """Won't succeed on retry (bad audio, no speech, bad config) -> fail fast."""


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})