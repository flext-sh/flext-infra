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
    """Return reports for the workspace root and selected project."""
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
    """Write summary and report artifacts during applied generation."""
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    tm.that((workspace / ".reports/docs/generate-summary.json").exists(), eq=True)
    tm.that((workspace / ".reports/docs/generate-report.md").exists(), eq=True)
    tm.that((workspace / "flext-a/.reports/docs/generate-report.md").exists(), eq=True)


def test_generate_preserves_declared_export_order_and_is_idempotent(
    tmp_path: Path,
) -> None:
    """Preserve declared export order across repeated generation."""
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
    project = workspace / "flext-a"
    package = project / "src/flext_a"
    (package / "alpha.py").write_text(
        '"""Alpha exports."""\n\nclass FlextAAlpha:\n    """Alpha facade."""\n',
        encoding="utf-8",
    )
    (package / "beta.py").write_text(
        '"""Beta exports."""\n\nclass FlextABeta:\n    """Beta facade."""\n',
        encoding="utf-8",
    )
    (package / "__init__.py").write_text(
        "from flext_a.beta import FlextABeta\n"
        "from flext_a.alpha import FlextAAlpha\n\n"
        '__all__ = ["FlextAAlpha", "FlextABeta"]\n',
        encoding="utf-8",
    )
    request = m.Infra.DocsGenerateRequest(
        workspace_root=workspace, projects=["flext-a"], apply=True
    )
    generator = FlextInfraDocGenerator()

    first = generator.generate(request)
    tm.ok(first)
    first_readme = (project / "README.md").read_text(encoding="utf-8")
    tm.that(
        first_readme.index("FlextAAlpha") < first_readme.index("FlextABeta"), eq=True
    )

    second = generator.generate(request)
    tm.ok(second)
    tm.that(second.value[1].generated, eq=0)
    tm.that((project / "README.md").read_text(encoding="utf-8"), eq=first_readme)


def test_generate_dry_run_marks_report_as_warn(tmp_path: Path) -> None:
    """Mark dry-run generation reports as warnings."""
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(workspace_root=workspace, apply=False)
    )

    tm.ok(result)
    tm.that(result.value[0].result, eq="WARN")


def test_generated_file_model_is_frozen() -> None:
    """Keep generated-file report models immutable."""
    tm.that(m.Infra.GeneratedFile.model_config.get("frozen"), eq=True)


def test_generate_report_tracks_written_files() -> None:
    """Track written files in generation phase reports."""
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
