from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.dependencies import check_database
from src.routers import authors, books, loans, readers
from src.services.base import (
    ConflictError,
    DatabaseUnavailableError,
    NotFoundError,
    ServiceError,
)

app = FastAPI(title="Библиотека", version="1.0.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(authors.router)
app.include_router(books.router)
app.include_router(readers.router)
app.include_router(loans.router)


@app.exception_handler(ServiceError)
async def handle_service_error(_request: Request, error: ServiceError) -> JSONResponse:
    status_codes = {
        NotFoundError: 404,
        ConflictError: 409,
        DatabaseUnavailableError: 503,
    }
    return JSONResponse(
        status_code=status_codes[type(error)], content={"detail": str(error)}
    )


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", dependencies=[Depends(check_database)])
def ready() -> dict[str, str]:
    return {"status": "ok"}
