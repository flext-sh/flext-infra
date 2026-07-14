"""Public release tests covering real git effects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli
from flext_infra.release.orchestrator import FlextInfraReleaseOrchestrator
from tests import c
from tests import m
from tests import TestsFlextInfraUtilities as u
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def make_config(
    workspace_root: Path,
    *,
    phase: str = c.Infra.VERB_VALIDATE,
    project_names: list[str] | None = None,
    push: bool = False,
) -> m.Infra.ReleaseOrchestratorConfig:
    return m.Infra.ReleaseOrchestratorConfig(
        workspace_root=workspace_root,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        phases=[phase],
        project_names=project_names,
        dry_run=False,
        push=push,
        dev_suffix=False,
        create_branches=True,
        next_dev=False,
        next_bump=c.Tests.RELEASE_BUMP_MINOR,
    )


def publish_ctx(
    workspace_root: Path, *, push: bool = False
) -> m.Infra.ReleasePhaseDispatchConfig:
    return m.Infra.ReleasePhaseDispatchConfig(
        phase=c.Infra.VERB_PUBLISH,
        workspace_root=workspace_root,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        project_names=[],
        dry_run=False,
        push=push,
        dev_suffix=False,
    )


def git_ref_exists(repo_root: Path, ref_name: str) -> bool:
    result = u.Cli.capture(["git", "show-ref", "--verify", ref_name], cwd=repo_root)
    return not result.failure


def configure_local_origin(repo_root: Path, remote_root: Path) -> Path:
    bare_remote = remote_root / "origin.git"
    cli.run_checked([c.Infra.GIT, "init", "--bare", str(bare_remote)])
    cli.run_checked(
        [c.Infra.GIT, "remote", "add", c.Infra.GIT_ORIGIN, str(bare_remote)],
        cwd=repo_root,
    )
    cli.run_checked(
        [c.Infra.GIT, "push", "-u", c.Infra.GIT_ORIGIN, "main"], cwd=repo_root
    )
    return bare_remote


def test_run_release_creates_branches_for_root_and_selected_project(
    tmp_path: Path,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        initialize_root_git=True,
        initialize_project_git=True,
    )

    result = FlextInfraReleaseOrchestrator().run_release(
        make_config(workspace, project_names=["flext-a"])
    )

    tm.ok(result)
    assert git_ref_exists(
        workspace, f"refs/heads/release/{c.Tests.RELEASE_VERSION_TARGET}"
    )
    assert git_ref_exists(
        workspace / "flext-a", f"refs/heads/release/{c.Tests.RELEASE_VERSION_TARGET}"
    )
    assert not git_ref_exists(
        workspace / "flext-b", f"refs/heads/release/{c.Tests.RELEASE_VERSION_TARGET}"
    )


def test_phase_publish_succeeds_when_tag_already_exists(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path, initialize_root_git=True)
    tm.ok(
        u.Cli.run_checked(
            [
                "git",
                "tag",
                "-a",
                c.Tests.RELEASE_TAG_TARGET,
                "-m",
                f"release: {c.Tests.RELEASE_TAG_TARGET}",
            ],
            cwd=workspace,
        )
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(publish_ctx(workspace))

    tm.ok(result)
    assert (workspace / "docs" / "CHANGELOG.md").is_file()
    assert (
        u.Cli.capture(
            ["git", "tag", "-l", c.Tests.RELEASE_TAG_TARGET], cwd=workspace
        ).unwrap()
        == c.Tests.RELEASE_TAG_TARGET
    )


def test_phase_publish_push_succeeds_with_local_origin(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path, initialize_root_git=True)
    configure_local_origin(workspace, tmp_path / "remote")

    result = FlextInfraReleaseOrchestrator().phase_publish(
        publish_ctx(workspace, push=True)
    )

    tm.ok(result)
    assert (
        u.Cli.capture(
            ["git", "tag", "-l", c.Tests.RELEASE_TAG_TARGET], cwd=workspace
        ).unwrap()
        == c.Tests.RELEASE_TAG_TARGET
    )
