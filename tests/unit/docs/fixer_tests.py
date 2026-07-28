"""Public fix-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_tests import tm
from tests import c, m, u

if TYPE_CHECKING:
    from pathlib import Path


def test_fix_returns_reports_for_root_and_selected_project(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b"), include_fixable_link=True
    )

    result = FlextInfraDocFixer().fix(workspace, projects=["flext-a"], apply=False)

    tm.ok(result)
    tm.that([report.scope for report in result.value], eq=["root", "flext-a"])


def test_fix_apply_updates_docs_file_and_writes_reports(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)

    result = FlextInfraDocFixer().fix(workspace, apply=True)

    tm.ok(result)
    tm.that((workspace / "docs/README.md").read_text(), has="guides/setup.md")
    tm.that((workspace / ".reports/docs/fix-report.md").exists(), eq=True)


def test_fix_check_apply_check_converges(tmp_path: Path) -> None:
    """Fail on unapplied drift, apply it, then pass at the fixed point."""
    workspace = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)
    fixer = FlextInfraDocFixer()

    check = fixer.fix(workspace, apply=False)
    tm.ok(check)
    tm.that(check.value[0].result, eq=c.Infra.ResultStatus.FAIL)
    tm.that(check.value[0].passed, eq=False)
    tm.that(check.value[0].changed_files, gt=0)

    applied = fixer.fix(workspace, apply=True)
    tm.ok(applied)
    tm.that(applied.value[0].result, eq=c.Infra.ResultStatus.OK)
    tm.that(applied.value[0].passed, eq=True)

    fixed_point = fixer.fix(workspace, apply=False)
    tm.ok(fixed_point)
    tm.that(fixed_point.value[0].result, eq=c.Infra.ResultStatus.OK)
    tm.that(fixed_point.value[0].passed, eq=True)
    tm.that(fixed_point.value[0].changed_files, eq=0)


def test_fix_item_model_tracks_link_and_toc_counts() -> None:
    item = m.Infra.DocsPhaseItemModel(phase="fix", file="README.md", links=2, toc=1)

    tm.that(item.file, eq="README.md")
    tm.that(item.links, eq=2)
    tm.that(item.toc, eq=1)
