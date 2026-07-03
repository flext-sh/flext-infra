"""Public execute() tests for release version and tag resolution."""

from __future__ import annotations

from pathlib import Path

from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from flext_infra.tests.constants import c


def make_command(
    workspace_root: Path,
    **overrides: object,
) -> FlextInfraReleaseOrchestrator:
    command: FlextInfraReleaseOrchestrator = (
        FlextInfraReleaseOrchestrator.model_validate({
            "workspace_root": workspace_root,
            "phase": c.Tests.RELEASE_PHASE_VERSION,
            "interactive": 0,
            "create_branches": 0,
            "apply_changes": True,
            **overrides,
        })
    )
    return command


def test_execute_with_explicit_version_updates_workspace_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version=c.Tests.RELEASE_VERSION_TARGET,
    ).execute()

    assert result.success
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_TARGET}"'
        in (workspace / "pyproject.toml").read_text()
    )


def test_execute_with_dev_suffix_appends_dev_version(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version=c.Tests.RELEASE_VERSION_TARGET,
        dev_suffix=True,
    ).execute()

    assert result.success
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_TARGET}-dev"'
        in (workspace / "pyproject.toml").read_text()
    )


def test_execute_with_bump_uses_current_workspace_version(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "Makefile").write_text("build:\n\t@exit 0\n", encoding="utf-8")
    (workspace / "pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "workspace-root"\n'
            'version = "0.1.0"\n'
            'dependencies = ["flext-core>=0.1.0"]\n'
        ),
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        phase=c.Tests.RELEASE_PHASE_BUILD,
        bump=c.Tests.RELEASE_BUMP_MINOR,
    ).execute()

    assert result.success
    assert (
        workspace / ".reports" / "release" / "v0.2.0" / "build-report.json"
    ).is_file()


def test_execute_with_invalid_explicit_version_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version="invalid",
    ).execute()

    assert result.failure


def test_execute_with_invalid_tag_prefix_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_VERSION_TARGET,
    ).execute()

    assert result.failure
