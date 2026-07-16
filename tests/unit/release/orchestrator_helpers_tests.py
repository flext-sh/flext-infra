"""Public tests for release utilities and filtered release behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_cli import u as cli_u
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from tests import c
from tests import m
from tests import u
from flext_tests import tm

from pathlib import Path

from tests import t



def make_config(
    workspace_root: Path, *, project_names: list[str] | None = None
) -> p.Infra.ReleaseOrchestratorConfig:
    """Build the validated release configuration used by public probes."""
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
        (c.Tests.RELEASE_PHASE_VALIDATE, (c.Tests.RELEASE_PHASE_VALIDATE,)),
    ],
)
def test_resolve_phase_names(phase: str, expected: t.StrSequence) -> None:
    """Resolve aliases and explicit release phases through the public utility."""
    tm.that(tuple(u.Infra.resolve_phase_names(phase)), eq=expected)


def test_generate_notes_writes_release_document(tmp_path: Path) -> None:
    """Generate a release note document with projects and verification lines."""
    notes_path = tmp_path / "release" / c.Tests.RELEASE_NOTES_FILENAME
    project = u.Tests.create_project_info(tmp_path / "flext-a", name="flext-a")

    result = u.Infra.generate_notes(
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        [project],
        c.Tests.RELEASE_NOTES_CHANGE_LINE,
        notes_path,
    )

    notes = notes_path.read_text(encoding="utf-8")
    tm.ok(result)
    tm.that(notes, has=c.Tests.RELEASE_NOTES_HEADING)
    tm.that(notes, has="- root")
    tm.that(notes, has="- flext-a")
    tm.that(notes, has=c.Tests.RELEASE_NOTES_CHANGE_LINE)
    for verification_line in c.Tests.RELEASE_VERIFICATION_LINES[:2]:
        tm.that(notes, has=verification_line)


def test_generate_notes_failure_returns_result_error(tmp_path: Path) -> None:
    """Return a typed failure when the release note path is not writable."""
    notes_path = tmp_path / "release" / c.Tests.RELEASE_NOTES_FILENAME
    notes_path.mkdir(parents=True, exist_ok=True)

    result = u.Infra.generate_notes(
        c.Tests.RELEASE_VERSION_TARGET, c.Tests.RELEASE_TAG_TARGET, [], "", notes_path
    )

    tm.fail(result)
    tm.that((result.error or ""), has="failed to write release notes")


def test_update_changelog_creates_expected_release_files(tmp_path: Path) -> None:
    """Create the changelog, latest release and versioned release files."""
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

    tm.ok(result)
    tm.that((workspace / "docs" / "CHANGELOG.md").is_file(), eq=True)
    tm.that((workspace / "docs" / "releases" / "latest.md").is_file(), eq=True)
    tm.that(
        (
            workspace / "docs" / "releases" / f"{c.Tests.RELEASE_TAG_TARGET}.md"
        ).is_file(),
        eq=True,
    )


def test_update_changelog_is_idempotent_for_existing_release_heading(
    tmp_path: Path,
) -> None:
    """Keep one release heading when changelog generation is repeated."""
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
    tm.ok(first_result)
    tm.ok(second_result)
    tm.that(changelog.count(f"## {c.Tests.RELEASE_VERSION_TARGET} - "), eq=1)


def test_update_changelog_adds_default_header_when_marker_is_missing(
    tmp_path: Path,
) -> None:
    """Add the canonical changelog header when an existing file lacks it."""
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
    tm.ok(result)
    tm.that(changelog.startswith(c.Tests.RELEASE_CHANGELOG_HEADER), eq=True)


def test_update_changelog_missing_notes_file_returns_failure(tmp_path: Path) -> None:
    """Return a typed failure when the source release notes are absent."""
    workspace = tmp_path / "workspace"

    result = u.Infra.update_changelog(
        workspace,
        c.Tests.RELEASE_VERSION_TARGET,
        c.Tests.RELEASE_TAG_TARGET,
        workspace / "missing-notes.md",
    )

    tm.fail(result)
    tm.that((result.error or ""), has="changelog update failed")


def test_run_release_build_deduplicates_duplicate_project_selectors(
    tmp_path: Path,
) -> None:
    """Build each selected project once and validate the emitted report model."""
    workspace = u.Tests.create_release_workspace(tmp_path, project_names=("flext-a",))

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(workspace, project_names=["flext-a", "flext-a"])
    )

    report_path = (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-report.json"
    )
    report = m.Infra.BuildReport.model_validate(
        cli_u.Cli.json_loads(report_path.read_text(encoding="utf-8")).unwrap()
    )

    tm.ok(result)
    tm.that(report.total, eq=2)
    tm.that([record.project for record in report.records], eq=["root", "flext-a"])
