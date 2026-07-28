"""Public generation-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from tests import m, u

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


def test_root_generated_catalog_survives_project_pass_and_curated_indexes_are_unowned(
    tmp_path: Path,
) -> None:
    """Preserve root output while leaving optional curated indexes unowned."""
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))
    request = m.Infra.DocsGenerateRequest(
        workspace_root=workspace, projects=["flext-a"], apply=True
    )
    generator = FlextInfraDocGenerator()

    first = generator.generate(request)
    tm.ok(first)
    catalog = workspace / "docs/projects/generated/catalog.md"
    tm.that(catalog.exists(), eq=True)

    second = generator.generate(request)
    tm.ok(second)
    tm.that(catalog.exists(), eq=True)

    for relative_path in (
        "docs/README.md",
        "docs/architecture/README.md",
        "docs/guides/README.md",
        "docs/projects/README.md",
    ):
        (workspace / relative_path).unlink()
    validation = FlextInfraDocValidator().validate_workspace(request)
    tm.ok(validation)
    tm.that(all(report.result == "OK" for report in validation.value), eq=True)


def test_generated_collection_rules_pointer_stays_within_consumer_limit(
    tmp_path: Path,
) -> None:
    """Keep the generated Collection Rules pointer within the Markdown limit."""
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    result = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    lines = (
        (workspace / "flext-a/docs/index.md").read_text(encoding="utf-8").splitlines()
    )
    section_start = lines.index("## Collection Rules")
    section_end = next(
        index
        for index in range(section_start + 1, len(lines))
        if lines[index].startswith("## ")
    )
    collection_rules_lines = [line for line in lines[section_start:section_end] if line]
    tm.that(max(map(len, collection_rules_lines)), lte=240)


def test_root_catalog_survives_project_generation_and_curated_paths_are_unowned(
    tmp_path: Path,
) -> None:
    """Keep colocated root output stable without owning curated indexes."""
    workspace = tmp_path
    (workspace / "src/flext_infra_fixture").mkdir(parents=True)
    (workspace / "src/flext_infra_fixture/__init__.py").write_text(
        'def fixture_entry() -> str:\n    return "fixture"\n\n__all__ = ["fixture_entry"]\n',
        encoding="utf-8",
    )
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "flext-infra-fixture"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (workspace / "Makefile").write_text("test:\n\t@true\n", encoding="utf-8")
    for relative_path in (
        "README.md",
        "docs/README.md",
        "docs/index.md",
        "docs/architecture/README.md",
        "docs/guides/README.md",
        "docs/projects/README.md",
        "docs/api-reference/README.md",
    ):
        path = workspace / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Docs\n", encoding="utf-8")
    request = m.Infra.DocsGenerateRequest(
        workspace_root=workspace, projects=["flext-infra-fixture"], apply=True
    )
    generator = FlextInfraDocGenerator()

    scopes = u.Infra.build_scopes(workspace, None, c.Infra.DEFAULT_DOCS_OUTPUT_DIR)
    tm.ok(scopes)
    tm.that([scope.name for scope in scopes.value], eq=["root", "flext-infra-fixture"])
    tm.that(scopes.value[0].path.resolve(), eq=scopes.value[1].path.resolve())

    generated = generator.generate(request)
    tm.ok(generated)
    catalog = workspace / "docs/projects/generated/catalog.md"
    tm.that(catalog.exists(), eq=True)
    stale = workspace / "docs/api-reference/generated/stale.md"
    stale.write_text("stale\n", encoding="utf-8")
    generator.generate(request)
    tm.that(stale.exists(), eq=False)
    first_output = catalog.read_bytes()

    for relative_path in (
        "docs/README.md",
        "docs/architecture/README.md",
        "docs/projects/README.md",
    ):
        (workspace / relative_path).unlink()
    validation = FlextInfraDocValidator().validate_workspace(request)
    tm.ok(validation)
    for report in validation.value:
        tm.that(report.result, eq="OK")
    generator.generate(request)
    tm.that(catalog.read_bytes(), eq=first_output)


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
