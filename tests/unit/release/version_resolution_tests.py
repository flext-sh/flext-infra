"""Public execute() tests for release version and tag resolution."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator


def make_command(
    workspace_root: Path,
    **overrides: object,
) -> FlextInfraReleaseOrchestrator:
    return FlextInfraReleaseOrchestrator.model_validate({
        "workspace_root": workspace_root,
        "phase": "version",
        "interactive": 0,
        "create_branches": 0,
        "apply_changes": True,
        **overrides,
    })


def test_execute_with_explicit_version_updates_workspace_file(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version="1.0.0",
    ).execute()

    assert result.is_success
    assert 'version = "1.0.0"' in (workspace / "pyproject.toml").read_text()


def test_execute_with_dev_suffix_appends_dev_version(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version="1.0.0",
        dev_suffix=True,
    ).execute()

    assert result.is_success
    assert 'version = "1.0.0-dev"' in (workspace / "pyproject.toml").read_text()


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
        phase="build",
        bump="minor",
    ).execute()

    assert result.is_success
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

    assert result.is_failure


def test_execute_with_invalid_tag_prefix_fails(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "pyproject.toml").write_text(
        '[project]\nname = "workspace-root"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = make_command(
        workspace,
        version="1.0.0",
        tag="1.0.0",
    ).execute()

    assert result.is_failure
