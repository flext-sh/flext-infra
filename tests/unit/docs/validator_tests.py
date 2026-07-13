"""Public validation-workflow tests for docs services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from tests import m
from tests import u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


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
            workspace_root=workspace, projects=["flext-a"], apply=False
        )
    )

    tm.ok(result)
    assert any(report.result == "FAIL" for report in result.value)


def test_validate_workspace_passes_after_generate_apply(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    generated = FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )
    tm.ok(generated)
    result = FlextInfraDocValidator().validate_workspace(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    assert all(report.result == "OK" for report in result.value)


def test_validate_workspace_apply_writes_project_todo(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    FlextInfraDocGenerator().generate(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )
    result = FlextInfraDocValidator().validate_workspace(
        m.Infra.DocsGenerateRequest(
            workspace_root=workspace, projects=["flext-a"], apply=True
        )
    )

    tm.ok(result)
    assert (workspace / "flext-a/TODOS.md").exists()
