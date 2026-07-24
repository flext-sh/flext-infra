"""Behavior tests for FlextInfraDocServer — single-scope serve selection.

Real workspace fixtures only (no mocks): the serve phase resolves governed
scopes, keeps the ones carrying an ``mkdocs.yml``, and refuses ambiguous
multi-scope previews — the blocking dev-server call itself is covered by the
integration suite (tests/integration/docs_serve_e2e_tests.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.docs.server import FlextInfraDocServer
from flext_infra.utilities import u
from tests import c, m, u as tu

if TYPE_CHECKING:
    from pathlib import Path


def _write_mkdocs_yml(scope_path: Path) -> None:
    (scope_path / "mkdocs.yml").write_text(
        "site_name: Demo\ndocs_dir: docs\n", encoding="utf-8"
    )


class TestsFlextInfraDocServer:
    """FlextInfraDocServer public-behavior tests (unit under test: docs serve)."""

    class TestScopeSelection:
        """Scope resolution governs which site a blocking preview may serve."""

        def test_serve_without_mkdocs_yml_fails_with_guidance(
            self, tmp_path: Path
        ) -> None:
            workspace = tu.Tests.create_docs_workspace(tmp_path)

            result = FlextInfraDocServer().serve(workspace)

            tm.fail(result)
            tm.that((result.error or ""), has="mkdocs.yml")
            tm.that((result.error or ""), has="docs generate")

        def test_serve_with_multiple_servable_scopes_requires_project(
            self, tmp_path: Path
        ) -> None:
            workspace = tu.Tests.create_docs_workspace(
                tmp_path, project_names=("flext-a", "flext-b")
            )
            _write_mkdocs_yml(workspace)
            _write_mkdocs_yml(workspace / "flext-a")

            result = FlextInfraDocServer().serve(workspace)

            tm.fail(result)
            tm.that((result.error or ""), has="--project")
            tm.that((result.error or ""), has="flext-a")

        def test_execute_propagates_selection_failure(self, tmp_path: Path) -> None:
            workspace = tu.Tests.create_docs_workspace(tmp_path)

            result = FlextInfraDocServer(workspace_root=workspace).execute()

            tm.fail(result)

    class TestRequestDefaults:
        """The public request model ships production-safe serve defaults."""

        def test_default_bind_address_is_localhost(self) -> None:
            server = FlextInfraDocServer()
            tm.that(server.dev_addr, eq="127.0.0.1:8000")
            assert server.livereload
            assert server.strict

        def test_output_dir_default_matches_docs_pipeline(self) -> None:
            server = FlextInfraDocServer()
            tm.that(str(server.output_dir), eq=c.Infra.DEFAULT_DOCS_OUTPUT_DIR)

    class TestServeUtility:
        """u.Infra.docs_serve_mkdocs degrades to a SKIP report without mkdocs.yml."""

        def test_serve_scope_without_mkdocs_yml_returns_skip(
            self, tmp_path: Path
        ) -> None:
            scope = m.Infra.DocScope(
                name="flext-demo", path=tmp_path, report_dir=tmp_path / ".reports/docs"
            )

            report = u.Infra.docs_serve_mkdocs(
                scope, dev_addr="127.0.0.1:18000", livereload=False, strict=True
            )

            tm.that(report.phase, eq="serve")
            tm.that(report.result, eq="SKIP")
            assert report.passed
