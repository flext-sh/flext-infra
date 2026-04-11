"""Public release tests covering real git effects."""

from __future__ import annotations

import subprocess
from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator
from tests import c, m, u


def make_config(
    workspace_root: Path,
    *,
    phase: str = c.Infra.VERB_VALIDATE,
    project_names: list[str] | None = None,
    push: bool = False,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version="1.0.0",
        tag="v1.0.0",
        phases=[phase],
        project_names=project_names,
        dry_run=False,
        push=push,
        dev_suffix=False,
        create_branches=True,
        next_dev=False,
        next_bump="minor",
    )


def publish_ctx(
    workspace_root: Path,
    *,
    push: bool = False,
) -> m.Infra.ReleasePhaseDispatchConfig:
    return m.Infra.ReleasePhaseDispatchConfig(
        phase=c.Infra.VERB_PUBLISH,
        workspace_root=workspace_root,
        version="1.0.0",
        tag="v1.0.0",
        project_names=[],
        dry_run=False,
        push=push,
        dev_suffix=False,
    )


def git_ref_exists(repo_root: Path, ref_name: str) -> bool:
    return u.Cli.capture(
        ["git", "show-ref", "--verify", ref_name],
        cwd=repo_root,
    ).success


def configure_local_origin(repo_root: Path, remote_root: Path) -> Path:
    bare_remote = remote_root / "origin.git"
    subprocess.run(
        [c.Infra.GIT, "init", "--bare", str(bare_remote)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [c.Infra.GIT, "remote", "add", c.Infra.GIT_ORIGIN, str(bare_remote)],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [c.Infra.GIT, "push", "-u", c.Infra.GIT_ORIGIN, "main"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return bare_remote


def test_run_release_creates_branches_for_root_and_selected_project(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        initialize_root_git=True,
        initialize_project_git=True,
    )

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(
            workspace,
            project_names=["flext-a"],
        ),
    )

    assert result.success
    assert git_ref_exists(workspace, "refs/heads/release/1.0.0")
    assert git_ref_exists(workspace / "flext-a", "refs/heads/release/1.0.0")
    assert not git_ref_exists(workspace / "flext-b", "refs/heads/release/1.0.0")


def test_phase_publish_succeeds_when_tag_already_exists(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )
    assert u.Cli.run_checked(
        ["git", "tag", "-a", "v1.0.0", "-m", "release: v1.0.0"],
        cwd=workspace,
    ).success

    result = FlextInfraReleaseOrchestrator().phase_publish(publish_ctx(workspace))

    assert result.success
    assert (workspace / "docs" / "CHANGELOG.md").is_file()
    assert (
        u.Cli.capture(["git", "tag", "-l", "v1.0.0"], cwd=workspace).unwrap()
        == "v1.0.0"
    )


def test_phase_publish_push_succeeds_with_local_origin(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )
    configure_local_origin(workspace, tmp_path / "remote")

    result = FlextInfraReleaseOrchestrator().phase_publish(
        publish_ctx(workspace, push=True),
    )

    assert result.success
    assert (
        u.Cli.capture(["git", "tag", "-l", "v1.0.0"], cwd=workspace).unwrap()
        == "v1.0.0"
    )
