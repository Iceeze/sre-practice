import os
from functools import wraps

from src.metrics import BUSINESS_ATTEMPTS
from src.services.base import ConflictError, DatabaseUnavailableError, NotFoundError


def business_operation(operation):
    def decorate(function):
        @wraps(function)
        def measured(*args, **kwargs):
            eligible = True
            try:
                if os.getenv("SLO_DEMO_FAIL", "") in (operation, "all"):
                    raise DatabaseUnavailableError(
                        "SLO demonstration: operation unavailable"
                    )
                return function(*args, **kwargs)
            except (ConflictError, NotFoundError):
                eligible = False
                raise
            finally:
                if eligible:
                    BUSINESS_ATTEMPTS.labels(operation=operation).inc()

        return measured

    return decorate
