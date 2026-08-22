"""End-to-end docs serve test — real MkDocs dev server over HTTP.

No mocks: starts the real ``FlextInfraDocServer`` flow against a synthetic
single-scope workspace, then polls the bound address until the dev server
answers an actual HTTP request. The blocking server runs in a managed child
process that the test terminates and joins at teardown.
"""

from __future__ import annotations

import http.client
import multiprocessing
import socket
import time
from typing import TYPE_CHECKING

import pytest
from flext_infra import config
from flext_infra.docs.server import FlextInfraDocServer
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

_PYTEST_POLICY = config.Infra.tooling.tools.pytest
# A real MkDocs dev server cold-starts a fresh interpreter and builds the
# site; under full-suite xdist contention that legitimately exceeds the
# per-case budget, so the scenario declares the config-owned slow budget
# (pytest.mark.slow below) and polls within it.
_DEADLINE_SECONDS = float(
    _PYTEST_POLICY.slow_timeout_seconds - _PYTEST_POLICY.termination_grace_seconds
)
_POLL_INTERVAL_SECONDS = 0.05
_PROCESS_STOP_TIMEOUT_SECONDS = float(_PYTEST_POLICY.termination_grace_seconds)
_HTTP_OK = 200


def _free_local_port() -> int:
    """Reserve and release an ephemeral localhost port for the dev server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _http_get_body(host: str, port: int) -> str | None:
    """Return the response body when the dev server answers HTTP 200, else None."""
    connection = http.client.HTTPConnection(host, port, timeout=0.25)
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        return (
            response.read().decode("utf-8", errors="replace")
            if response.status == _HTTP_OK
            else None
        )
    except (OSError, http.client.HTTPException):
        return None
    finally:
        connection.close()


class TestsFlextInfraIntegrationDocsServeE2e:
    """Real serve: a governed scope with mkdocs.yml answers HTTP requests."""

    @pytest.mark.slow
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
        server = FlextInfraDocServer(dev_addr=dev_addr, livereload=False, strict=False)
        process = context.Process(target=server.serve, args=(tmp_path,))
        try:
            process.start()
            deadline = time.monotonic() + _DEADLINE_SECONDS
            body: str | None = None
            while body is None and process.is_alive() and time.monotonic() < deadline:
                body = _http_get_body("127.0.0.1", port)
                if body is None:
                    time.sleep(_POLL_INTERVAL_SECONDS)

            tm.that(body, none=False, msg=f"child exit code: {process.exitcode}")
            tm.that(body, has="Flext Demo Docs")
            tm.that(body, has="Hello from the real dev server.")
        finally:
            stopped = process.pid is None
            if not stopped:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=_PROCESS_STOP_TIMEOUT_SECONDS)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=_PROCESS_STOP_TIMEOUT_SECONDS)
                stopped = not process.is_alive()
            try:
                tm.that(stopped, where=bool)
            finally:
                if stopped:
                    process.close()
