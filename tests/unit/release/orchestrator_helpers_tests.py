"""Public tests for release utilities and filtered release behavior."""

from __future__ import annotations

import json
from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator
from tests import c, m, u


def make_config(
    workspace_root: Path,
    *,
    project_names: list[str] | None = None,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version="1.0.0",
        tag="v1.0.0",
        phases=[c.Infra.Directories.BUILD],
        project_names=project_names,
        dry_run=False,
        push=False,
        dev_suffix=False,
        create_branches=False,
        next_dev=False,
        next_bump="minor",
    )


def test_generate_notes_writes_release_document(tmp_path: Path) -> None:
    notes_path = tmp_path / "release" / "RELEASE_NOTES.md"
    project = u.Infra.Tests.create_project_info(
        tmp_path / "flext-a",
        name="flext-a",
    )

    result = u.Infra.generate_notes(
        "1.0.0",
        "v1.0.0",
        [project],
        "- abc123 fix release flow",
        notes_path,
    )

    notes = notes_path.read_text(encoding="utf-8")
    assert result.is_success
    assert "# Release v1.0.0" in notes
    assert "- root" in notes
    assert "- flext-a" in notes
    assert "- abc123 fix release flow" in notes


def test_update_changelog_creates_expected_release_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    notes_path = workspace / "notes.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text("# Release v1.0.0\n", encoding="utf-8")

    result = u.Infra.update_changelog(
        workspace,
        "1.0.0",
        "v1.0.0",
        notes_path,
    )

    assert result.is_success
    assert (workspace / "docs" / "CHANGELOG.md").is_file()
    assert (workspace / "docs" / "releases" / "latest.md").is_file()
    assert (workspace / "docs" / "releases" / "v1.0.0.md").is_file()


def test_update_changelog_is_idempotent_for_existing_release_heading(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    notes_path = workspace / "notes.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text("# Release v1.0.0\n", encoding="utf-8")

    first_result = u.Infra.update_changelog(
        workspace,
        "1.0.0",
        "v1.0.0",
        notes_path,
    )
    second_result = u.Infra.update_changelog(
        workspace,
        "1.0.0",
        "v1.0.0",
        notes_path,
    )

    changelog = (workspace / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert first_result.is_success
    assert second_result.is_success
    assert changelog.count("## 1.0.0 - ") == 1


def test_run_release_build_deduplicates_duplicate_project_selectors(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(
            workspace,
            project_names=["flext-a", "flext-a"],
        ),
    )

    report_path = workspace / ".reports" / "release" / "v1.0.0" / "build-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert result.is_success
    assert report["total"] == 2
    assert [record["project"] for record in report["records"]] == ["root", "flext-a"]
