"""Public build-workflow tests for docs services."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocBuilder
from tests import c, u


def test_build_returns_root_and_selected_project_reports(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = FlextInfraDocBuilder().build(
        workspace,
        projects=["flext-a"],
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert result.is_success
    assert [report.scope for report in result.value] == ["root", "flext-a"]
    assert all(report.result == "SKIP" for report in result.value)


def test_build_uses_custom_output_dir(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = FlextInfraDocBuilder().build(
        workspace,
        projects=["flext-a"],
        output_dir=".custom-docs",
    )

    assert result.is_success
    assert (workspace / ".custom-docs/build-report.md").exists()
    assert (workspace / "flext-a/.custom-docs/build-report.md").exists()


def test_build_skip_report_has_empty_site_dir(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder().build(workspace)

    assert result.is_success
    assert result.value[0].site_dir == ""
