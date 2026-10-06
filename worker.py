"""Recurring discovery worker; manual draft/send commands remain separate."""
import fcntl
import os
import signal
import subprocess
import sys
from pathlib import Path
from threading import Event
from app.settings import load_env
from app.notifications import notify


def main():
    load_env()
    interval = int(os.getenv("SEARCH_INTERVAL_SECONDS", "3600"))
    if interval < 60:
        raise ValueError("Search interval must be at least 60 seconds.")
    data = Path("data")
    data.mkdir(parents=True, exist_ok=True)
    stop = Event()
    def shutdown(signum, frame):
        stop.set()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    with (data / "discovery.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another discovery worker is running.")
        notify("worker: started", {"interval_seconds": interval})
        try:
            while not stop.is_set():
                try:
                    result = subprocess.run(
                        [sys.executable, "discover_jobs.py"],
                        timeout=int(os.getenv("SEARCH_RUN_TIMEOUT_SECONDS", "600")),
                        check=False,
                    )
                    if result.returncode:
                        notify("worker: cycle failed", {"exit_code": result.returncode})
                except subprocess.TimeoutExpired:
                    notify("worker: cycle timed out")
                stop.wait(interval)
        finally:
            notify("worker: stopped")


if __name__ == "__main__":
    main()
