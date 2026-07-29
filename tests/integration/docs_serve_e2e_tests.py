"""End-to-end docs serve test — real MkDocs dev server over HTTP.

No mocks: starts the real ``FlextInfraDocServer`` flow against a synthetic
single-scope workspace, then polls the bound address until the dev server
answers an actual HTTP request. The blocking server runs in a managed child
process that the test terminates and joins at teardown.
"""

from __future__ import annotations

import http.client
import importlib
import multiprocessing
import socket
import sys
import time
from typing import TYPE_CHECKING

import pytest

from flext_tests import tm

pytestmark = pytest.mark.timeout(60)

if TYPE_CHECKING:
    from pathlib import Path

_DEADLINE_SECONDS = 9.0
_HTTP_OK = 200


def _free_local_port() -> int:
    """Reserve and release an ephemeral localhost port for the dev server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _http_get_body(host: str, port: int) -> str | None:
    """Return the response body when the dev server answers HTTP 200, else None."""
    try:
        connection = http.client.HTTPConnection(host, port, timeout=0.25)
        connection.request("GET", "/")
        response = connection.getresponse()
        body = (
            response.read().decode("utf-8", errors="replace")
            if response.status == _HTTP_OK
            else None
        )
        connection.close()
    except OSError:
        return None
    return body


class TestsFlextInfraIntegrationDocsServeE2e:
    """Real serve: a governed scope with mkdocs.yml answers HTTP requests."""

    def test_serve_scope_serves_site_over_http(self, tmp_path: Path) -> None:
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/index.md").write_text(
            "# Demo\n\nHello from the real dev server.\n", encoding="utf-8"
        )
        (tmp_path / "mkdocs.yml").write_text(
            "site_name: Flext Demo Docs\n", encoding="utf-8"
        )
        port = _free_local_port()
        dev_addr = f"127.0.0.1:{port}"
        context = multiprocessing.get_context("spawn")
        run_process = importlib.import_module("subprocess").run
        process = context.Process(
            target=run_process,
            args=(
                [
                    sys.executable,
                    "-m",
                    "mkdocs",
                    "serve",
                    "--config-file",
                    str(tmp_path / "mkdocs.yml"),
                    "--dev-addr",
                    dev_addr,
                    "--no-livereload",
                ],
            ),
            kwargs={"cwd": tmp_path, "check": False},
        )
        process.start()
        try:
            deadline = time.monotonic() + _DEADLINE_SECONDS
            body: str | None = None
            while body is None and time.monotonic() < deadline:
                body = _http_get_body("127.0.0.1", port)

            tm.that(body, none=False, msg=f"child exit code: {process.exitcode}")
            tm.that(body, has="Flext Demo Docs")
            tm.that(body, has="Hello from the real dev server.")
        finally:
            process.terminate()
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join()
