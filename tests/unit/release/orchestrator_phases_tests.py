"""Public tests for release phase methods."""

from __future__ import annotations

import json
from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator
from tests.constants import c
from tests.models import m
from tests.utilities import TestsFlextInfraUtilities as u


def version_ctx(
    workspace_root: Path,
    *,
    version: str = "1.0.0",
    project_names: list[str] | None = None,
    dry_run: bool = False,
    dev_suffix: bool = False,
) -> m.Infra.ReleasePhaseDispatchConfig:
    return m.Infra.ReleasePhaseDispatchConfig(
        phase=c.Infra.VERSION,
        workspace_root=workspace_root,
        version=version,
        tag=f"v{version}",
        project_names=project_names or [],
        dry_run=dry_run,
        push=False,
        dev_suffix=dev_suffix,
    )


def build_ctx(
    workspace_root: Path,
    *,
    version: str = "1.0.0",
    project_names: list[str] | None = None,
) -> m.Infra.ReleasePhaseDispatchConfig:
    return m.Infra.ReleasePhaseDispatchConfig(
        phase=c.Infra.DIR_BUILD,
        workspace_root=workspace_root,
        version=version,
        tag=f"v{version}",
        project_names=project_names or [],
        dry_run=False,
        push=False,
        dev_suffix=False,
    )


def test_phase_validate_dry_run_succeeds(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator().phase_validate(workspace, dry_run=True)

    assert result.success


def test_phase_validate_apply_propagates_make_failure(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        root_validate_exit_code="1",
    )

    result = FlextInfraReleaseOrchestrator().phase_validate(workspace, dry_run=False)

    assert result.failure


def test_phase_version_updates_root_and_selected_project(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = FlextInfraReleaseOrchestrator().phase_version(
        version_ctx(workspace, project_names=["flext-a"]),
    )

    assert result.success
    assert 'version = "1.0.0"' in (workspace / "pyproject.toml").read_text()
    assert 'version = "1.0.0"' in (workspace / "flext-a" / "pyproject.toml").read_text()
    assert 'version = "0.1.0"' in (workspace / "flext-b" / "pyproject.toml").read_text()


def test_phase_version_dry_run_leaves_files_unchanged(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator().phase_version(
        version_ctx(workspace, dry_run=True),
    )

    assert result.success
    assert 'version = "0.1.0"' in (workspace / "pyproject.toml").read_text()


def test_phase_build_writes_report_and_logs_for_root_and_project(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = FlextInfraReleaseOrchestrator().phase_build(
        build_ctx(workspace, project_names=["flext-a"]),
    )

    assert result.success
    report_path = workspace / ".reports" / "release" / "v1.0.0" / "build-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total"] == 2
    assert report["failures"] == 0
    assert (workspace / ".reports" / "release" / "v1.0.0" / "build-root.log").is_file()
    assert (
        workspace / ".reports" / "release" / "v1.0.0" / "build-flext-a.log"
    ).is_file()
    assert not (
        workspace / ".reports" / "release" / "v1.0.0" / "build-flext-b.log"
    ).exists()


def test_phase_build_failure_still_writes_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        root_build_exit_code="1",
    )

    result = FlextInfraReleaseOrchestrator().phase_build(build_ctx(workspace))

    assert result.failure
    report_path = workspace / ".reports" / "release" / "v1.0.0" / "build-report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failures"] == 1
    assert (workspace / ".reports" / "release" / "v1.0.0" / "build-root.log").is_file()
