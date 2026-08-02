"""End-to-end docs serve test — real MkDocs dev server over HTTP.

No mocks: starts the real ``FlextInfraDocServer`` flow against a synthetic
single-scope workspace, then polls the bound address until the dev server
answers an actual HTTP request. The blocking server runs on a daemon thread
that the pytest process reaps at teardown.
"""

from __future__ import annotations

import http.client
import multiprocessing
import socket
import time
from typing import TYPE_CHECKING

from flext_infra.docs.server import FlextInfraDocServer
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path

_DEADLINE_SECONDS = 6.0
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


def _serve_docs(root: Path, dev_addr: str) -> None:
    FlextInfraDocServer(dev_addr=dev_addr, livereload=False, strict=False).serve(root)


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
        process = multiprocessing.get_context("fork").Process(
            target=_serve_docs, args=(tmp_path, dev_addr)
        )
        process.start()
        try:
            deadline = time.monotonic() + _DEADLINE_SECONDS
            body: str | None = None
            while body is None and time.monotonic() < deadline:
                body = _http_get_body("127.0.0.1", port)

            tm.that(body, none=False)
            tm.that(body, has="Flext Demo Docs")
            tm.that(body, has="Hello from the real dev server.")
        finally:
            process.terminate()
            process.join(timeout=2)
            if process.is_alive():
                process.kill()
                process.join()
