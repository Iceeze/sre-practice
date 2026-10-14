import os
import traceback

import structlog


def exception_summary(exc_info) -> str:
    """Exception type and stack locations, without private values or SQL text."""
    frames = traceback.extract_tb(exc_info[2])
    return "\n".join(
        [exc_info[0].__name__]
        + [f"{frame.filename}:{frame.lineno} in {frame.name}" for frame in frames]
    )


def add_service(_logger, _method, event: dict) -> dict:
    event["service.name"] = os.getenv("SERVICE_NAME", "library")
    return event


def json_formatter() -> structlog.stdlib.ProcessorFormatter:
    structlog.configure(
        processors=[
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )
    return structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            add_service,
            structlog.processors.ExceptionRenderer(exception_summary),
            structlog.processors.EventRenamer("message"),
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
    )


def logging_config() -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": "src.logging_config.json_formatter"}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json",
            }
        },
        "root": {"handlers": ["stdout"], "level": os.getenv("LOG_LEVEL", "INFO")},
        "loggers": {
            "uvicorn": {"handlers": [], "propagate": True},
            "uvicorn.error": {
                "handlers": [],
                "propagate": True,
            },
        },
    }
