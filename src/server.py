import os

import uvicorn

from src.logging_config import logging_config


def main() -> None:
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        workers=int(os.getenv("WEB_CONCURRENCY", "1")),
        log_config=logging_config(),
        access_log=False,
    )


if __name__ == "__main__":
    main()
