"""Public release CLI flow tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import main as infra_main
from tests import u


def run_release_main(workspace: Path, *extra: str) -> int:
    return infra_main([
        "release",
        "run",
        "--workspace",
        str(workspace),
        *extra,
    ])


def test_main_validate_apply_succeeds(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(tmp_path)

    result = run_release_main(
        workspace,
        "--phase",
        "validate",
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 0


def test_main_version_apply_updates_root_and_selected_project(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = run_release_main(
        workspace,
        "--phase",
        "version",
        "--version",
        "1.2.0",
        "--projects",
        "flext-a",
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 0
    assert 'version = "1.2.0"' in (workspace / "pyproject.toml").read_text()
    assert 'version = "1.2.0"' in (workspace / "flext-a" / "pyproject.toml").read_text()
    assert 'version = "0.1.0"' in (workspace / "flext-b" / "pyproject.toml").read_text()


def test_main_build_with_bump_uses_resolved_version_in_report_dir(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_release_workspace(tmp_path)

    result = run_release_main(
        workspace,
        "--phase",
        "build",
        "--bump",
        "minor",
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
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a",),
    )

    result = run_release_main(
        workspace,
        "--phase",
        "all",
        "--interactive",
        "0",
        "--dry-run",
    )

    assert result == 0
    assert (
        workspace / ".reports" / "release" / "v0.1.0" / "build-report.json"
    ).is_file()
    assert (
        workspace / ".reports" / "release" / "v0.1.0" / "RELEASE_NOTES.md"
    ).is_file()


def test_main_invalid_version_returns_failure(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(tmp_path)

    result = run_release_main(
        workspace,
        "--phase",
        "version",
        "--version",
        "invalid",
        "--interactive",
        "0",
        "--create-branches",
        "0",
        "--apply",
    )

    assert result == 1
