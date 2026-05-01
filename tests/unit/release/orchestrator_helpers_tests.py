"""Public tests for release utilities and filtered release behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flext_infra import FlextInfraReleaseOrchestrator
from tests.constants import c
from tests.models import m
from tests.utilities import TestsFlextInfraUtilities as u


def make_config(
    workspace_root: Path,
    *,
    project_names: list[str] | None = None,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        phases=[c.Infra.DIR_BUILD],
        project_names=project_names,
        dry_run=False,
        push=False,
        dev_suffix=False,
        create_branches=False,
        next_dev=False,
        next_bump=c.Tests.RELEASE_BUMP_MINOR,
    )


@pytest.mark.parametrize(
    ("phase", "expected"),
    [
        (c.Infra.RELEASE_PHASE_ALL, c.Tests.ALL_PHASES),
        (
            c.Tests.RELEASE_PHASE_VALIDATE,
            (c.Tests.RELEASE_PHASE_VALIDATE,),
        ),
    ],
)
def test_resolve_phase_names(
    phase: str,
    expected: tuple[str, ...],
) -> None:
    assert tuple(u.Infra.resolve_phase_names(phase)) == expected


def test_generate_notes_writes_release_document(tmp_path: Path) -> None:
    notes_path = tmp_path / "release" / c.Tests.RELEASE_NOTES_FILENAME
    project = u.Tests.create_project_info(
        tmp_path / "flext-a",
        name="flext-a",
    )

    result = u.Infra.generate_notes(
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        [project],
        c.Tests.RELEASE_NOTES_CHANGE_LINE,
        notes_path,
    )

    notes = notes_path.read_text(encoding="utf-8")
    assert result.success
    assert c.Tests.RELEASE_NOTES_HEADING in notes
    assert "- root" in notes
    assert "- flext-a" in notes
    assert c.Tests.RELEASE_NOTES_CHANGE_LINE in notes
    for verification_line in c.Tests.RELEASE_VERIFICATION_LINES[:2]:
        assert verification_line in notes


def test_generate_notes_failure_returns_result_error(tmp_path: Path) -> None:
    notes_path = tmp_path / "release" / c.Tests.RELEASE_NOTES_FILENAME
    notes_path.mkdir(parents=True, exist_ok=True)

    result = u.Infra.generate_notes(
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        [],
        "",
        notes_path,
    )

    assert result.failure
    assert "failed to write release notes" in (result.error or "")


def test_update_changelog_creates_expected_release_files(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    notes_path = workspace / "notes.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(c.Tests.RELEASE_NOTES_HEADING + "\n", encoding="utf-8")

    result = u.Infra.update_changelog(
        workspace,
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        notes_path,
    )

    assert result.success
    assert (workspace / "docs" / "CHANGELOG.md").is_file()
    assert (workspace / "docs" / "releases" / "latest.md").is_file()
    assert (
        workspace / "docs" / "releases" / f"{c.Tests.RELEASE_TAG_TARGET}.md"
    ).is_file()


def test_update_changelog_is_idempotent_for_existing_release_heading(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    notes_path = workspace / "notes.md"
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(c.Tests.RELEASE_NOTES_HEADING + "\n", encoding="utf-8")

    first_result = u.Infra.update_changelog(
        workspace,
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        notes_path,
    )
    second_result = u.Infra.update_changelog(
        workspace,
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        notes_path,
    )

    changelog = (workspace / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    assert first_result.success
    assert second_result.success
    assert changelog.count(f"## {c.Tests.RELEASE_VERSION_TARGET} - ") == 1


def test_update_changelog_adds_default_header_when_marker_is_missing(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    docs_dir = workspace / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "CHANGELOG.md").write_text("Existing notes only\n", encoding="utf-8")
    notes_path = workspace / "notes.md"
    notes_path.write_text(c.Tests.RELEASE_NOTES_HEADING + "\n", encoding="utf-8")

    result = u.Infra.update_changelog(
        workspace,
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        notes_path,
    )

    changelog = (docs_dir / "CHANGELOG.md").read_text(encoding="utf-8")
    assert result.success
    assert changelog.startswith(c.Tests.RELEASE_CHANGELOG_HEADER)


def test_update_changelog_missing_notes_file_returns_failure(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"

    result = u.Infra.update_changelog(
        workspace,
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        workspace / "missing-notes.md",
    )

    assert result.failure
    assert "changelog update failed" in (result.error or "")


def test_run_release_build_deduplicates_duplicate_project_selectors(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(
            workspace,
            project_names=["flext-a", "flext-a"],
        ),
    )

    report_path = (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-report.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert result.success
    assert report["total"] == 2
    assert [record["project"] for record in report["records"]] == ["root", "flext-a"]
