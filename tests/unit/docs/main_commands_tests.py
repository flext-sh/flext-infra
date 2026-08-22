"""Public service execution tests for docs commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.docs.auditor import FlextInfraDocAuditor
from flext_infra.docs.builder import FlextInfraDocBuilder
from flext_infra.docs.fixer import FlextInfraDocFixer
from flext_infra.docs.generator import FlextInfraDocGenerator
from flext_infra.docs.validator import FlextInfraDocValidator
from flext_tests import tm
from tests import u

if TYPE_CHECKING:
    from pathlib import Path


def test_auditor_execute_fails_in_strict_mode_on_broken_links(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)
    (workspace / "docs/README.md").write_text(
        "# Docs\n\n[Broken](missing.md)\n", encoding="utf-8"
    )

    result = FlextInfraDocAuditor(workspace_root=workspace, strict_mode=True).execute()

    tm.fail(result)


def test_fixer_execute_applies_link_and_toc_updates(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)

    result = FlextInfraDocFixer(workspace_root=workspace, apply_changes=True).execute()

    tm.ok(result)
    content = (workspace / "docs/README.md").read_text(encoding="utf-8")
    tm.that(content, has="guides/setup.md")
    tm.that(content, has="<!-- TOC START -->")


def test_fixer_execute_fails_on_unapplied_drift(tmp_path: Path) -> None:
    """The command boundary rejects fixable docs left unapplied."""
    workspace = u.Tests.create_docs_workspace(tmp_path, include_fixable_link=True)

    result = FlextInfraDocFixer(workspace_root=workspace).execute()

    tm.fail(result)


def test_generator_execute_writes_reports_for_root_and_selected_project(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_docs_workspace(
        tmp_path, project_names=("flext-a", "flext-b")
    )

    result = FlextInfraDocGenerator(
        workspace_root=workspace, selected_projects=["flext-a"], apply_changes=True
    ).execute()

    tm.ok(result)
    tm.that((workspace / ".reports/docs/generate-report.md").exists(), eq=True)
    tm.that((workspace / "flext-a/.reports/docs/generate-report.md").exists(), eq=True)
    tm.that(
        not (workspace / "flext-b/.reports/docs/generate-report.md").exists(), eq=True
    )


def test_validator_execute_fails_before_generation_and_succeeds_after(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path, project_names=("flext-a",))

    before = FlextInfraDocValidator(
        workspace_root=workspace, selected_projects=["flext-a"]
    ).execute()
    tm.fail(before)
    generated = FlextInfraDocGenerator(
        workspace_root=workspace, selected_projects=["flext-a"], apply_changes=True
    ).execute()
    tm.ok(generated)
    after = FlextInfraDocValidator(
        workspace_root=workspace, selected_projects=["flext-a"], apply_changes=True
    ).execute()
    tm.ok(after)
    tm.that((workspace / "flext-a/TODOS.md").exists(), eq=True)


def test_builder_execute_fails_when_mkdocs_is_missing(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)

    result = FlextInfraDocBuilder(workspace_root=workspace).execute()

    tm.fail(result)
    tm.that((workspace / ".reports/docs/build-report.md").exists(), eq=True)


def test_builder_execute_fails_with_invalid_mkdocs_config(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)
    (workspace / "mkdocs.yml").write_text("site_name: [", encoding="utf-8")

    result = FlextInfraDocBuilder(workspace_root=workspace).execute()

    tm.fail(result)


def test_generate_fix_cycle_is_byte_identical_on_second_run(tmp_path: Path) -> None:
    workspace = u.Tests.create_docs_workspace(tmp_path)
    generator = FlextInfraDocGenerator(workspace_root=workspace, apply_changes=True)
    fixer = FlextInfraDocFixer(workspace_root=workspace, apply_changes=True)

    tm.ok(generator.execute())
    tm.ok(fixer.execute())
    first_cycle = {
        path: path.read_bytes() for path in u.Infra.iter_markdown_files(workspace)
    }

    tm.ok(generator.execute())
    tm.ok(fixer.execute())
    second_cycle = {
        path: path.read_bytes() for path in u.Infra.iter_markdown_files(workspace)
    }

    tm.that(second_cycle, eq=first_cycle)
