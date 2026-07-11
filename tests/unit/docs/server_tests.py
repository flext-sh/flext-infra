"""Behavior tests for FlextInfraDocServer — single-scope serve selection.

Real workspace fixtures only (no mocks): the serve phase resolves governed
scopes, keeps the ones carrying an ``mkdocs.yml``, and refuses ambiguous
multi-scope previews — the blocking dev-server call itself is covered by the
integration suite (tests/integration/docs_serve_e2e_tests.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.server import FlextInfraDocServer
from flext_infra.utilities import u
from tests.constants import c
from tests.models import m
from tests.utilities import u as tu

if TYPE_CHECKING:
    from pathlib import Path


def _write_mkdocs_yml(scope_path: Path) -> None:
    (scope_path / "mkdocs.yml").write_text(
        "site_name: Demo\ndocs_dir: docs\n",
        encoding="utf-8",
    )


class TestsFlextInfraDocServer:
    """FlextInfraDocServer public-behavior tests (unit under test: docs serve)."""

    class TestScopeSelection:
        """Scope resolution governs which site a blocking preview may serve."""

        def test_serve_without_mkdocs_yml_fails_with_guidance(
            self,
            tmp_path: Path,
        ) -> None:
            workspace = tu.Tests.create_docs_workspace(tmp_path)

            result = FlextInfraDocServer().serve(workspace)

            assert result.failure
            assert "mkdocs.yml" in (result.error or "")
            assert "docs generate" in (result.error or "")

        def test_serve_with_multiple_servable_scopes_requires_project(
            self,
            tmp_path: Path,
        ) -> None:
            workspace = tu.Tests.create_docs_workspace(
                tmp_path,
                project_names=("flext-a", "flext-b"),
            )
            _write_mkdocs_yml(workspace)
            _write_mkdocs_yml(workspace / "flext-a")

            result = FlextInfraDocServer().serve(workspace)

            assert result.failure
            assert "--project" in (result.error or "")
            assert "flext-a" in (result.error or "")

        def test_execute_propagates_selection_failure(self, tmp_path: Path) -> None:
            workspace = tu.Tests.create_docs_workspace(tmp_path)

            result = FlextInfraDocServer(workspace_root=workspace).execute()

            assert result.failure

    class TestRequestDefaults:
        """The public request model ships production-safe serve defaults."""

        def test_default_bind_address_is_localhost(self) -> None:
            server = FlextInfraDocServer()
            assert server.dev_addr == "127.0.0.1:8000"
            assert server.livereload
            assert server.strict

        def test_output_dir_default_matches_docs_pipeline(self) -> None:
            server = FlextInfraDocServer()
            assert str(server.output_dir) == c.Infra.DEFAULT_DOCS_OUTPUT_DIR

    class TestServeUtility:
        """u.Infra.docs_serve_mkdocs degrades to a SKIP report without mkdocs.yml."""

        def test_serve_scope_without_mkdocs_yml_returns_skip(
            self,
            tmp_path: Path,
        ) -> None:
            scope = m.Infra.DocScope(
                name="flext-demo",
                path=tmp_path,
                report_dir=tmp_path / ".reports/docs",
            )

            report = u.Infra.docs_serve_mkdocs(
                scope,
                dev_addr="127.0.0.1:18000",
                livereload=False,
                strict=True,
            )

            assert report.phase == "serve"
            assert report.result == "SKIP"
            assert report.passed
