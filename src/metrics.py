import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import Counter, start_http_server
from starlette.concurrency import run_in_threadpool

BOOKS_CREATED = Counter(
    "library_books_created_total",
    "Number of book copies successfully added to the library.",
)
READERS_REGISTERED = Counter(
    "library_readers_registered_total",
    "Number of readers successfully registered.",
)
LOANS_CREATED = Counter(
    "library_loans_created_total",
    "Number of loan records successfully created.",
)
LOANS_RETURNED = Counter(
    "library_loans_returned_total",
    "Number of successful transitions from an active loan to a returned loan.",
)


@asynccontextmanager
async def metrics_lifespan(_app: FastAPI):
    server, thread = start_http_server(int(os.getenv("METRICS_PORT", "8001")))
    try:
        yield
    finally:
        await run_in_threadpool(server.shutdown)
        server.server_close()
        await run_in_threadpool(thread.join)


BUSINESS_ATTEMPTS = Counter(
    "library_business_attempts_total",
    "Completed eligible business attempts.",
    ["operation"],
)
for operation in ("books", "readers", "loans"):
    BUSINESS_ATTEMPTS.labels(operation=operation)
