"""Public utility tests used by docs validation flows."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraDocGenerator, FlextInfraDocValidator
from tests import c, u


def test_docs_has_adr_reference_detects_marker(tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("# Skill\n\nADR: documented.\n", encoding="utf-8")

    assert u.Infra.docs_has_adr_reference(skill) is True


def test_docs_load_required_skills_reads_architecture_config(tmp_path: Path) -> None:
    config = tmp_path / "docs/architecture/architecture_config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        '{"docs_validation": {"required_skills": ["rules-docs", "readme-standardization"]}}',
        encoding="utf-8",
    )

    required = u.Infra.docs_load_required_skills(tmp_path)

    assert required == ["rules-docs", "readme-standardization"]


def test_docs_write_todo_writes_only_for_project_scopes(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )
    scopes = u.Infra.build_scopes(
        workspace,
        projects=["flext-a"],
        output_dir=c.Infra.DEFAULT_DOCS_OUTPUT_DIR,
    )

    assert scopes.success
    root_scope, project_scope = scopes.value
    assert u.Infra.docs_write_todo(root_scope, apply_mode=True) is False
    assert u.Infra.docs_write_todo(project_scope, apply_mode=True) is True
    assert (workspace / "flext-a/TODOS.md").exists()


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
