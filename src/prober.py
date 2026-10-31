import json
import os
import signal
import time
import uuid
from datetime import date, timedelta
from http.client import HTTPException
from threading import Event
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from prometheus_client import Counter, Gauge, start_http_server

ATTEMPTS = Counter("library_probe_attempts_total", "Completed business journeys.")
SUCCESSES = Counter(
    "library_probe_successes_total", "Successfully verified business journeys."
)
SUCCESS = Gauge("library_probe_success", "Last business journey result.")
DURATION = Gauge(
    "library_probe_duration_seconds", "Last journey duration including cleanup."
)
LAST_CHECK = Gauge(
    "library_probe_last_check_timestamp_seconds", "Last completion timestamp."
)
CLEANUP_ERRORS = Counter(
    "library_probe_cleanup_errors_total", "Failed cleanup requests."
)
ERRORS = (HTTPError, URLError, HTTPException, OSError, ValueError, KeyError, TypeError)


def api(base, method, path, timeout, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        base.rstrip("/") + "/api/" + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        expected = {"POST": 201, "GET": 200, "DELETE": 204}[method]
        if response.status != expected:
            raise ValueError("Unexpected API status")
        return json.load(response) if method != "DELETE" else None


def probe_once(url: str, timeout: float) -> bool:
    started = time.monotonic()
    created = []
    success = False

    def create(resource, payload):
        result = api(url, "POST", resource, timeout, payload)

        item_id = result["id"]
        if type(item_id) is not int or item_id <= 0:
            raise ValueError("Invalid object ID")

        path = f"{resource}/{item_id}"
        created.append(path)

        stored = api(url, "GET", path, timeout)
        if any(stored.get(key) != value for key, value in payload.items()):
            raise ValueError("Stored business data differs from requested data")

        return item_id

    try:
        token = uuid.uuid4()
        author = create("authors", {"first_name": "SLO", "last_name": "Probe"})
        book = create(
            "books",
            {
                "title": "SLO probe",
                "isbn": "SLO-test",
                "inventory_number": f"slo-{token.hex}",
                "author_id": author,
            },
        )
        reader = create(
            "readers",
            {
                "first_name": "SLO",
                "last_name": "Probe",
                "phone": "+9" + str(token.int % 10**13).zfill(13),
            },
        )
        today = date.today()
        create(
            "loans",
            {
                "book_id": book,
                "reader_id": reader,
                "issued_on": today.isoformat(),
                "due_on": (today + timedelta(days=7)).isoformat(),
            },
        )
        success = True
    except ERRORS:
        pass
    finally:
        for path in reversed(created):
            try:
                api(url, "DELETE", path, timeout)
            except ERRORS:
                CLEANUP_ERRORS.inc()

        ATTEMPTS.inc()

        if success:
            SUCCESSES.inc()

        SUCCESS.set(int(success))
        DURATION.set(time.monotonic() - started)
        LAST_CHECK.set(time.time())

    return success


def main() -> None:
    url = os.getenv("PROBE_URL", "http://library.library.svc.cluster.local")
    interval = float(os.getenv("PROBE_INTERVAL_SECONDS", "15"))
    timeout = float(os.getenv("PROBE_TIMEOUT_SECONDS", "3"))

    if interval <= 0 or timeout <= 0:
        raise ValueError("Probe interval and timeout must be positive")

    stopped = Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopped.set())

    server, thread = start_http_server(int(os.getenv("METRICS_PORT", "8001")))

    try:
        while not stopped.is_set():
            started = time.monotonic()
            probe_once(url, timeout)
            stopped.wait(max(0, interval - (time.monotonic() - started)))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    main()
