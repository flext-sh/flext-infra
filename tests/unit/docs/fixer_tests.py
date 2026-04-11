"""Public fix-workflow tests for docs services."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocFixer
from tests import m, u


def test_fix_returns_reports_for_root_and_selected_project(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        include_fixable_link=True,
    )

    result = FlextInfraDocFixer().fix(
        workspace,
        projects=["flext-a"],
        apply=False,
    )

    assert result.success
    assert [report.scope for report in result.value] == ["root", "flext-a"]


def test_fix_apply_updates_docs_file_and_writes_reports(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        include_fixable_link=True,
    )

    result = FlextInfraDocFixer().fix(workspace, apply=True)

    assert result.success
    assert "guides/setup.md" in (workspace / "docs/README.md").read_text()
    assert (workspace / ".reports/docs/fix-report.md").exists()


def test_fix_report_warns_without_apply_when_changes_exist(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        include_fixable_link=True,
    )

    result = FlextInfraDocFixer().fix(workspace, apply=False)

    assert result.success
    assert result.value[0].result == "WARN"


def test_fix_item_model_tracks_link_and_toc_counts() -> None:
    item = m.Infra.DocsPhaseItemModel(
        phase="fix",
        file="README.md",
        links=2,
        toc=1,
    )

    assert item.file == "README.md"
    assert item.links == 2
    assert item.toc == 1
