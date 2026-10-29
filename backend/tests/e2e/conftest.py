import os
import re
import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx2
import pytest
from sqlalchemy import create_engine, make_url, text

from tests.conftest import TEST_DATABASE_URL

BACKEND_DIR = Path(__file__).resolve().parents[2]
CSRF_COOKIE = "dateno_csrf"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class Server:
    def __init__(self, base_url: str, log_path: Path):
        self.base_url = base_url
        self.log_path = log_path

    def last_emailed_code(self, email: str, after: int = 0) -> str:
        """Waits for the `after + 1`-th email to `email` and returns its code.

        In local mode the console mailer writes emails to the server log, like in
        development. Emails go out in a background task after the response, so poll.
        """
        pattern = re.compile(rf"Email to {re.escape(email)} \|.*?\n.*?\b(\d{{6}})\b", re.S)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            codes = pattern.findall(self.log_path.read_text(encoding="utf-8"))
            if len(codes) > after:
                return codes[-1]
            time.sleep(0.05)
        raise AssertionError(f"no emailed code for {email} in server log")

    def client(self) -> httpx2.Client:
        """A browser-like client: keeps cookies and echoes the CSRF cookie as a header."""
        client = httpx2.Client(base_url=self.base_url, timeout=10)
        client.get("/api/health").raise_for_status()
        client.headers["X-CSRF-Token"] = client.cookies[CSRF_COOKIE]
        return client


@contextmanager
def _fresh_database(workdir: Path) -> Iterator[str]:
    if not TEST_DATABASE_URL.startswith("postgresql"):
        yield f"sqlite:///{workdir / 'e2e.db'}"
        return

    # A dedicated database proves the migrations work from empty, independent of other tests.
    name = f"dateno_e2e_{uuid.uuid4().hex[:8]}"
    admin_url = make_url(TEST_DATABASE_URL)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    try:
        yield admin_url.set(database=name).render_as_string(hide_password=False)
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture(scope="session")
def server(tmp_path_factory) -> Iterator[Server]:
    workdir = tmp_path_factory.mktemp("e2e")
    with _fresh_database(workdir) as database_url:
        yield from _run_server(workdir, database_url)


def _run_server(workdir: Path, database_url: str) -> Iterator[Server]:
    port = _free_port()
    env = {
        **os.environ,
        "APP_ENV": "local",
        "DATABASE_URL": database_url,
        "SECRET_KEY": "e2e-secret",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
    }

    # Build the schema the same way production does: through the Alembic migrations.
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        check=True,
        capture_output=True,
    )

    log_path = workdir / "server.log"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
            cwd=BACKEND_DIR,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        base_url = f"http://127.0.0.1:{port}"
        try:
            _wait_until_healthy(base_url, process, log_path)
            yield Server(base_url, log_path)
        finally:
            process.terminate()
            process.wait(timeout=10)


def _wait_until_healthy(base_url: str, process: subprocess.Popen, log_path: Path) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"server exited early:\n{log_path.read_text(encoding='utf-8')}")
        try:
            if httpx2.get(f"{base_url}/api/health", timeout=1).status_code == 200:
                return
        except httpx2.TransportError:
            time.sleep(0.2)
    raise RuntimeError(f"server not healthy in time:\n{log_path.read_text(encoding='utf-8')}")
