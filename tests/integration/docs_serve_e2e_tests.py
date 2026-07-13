"""End-to-end docs serve test — real MkDocs dev server over HTTP.

No mocks: starts the real ``FlextInfraDocServer`` flow against a synthetic
single-scope workspace, then polls the bound address until the dev server
answers an actual HTTP request. The blocking server runs on a daemon thread
that the pytest process reaps at teardown.
"""

from __future__ import annotations

import http.client
import socket
import threading
import time
from typing import TYPE_CHECKING

from flext_infra.docs.server import FlextInfraDocServer

if TYPE_CHECKING:
    from pathlib import Path

_DEADLINE_SECONDS = 90.0
_POLL_INTERVAL_SECONDS = 0.5


def _free_local_port() -> int:
    """Reserve and release an ephemeral localhost port for the dev server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _http_get_body(host: str, port: int) -> str | None:
    """Return the response body when the dev server answers HTTP 200, else None."""
    try:
        connection = http.client.HTTPConnection(host, port, timeout=5)
        connection.request("GET", "/")
        response = connection.getresponse()
        body = (
            response.read().decode("utf-8", errors="replace")
            if response.status == 200
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
            "# Demo\n\nHello from the real dev server.\n",
            encoding="utf-8",
        )
        (tmp_path / "mkdocs.yml").write_text(
            "site_name: Flext Demo Docs\n",
            encoding="utf-8",
        )
        port = _free_local_port()
        dev_addr = f"127.0.0.1:{port}"
        outcome: dict[str, object] = {}

        def _run_server() -> None:
            outcome["result"] = FlextInfraDocServer(
                dev_addr=dev_addr,
                livereload=False,
                strict=False,
            ).serve(tmp_path)

        thread = threading.Thread(target=_run_server, daemon=True)
        thread.start()
        deadline = time.monotonic() + _DEADLINE_SECONDS
        body: str | None = None
        while body is None and time.monotonic() < deadline:
            body = _http_get_body("127.0.0.1", port)
            if body is None:
                time.sleep(_POLL_INTERVAL_SECONDS)

        assert body is not None, (
            f"dev server at {dev_addr} did not answer HTTP 200 within "
            f"{_DEADLINE_SECONDS:.0f}s"
        )
        assert "Flext Demo Docs" in body
        assert "Hello from the real dev server." in body
