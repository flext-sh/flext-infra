"""Public validation-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_tests import tm
from tests import m, u

if TYPE_CHECKING:
    from pathlib import Path


def _publish_docs(workspace: Path) -> None:
    """Publish one generated docs bundle through the transaction adapter."""
    generator = FlextInfraDocGenerator(
        repository_root=workspace, selected_projects=["flext-a"]
    )
    prepared = generator.prepare_bundle()
    tm.ok(prepared)
    required = generator.required_directories(prepared.value)
    tm.ok(required)
    for directory in required.value:
        directory.mkdir(parents=True, exist_ok=True)
    planned = generator.plan_files(prepared.value)
    tm.ok(planned)
    published = u.Tests.materialize_codegen_plans(
        r[tuple[m.Infra.CodegenFilePlan, ...]].ok(planned.value)
    )
    tm.ok(published)


def test_validate_report_model_fields() -> None:
    report = m.Infra.DocsPhaseReport(
        phase="validate",
        scope="root",
        result="FAIL",
        message="Missing generated docs",
        missing_adr_skills=["rules-docs"],
        todo_written=False,
    )

    tm.that(report.result, eq="FAIL")
    tm.that(report.missing_adr_skills, eq=["rules-docs"])
    tm.that(report.todo_written, eq=False)


def test_validate_workspace_fails_before_generated_files_exist(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    result = FlextInfraDocValidator().validate_workspace(
        m.Infra.DocsGenerateRequest(
            repository_root=workspace, projects=["flext-a"], apply=False
        )
    )

    tm.ok(result)
    tm.that(any(report.result == "FAIL" for report in result.value), eq=True)


def test_validate_workspace_passes_after_generate_apply(tmp_path: Path) -> None:
    """Validation passes once the generated bundle is published."""
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    _publish_docs(workspace)
    result = FlextInfraDocValidator().validate_workspace(
        m.Infra.DocsGenerateRequest(
            repository_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    tm.that(all(report.result == "OK" for report in result.value), eq=True)


def test_validate_workspace_apply_writes_project_todo(tmp_path: Path) -> None:
    """Applied validation writes the project TODO ledger."""
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    _publish_docs(workspace)
    result = FlextInfraDocValidator().validate_workspace(
        m.Infra.DocsGenerateRequest(
            repository_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    tm.that((workspace / "flext-a/TODOS.md").exists(), eq=True)
