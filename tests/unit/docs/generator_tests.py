"""Public generation-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.generator import FlextInfraDocGenerator
from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def test_generate_returns_reports_for_root_and_selected_project(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=False
        )
    )

    tm.ok(result)
    tm.that([report.scope for report in result.value], eq=["root", "flext-a"])


def test_generate_apply_writes_summary_and_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    assert (workspace / ".reports/docs/generate-summary.json").exists()
    assert (workspace / ".reports/docs/generate-report.md").exists()
    assert (workspace / "flext-a/.reports/docs/generate-report.md").exists()


def test_generate_dry_run_marks_report_as_warn(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(workspace_root=workspace, apply=False)
    )

    tm.ok(result)
    tm.that(result.value[0].result, eq="WARN")


def test_generated_file_model_is_frozen() -> None:
    tm.that(m.Infra.GeneratedFile.model_config.get("frozen"), eq=True)


def test_generate_report_tracks_written_files() -> None:
    report = m.Infra.DocsPhaseReport(
        phase="generate",
        scope="root",
        generated=2,
        applied=True,
        source="code-docstring-ssot",
        items=[
            m.Infra.DocsPhaseItemModel(
                phase="generate", path="docs/a.md", written=True
            ),
            m.Infra.DocsPhaseItemModel(
                phase="generate", path="docs/b.md", written=False
            ),
        ],
    )

    tm.that(report.generated, eq=2)
    tm.that(len(report.items), eq=2)
