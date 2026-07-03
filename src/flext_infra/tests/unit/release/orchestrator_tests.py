"""Public tests for release orchestration entrypoints."""

from __future__ import annotations

from pathlib import Path

from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.tests.constants import c
from flext_infra.tests.models import m
from flext_infra.tests.utilities import TestsFlextInfraUtilities as u


def make_config(
    workspace_root: Path,
    *,
    phases: list[str] | None = None,
    project_names: list[str] | None = None,
    dry_run: bool = False,
    create_branches: bool = False,
    next_dev: bool = False,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        phases=phases or [c.Infra.VERB_VALIDATE],
        project_names=project_names,
        dry_run=dry_run,
        push=False,
        dev_suffix=False,
        create_branches=create_branches,
        next_dev=next_dev,
        next_bump=c.Tests.RELEASE_BUMP_MINOR,
    )


def test_execute_validate_dry_run_succeeds(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator.model_validate({
        "workspace_root": workspace,
        "phase": c.Tests.RELEASE_PHASE_VALIDATE,
        "interactive": 0,
    }).execute()

    assert result.success


def test_run_release_invalid_phase_fails(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(workspace, phases=["invalid"]),
    )

    assert result.failure
    assert "invalid phase" in (result.error or "")


def test_run_release_empty_phase_list_is_a_noop_success(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(workspace, phases=[]),
    )

    assert result.success


def test_run_release_stops_on_validate_failure_before_version_update(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        root_validate_exit_code="1",
    )

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(
            workspace,
            phases=[c.Infra.VERB_VALIDATE, c.Infra.VERSION],
        ),
    )

    assert result.failure
    assert 'version = "0.1.0"' in (workspace / "pyproject.toml").read_text()


def test_run_release_project_filter_updates_only_selected_project(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
    )

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(
            workspace,
            phases=[c.Infra.VERSION],
            project_names=["flext-a"],
        ),
    )

    assert result.success
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_TARGET}"'
        in (workspace / "pyproject.toml").read_text()
    )
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_TARGET}"'
        in (workspace / "flext-a" / "pyproject.toml").read_text()
    )
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_BASE}"'
        in (workspace / "flext-b" / "pyproject.toml").read_text()
    )


def test_run_release_next_dev_updates_workspace_to_next_dev_version(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(
            workspace,
            phases=[c.Infra.VERSION],
            next_dev=True,
        ),
    )

    assert result.success
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_NEXT_DEV}"'
        in (workspace / "pyproject.toml").read_text()
    )
