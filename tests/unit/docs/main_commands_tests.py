"""Public service execution tests for docs commands."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    FlextInfraDocAuditor,
    FlextInfraDocBuilder,
    FlextInfraDocFixer,
    FlextInfraDocGenerator,
    FlextInfraDocValidator,
)
from tests import u


def test_auditor_execute_fails_in_strict_mode_on_broken_links(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)
    (workspace / "docs/README.md").write_text(
        "# Docs\n\n[Broken](missing.md)\n",
        encoding="utf-8",
    )

    result = FlextInfraDocAuditor(
        workspace=workspace,
        strict_mode=True,
    ).execute()

    assert result.failure


def test_fixer_execute_applies_link_and_toc_updates(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        include_fixable_link=True,
    )

    result = FlextInfraDocFixer(
        workspace=workspace,
        apply=True,
    ).execute()

    assert result.success
    content = (workspace / "docs/README.md").read_text(encoding="utf-8")
    assert "guides/setup.md" in content
    assert "<!-- TOC START -->" in content


def test_generator_execute_writes_reports_for_root_and_selected_project(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = FlextInfraDocGenerator(
        workspace=workspace,
        selected_projects=["flext-a"],
        apply=True,
    ).execute()

    assert result.success
    assert (workspace / ".reports/docs/generate-report.md").exists()
    assert (workspace / "flext-a/.reports/docs/generate-report.md").exists()
    assert not (workspace / "flext-b/.reports/docs/generate-report.md").exists()


def test_validator_execute_fails_before_generation_and_succeeds_after(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    before = FlextInfraDocValidator(
        workspace=workspace,
        selected_projects=["flext-a"],
    ).execute()
    assert before.failure
    generated = FlextInfraDocGenerator(
        workspace=workspace,
        selected_projects=["flext-a"],
        apply=True,
    ).execute()
    assert generated.success
    after = FlextInfraDocValidator(
        workspace=workspace,
        selected_projects=["flext-a"],
        apply=True,
    ).execute()
    assert after.success
    assert (workspace / "flext-a/TODOS.md").exists()


def test_builder_execute_skips_when_mkdocs_is_missing(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder(workspace=workspace).execute()

    assert result.success
    assert (workspace / ".reports/docs/build-report.md").exists()


def test_builder_execute_fails_with_invalid_mkdocs_config(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_docs_workspace(tmp_path)
    (workspace / "mkdocs.yml").write_text("site_name: [", encoding="utf-8")

    result = FlextInfraDocBuilder(workspace=workspace).execute()

    assert result.failure
