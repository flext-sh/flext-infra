"""Public build-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.builder import FlextInfraDocBuilder
from tests import c
from tests import u
from flext_tests import tm

from pathlib import Path



def test_build_returns_root_and_selected_project_reports(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = FlextInfraDocBuilder().build(
        workspace, projects=["flext-a"], output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR
    )

    tm.ok(result)
    tm.that([report.scope for report in result.value], eq=["root", "flext-a"])
    assert all(report.result == "SKIP" for report in result.value)


def test_build_uses_custom_output_dir(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    result = FlextInfraDocBuilder().build(
        workspace, projects=["flext-a"], output_dir=".custom-docs"
    )

    tm.ok(result)
    assert (workspace / ".custom-docs/build-report.md").exists()
    assert (workspace / "flext-a/.custom-docs/build-report.md").exists()


def test_build_skip_report_has_empty_site_dir(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder().build(workspace)

    tm.ok(result)
    tm.that(result.value[0].site_dir, eq="")
