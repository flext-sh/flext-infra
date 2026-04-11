"""Public validation-workflow tests for docs services."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocGenerator, FlextInfraDocValidator
from tests import m, u


def test_validate_report_model_fields() -> None:
    report = m.Infra.DocsPhaseReport(
        phase="validate",
        scope="root",
        result="FAIL",
        message="Missing generated docs",
        missing_adr_skills=["rules-docs"],
        todo_written=False,
    )

    assert report.result == "FAIL"
    assert report.missing_adr_skills == ["rules-docs"]
    assert report.todo_written is False


def test_validate_workspace_fails_before_generated_files_exist(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = FlextInfraDocValidator().validate_workspace(
        workspace,
        projects=["flext-a"],
        apply=False,
    )

    assert result.success
    assert any(report.result == "FAIL" for report in result.value)


def test_validate_workspace_passes_after_generate_apply(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    generated = FlextInfraDocGenerator().generate(
        workspace,
        projects=["flext-a"],
        apply=True,
    )
    assert generated.success
    result = FlextInfraDocValidator().validate_workspace(
        workspace,
        projects=["flext-a"],
        apply=True,
    )

    assert result.success
    assert all(report.result == "OK" for report in result.value)


def test_validate_workspace_apply_writes_project_todo(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    FlextInfraDocGenerator().generate(
        workspace,
        projects=["flext-a"],
        apply=True,
    )
    result = FlextInfraDocValidator().validate_workspace(
        workspace,
        projects=["flext-a"],
        apply=True,
    )

    assert result.success
    assert (workspace / "flext-a/TODOS.md").exists()
