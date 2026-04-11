"""Public tests for the publish phase."""

from __future__ import annotations

from pathlib import Path

from flext_infra import FlextInfraReleaseOrchestrator
from tests import c, m, u


def publish_ctx(
    workspace_root: Path,
    *,
    project_names: list[str] | None = None,
    dry_run: bool = False,
    push: bool = False,
) -> m.Infra.ReleasePhaseDispatchConfig:
    return m.Infra.ReleasePhaseDispatchConfig(
        phase=c.Infra.VERB_PUBLISH,
        workspace_root=workspace_root,
        version="1.0.0",
        tag="v1.0.0",
        project_names=project_names or [],
        dry_run=dry_run,
        push=push,
        dev_suffix=False,
    )


def test_phase_publish_dry_run_writes_notes_only(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        publish_ctx(workspace, dry_run=True),
    )

    assert result.success
    assert (
        workspace / ".reports" / "release" / "v1.0.0" / "RELEASE_NOTES.md"
    ).is_file()
    assert not (workspace / "docs" / "CHANGELOG.md").exists()
    assert u.Cli.capture(["git", "tag", "-l", "v1.0.0"], cwd=workspace).unwrap() == ""


def test_phase_publish_apply_updates_docs_and_creates_tag(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(publish_ctx(workspace))

    assert result.success
    assert (workspace / "docs" / "CHANGELOG.md").is_file()
    assert (workspace / "docs" / "releases" / "latest.md").is_file()
    assert (workspace / "docs" / "releases" / "v1.0.0.md").is_file()
    assert (
        u.Cli.capture(["git", "tag", "-l", "v1.0.0"], cwd=workspace).unwrap()
        == "v1.0.0"
    )


def test_phase_publish_push_without_origin_fails_after_local_tagging(
    tmp_path: Path,
) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        publish_ctx(workspace, push=True),
    )

    assert result.failure
    assert (workspace / "docs" / "CHANGELOG.md").is_file()
    assert (
        u.Cli.capture(["git", "tag", "-l", "v1.0.0"], cwd=workspace).unwrap()
        == "v1.0.0"
    )


def test_phase_publish_notes_include_only_selected_projects(tmp_path: Path) -> None:
    workspace = u.Infra.Tests.create_release_workspace(
        tmp_path,
        project_names=("flext-a", "flext-b"),
        initialize_root_git=True,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        publish_ctx(
            workspace,
            project_names=["flext-a"],
            dry_run=True,
        ),
    )

    notes_path = workspace / ".reports" / "release" / "v1.0.0" / "RELEASE_NOTES.md"
    notes = notes_path.read_text(encoding="utf-8")

    assert result.success
    assert "- root" in notes
    assert "- flext-a" in notes
    assert "- flext-b" not in notes
