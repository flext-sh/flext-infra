"""Public release CLI flow tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main
from flext_infra.tests.constants import c
from tests.utilities import TestsFlextInfraUtilities as u


def run_release_main(workspace: Path, *extra: str) -> int:
    return infra_main([
        "release",
        "run",
        "--workspace",
        str(workspace),
        *extra,
    ])


def test_main_validate_apply_succeeds(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = run_release_main(
        workspace,
        "--phase",
        c.Tests.RELEASE_PHASE_VALIDATE,
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 0


def test_main_version_apply_updates_root_and_selected_project(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=c.Tests.RELEASE_PROJECTS,
    )

    result = run_release_main(
        workspace,
        "--phase",
        c.Tests.RELEASE_PHASE_VERSION,
        "--version",
        c.Tests.RELEASE_VERSION_SELECTED,
        "--projects",
        c.Tests.RELEASE_PROJECTS[0],
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 0
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_SELECTED}"'
        in (workspace / "pyproject.toml").read_text()
    )
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_SELECTED}"'
        in (workspace / c.Tests.RELEASE_PROJECTS[0] / "pyproject.toml").read_text()
    )
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_BASE}"'
        in (workspace / c.Tests.RELEASE_PROJECTS[1] / "pyproject.toml").read_text()
    )


def test_main_build_with_bump_uses_resolved_version_in_report_dir(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = run_release_main(
        workspace,
        "--phase",
        c.Tests.RELEASE_PHASE_BUILD,
        "--bump",
        c.Tests.RELEASE_BUMP_MINOR,
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 0
    assert (
        workspace / ".reports" / "release" / "v0.2.0" / "build-report.json"
    ).is_file()


def test_main_all_dry_run_writes_release_artifacts(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=(c.Tests.RELEASE_PROJECTS[0],),
    )

    result = run_release_main(
        workspace,
        "--phase",
        c.Infra.RELEASE_PHASE_ALL,
        "--interactive",
        "0",
        "--dry-run",
    )

    assert result == 0
    assert (
        workspace
        / ".reports"
        / "release"
        / f"v{c.Tests.RELEASE_VERSION_BASE}"
        / "build-report.json"
    ).is_file()
    assert (
        workspace
        / ".reports"
        / "release"
        / f"v{c.Tests.RELEASE_VERSION_BASE}"
        / c.Tests.RELEASE_NOTES_FILENAME
    ).is_file()


def test_main_invalid_version_returns_failure(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = run_release_main(
        workspace,
        "--phase",
        c.Tests.RELEASE_PHASE_VERSION,
        "--version",
        "invalid",
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 1
