import logging
from time import perf_counter

import structlog
from fastapi import Request

logger = structlog.get_logger("library.http")


async def log_requests(request: Request, call_next):
    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        if status >= 400 or request.url.path not in ("/health/live", "/health/ready"):
            level = (
                logging.ERROR if status >= 500
                else logging.WARNING if status >= 400
                else logging.INFO
            )
            logger.log(
                level,
                "HTTP request",
                **{
                    "http.method": request.method,
                    "http.path": request.url.path,
                    "http.status_code": status,
                    "duration_ms": round((perf_counter() - started) * 1000, 3),
                },
            )
