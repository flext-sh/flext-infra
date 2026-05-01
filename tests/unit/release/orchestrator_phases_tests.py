"""Public tests for release phase methods."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from flext_infra import FlextInfraReleaseOrchestrator
from flext_infra.release.orchestrator_phases import FlextInfraReleaseOrchestratorPhases
from tests import c, m, p, r, t, u


def version_ctx(
    workspace_root: Path,
    *,
    version: str = c.Tests.RELEASE_VERSION_TARGET,
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
    version: str = c.Tests.RELEASE_VERSION_TARGET,
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


def test_phase_version_dry_run_leaves_files_unchanged(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    result = FlextInfraReleaseOrchestrator().phase_version(
        version_ctx(workspace, dry_run=True),
    )

    assert result.success
    assert (
        f'version = "{c.Tests.RELEASE_VERSION_BASE}"'
        in (workspace / "pyproject.toml").read_text()
    )


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
    report_path = (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-report.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["total"] == 2
    assert report["failures"] == 0
    assert (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-root.log"
    ).is_file()
    assert (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-flext-a.log"
    ).is_file()
    assert not (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-flext-b.log"
    ).exists()


def test_phase_build_failure_still_writes_report(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        root_build_exit_code="1",
    )

    result = FlextInfraReleaseOrchestrator().phase_build(build_ctx(workspace))

    assert result.failure
    report_path = (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-report.json"
    )
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["failures"] == 1
    assert (
        workspace
        / ".reports"
        / "release"
        / c.Tests.RELEASE_TAG_TARGET
        / "build-root.log"
    ).is_file()


def test_run_make_propagates_command_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_path = tmp_path / "proj"
    project_path.mkdir()

    def _run_raw(args: t.StrSequence) -> p.Result[t.JsonValue]:
        del args
        return r[t.JsonValue].fail("make execution failed")

    monkeypatch.setattr(u.Cli, "run_raw", staticmethod(_run_raw))

    result = FlextInfraReleaseOrchestratorPhases._run_make(
        project_path,
        c.Infra.DIR_BUILD,
    )

    assert result.failure


def test_phase_build_fails_when_report_dir_creation_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)
    orchestrator = FlextInfraReleaseOrchestrator()

    def _raise_mkdir(
        self: Path,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        del self
        del mode
        del parents
        del exist_ok
        message = "mkdir failed"
        raise OSError(message)

    monkeypatch.setattr(Path, "mkdir", _raise_mkdir)

    result = orchestrator.phase_build(build_ctx(workspace))

    assert result.failure
    assert "report dir creation failed" in (result.error or "")


def test_phase_build_handles_make_result_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    def _run_make_fail(
        self: FlextInfraReleaseOrchestrator,
        project_path: Path,
        verb: str,
    ) -> p.Result[t.Pair[int, str]]:
        del self
        del project_path
        del verb
        return r[t.Pair[int, str]].fail("make execution failed")

    monkeypatch.setattr(FlextInfraReleaseOrchestrator, "_run_make", _run_make_fail)

    result = FlextInfraReleaseOrchestrator().phase_build(build_ctx(workspace))

    assert result.failure
    assert "build failed" in (result.error or "")


def test_phase_publish_fails_when_report_dir_creation_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)
    orchestrator = FlextInfraReleaseOrchestrator()

    def _raise_mkdir(
        self: Path,
        mode: int = 0o777,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        del self
        del mode
        del parents
        del exist_ok
        message = "mkdir failed"
        raise OSError(message)

    monkeypatch.setattr(Path, "mkdir", _raise_mkdir)

    result = orchestrator.phase_publish(
        m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_PUBLISH,
            workspace_root=workspace,
            version=c.Tests.RELEASE_VERSION_TARGET,
            tag=c.Tests.RELEASE_TAG_TARGET,
            project_names=[],
            dry_run=True,
            push=False,
            dev_suffix=False,
        )
    )

    assert result.failure
    assert "report dir creation failed" in (result.error or "")


def test_phase_publish_propagates_generate_notes_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    def _generate_notes_fail(
        self: FlextInfraReleaseOrchestrator,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        output_path: Path,
    ) -> p.Result[bool]:
        del self
        del ctx
        del output_path
        return r[bool].fail("notes failed")

    monkeypatch.setattr(
        FlextInfraReleaseOrchestrator,
        "_generate_notes",
        _generate_notes_fail,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_PUBLISH,
            workspace_root=workspace,
            version=c.Tests.RELEASE_VERSION_TARGET,
            tag=c.Tests.RELEASE_TAG_TARGET,
            project_names=[],
            dry_run=False,
            push=False,
            dev_suffix=False,
        )
    )

    assert result.failure
    assert "notes failed" in (result.error or "")


def test_phase_publish_fails_when_notes_file_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    def _generate_notes_ok(
        self: FlextInfraReleaseOrchestrator,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        output_path: Path,
    ) -> p.Result[bool]:
        del self
        del ctx
        del output_path
        return r[bool].ok(True)

    monkeypatch.setattr(
        FlextInfraReleaseOrchestrator,
        "_generate_notes",
        _generate_notes_ok,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_PUBLISH,
            workspace_root=workspace,
            version=c.Tests.RELEASE_VERSION_TARGET,
            tag=c.Tests.RELEASE_TAG_TARGET,
            project_names=[],
            dry_run=False,
            push=False,
            dev_suffix=False,
        )
    )

    assert result.failure
    assert "did not create" in (result.error or "")


def test_publish_apply_propagates_changelog_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    def _update_changelog(
        workspace_root: Path,
        version: str,
        tag: str,
        notes_path: Path,
    ) -> p.Result[bool]:
        del workspace_root
        del version
        del tag
        del notes_path
        return r[bool].fail("changelog failed")

    monkeypatch.setattr(u.Infra, "update_changelog", staticmethod(_update_changelog))

    result = FlextInfraReleaseOrchestrator()._publish_apply(
        workspace_root=workspace,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        notes_path=workspace / "notes.md",
        push=False,
    )

    assert result.failure
    assert "changelog failed" in (result.error or "")


def test_publish_apply_propagates_tag_creation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)
    notes_path = workspace / "notes.md"
    notes_path.write_text("# release notes\n", encoding=c.Cli.ENCODING_DEFAULT)

    def _create_tag_fail(
        self: FlextInfraReleaseOrchestrator,
        workspace_root: Path,
        tag: str,
    ) -> p.Result[bool]:
        del self
        del workspace_root
        del tag
        return r[bool].fail("tag failed")

    monkeypatch.setattr(FlextInfraReleaseOrchestrator, "_create_tag", _create_tag_fail)

    result = FlextInfraReleaseOrchestrator()._publish_apply(
        workspace_root=workspace,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        notes_path=notes_path,
        push=False,
    )

    assert result.failure
    assert "tag failed" in (result.error or "")


def test_phase_publish_apply_success_path(tmp_path: Path) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_PUBLISH,
            workspace_root=workspace,
            version=c.Tests.RELEASE_VERSION_TARGET,
            tag=c.Tests.RELEASE_TAG_TARGET,
            project_names=[],
            dry_run=False,
            push=False,
            dev_suffix=False,
        )
    )

    assert result.success


def test_phase_publish_propagates_apply_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    def _publish_apply_fail(
        self: FlextInfraReleaseOrchestrator,
        *,
        workspace_root: Path,
        version: str,
        tag: str,
        notes_path: Path,
        push: bool,
    ) -> p.Result[bool]:
        del self
        del workspace_root
        del version
        del tag
        del notes_path
        del push
        return r[bool].fail("apply failed")

    monkeypatch.setattr(
        FlextInfraReleaseOrchestrator,
        "_publish_apply",
        _publish_apply_fail,
    )

    result = FlextInfraReleaseOrchestrator().phase_publish(
        m.Infra.ReleasePhaseDispatchConfig(
            phase=c.Infra.VERB_PUBLISH,
            workspace_root=workspace,
            version=c.Tests.RELEASE_VERSION_TARGET,
            tag=c.Tests.RELEASE_TAG_TARGET,
            project_names=[],
            dry_run=False,
            push=False,
            dev_suffix=False,
        )
    )

    assert result.failure
    assert "apply failed" in (result.error or "")


def test_publish_apply_push_failure_is_propagated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(
        tmp_path,
        initialize_root_git=True,
    )
    notes_path = workspace / "notes.md"
    notes_path.write_text("# release notes\n", encoding=c.Cli.ENCODING_DEFAULT)

    def _push_release_fail(
        self: FlextInfraReleaseOrchestrator,
        workspace_root: Path,
        tag: str,
    ) -> p.Result[bool]:
        del self
        del workspace_root
        del tag
        return r[bool].fail("push failed")

    monkeypatch.setattr(
        FlextInfraReleaseOrchestrator,
        "_push_release",
        _push_release_fail,
    )

    result = FlextInfraReleaseOrchestrator()._publish_apply(
        workspace_root=workspace,
        version=c.Tests.RELEASE_VERSION_TARGET,
        tag=c.Tests.RELEASE_TAG_TARGET,
        notes_path=notes_path,
        push=True,
    )

    assert result.failure
    assert "push failed" in (result.error or "")


def test_phase_version_fails_on_invalid_semver_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = u.Tests.create_release_workspace(tmp_path)

    def _parse_semver(version: str) -> p.Result[t.JsonValue]:
        del version
        return r[t.JsonValue].fail("invalid semver")

    monkeypatch.setattr(u.Infra, "parse_semver", staticmethod(_parse_semver))

    result = FlextInfraReleaseOrchestrator().phase_version(
        version_ctx(workspace, version="invalid-semver")
    )

    assert result.failure
    assert "invalid semver" in (result.error or "")


def test_version_update_files_skips_missing_file(tmp_path: Path) -> None:
    orchestrator = FlextInfraReleaseOrchestrator()
    changed = orchestrator._version_update_files(
        files=[tmp_path / "missing" / "pyproject.toml"],
        target=c.Tests.RELEASE_VERSION_TARGET,
        dry_run=False,
    )

    assert changed == 0


def test_version_update_files_skips_when_target_already_matches(
    tmp_path: Path,
) -> None:
    orchestrator = FlextInfraReleaseOrchestrator()
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        f'[project]\nname = "demo"\nversion = "{c.Tests.RELEASE_VERSION_TARGET}"\n',
        encoding=c.Cli.ENCODING_DEFAULT,
    )

    changed = orchestrator._version_update_files(
        files=[pyproject],
        target=c.Tests.RELEASE_VERSION_TARGET,
        dry_run=False,
    )

    assert changed == 0


def test_orchestrator_phases_abstract_methods_raise() -> None:
    phases = FlextInfraReleaseOrchestratorPhases()

    with pytest.raises(NotImplementedError):
        phases._build_targets(Path(), [])
    with pytest.raises(NotImplementedError):
        phases._generate_notes(
            m.Infra.ReleasePhaseDispatchConfig(
                phase=c.Infra.VERB_PUBLISH,
                workspace_root=Path(),
                version=c.Tests.RELEASE_VERSION_TARGET,
                tag=c.Tests.RELEASE_TAG_TARGET,
                project_names=[],
                dry_run=False,
                push=False,
                dev_suffix=False,
            ),
            Path(c.Tests.RELEASE_NOTES_FILENAME),
        )
    with pytest.raises(NotImplementedError):
        phases._create_tag(Path(), c.Tests.RELEASE_TAG_TARGET)
    with pytest.raises(NotImplementedError):
        phases._push_release(Path(), c.Tests.RELEASE_TAG_TARGET)
    with pytest.raises(NotImplementedError):
        phases._version_files(Path(), [])
