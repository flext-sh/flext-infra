"""Tests for FlextInfraReleaseOrchestrator helper methods."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch
from flext_tests import tm
from tests import (
    FakeSelection,
    FakeUtilsNamespace,
    m,
    r,
    t,
    u,
)

import flext_infra.release.orchestrator as _orch_mod
from flext_infra import FlextInfraReleaseOrchestrator


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir(exist_ok=True)
    (root / ".git").mkdir()
    (root / "Makefile").touch()
    (root / "pyproject.toml").write_text('version = "0.1.0"\n', encoding="utf-8")
    return root


def _patch_sel(mp: MonkeyPatch, sel: FakeSelection) -> None:
    def _resolve_projects(
        workspace_root: Path,
        names: t.StrSequence,
    ) -> r[Sequence[m.Infra.ProjectInfo]]:
        return sel.resolve_projects(workspace_root, names)

    mp.setattr(u.Infra, "resolve_projects", staticmethod(_resolve_projects))


class TestVersionFiles:
    def test_includes_workspace_root(self, workspace_root: Path) -> None:
        files = FlextInfraReleaseOrchestrator()._version_files(workspace_root, [])
        tm.that(any(f.name == "pyproject.toml" for f in files), eq=True)

    def test_discovery(self, workspace_root: Path, monkeypatch: MonkeyPatch) -> None:
        proj_dir = workspace_root / "proj1"
        proj_dir.mkdir()
        (proj_dir / "pyproject.toml").touch()
        fake_sel = FakeSelection()
        fake_sel._resolve_result = r[Sequence[m.Infra.ProjectInfo]].ok([
            m.Infra.ProjectInfo(name="proj1", path=proj_dir, stack="python"),
        ])
        _patch_sel(monkeypatch, fake_sel)
        tm.that(
            len(
                FlextInfraReleaseOrchestrator()._version_files(
                    workspace_root,
                    ["proj1"],
                ),
            ),
            gt=0,
        )


class TestBuildTargets:
    """Tests for _build_targets."""

    def test_includes_root(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        _patch_sel(monkeypatch, FakeSelection())
        targets = FlextInfraReleaseOrchestrator()._build_targets(workspace_root, [])
        name, path = targets[0]
        tm.that(name, eq="root")
        tm.that(str(path), eq=str(workspace_root))

    def test_deduplication(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        fake_sel = FakeSelection()
        fake_sel._resolve_result = r[Sequence[m.Infra.ProjectInfo]].ok([
            m.Infra.ProjectInfo(
                name="proj1",
                path=workspace_root / "proj1",
                stack="python",
            ),
        ])
        _patch_sel(monkeypatch, fake_sel)
        names = [
            name
            for name, _ in FlextInfraReleaseOrchestrator()._build_targets(
                workspace_root,
                ["proj1"],
            )
        ]
        tm.that(len(names), eq=len(set(names)))


class TestRunMake:
    """Tests for _run_make."""

    def test_success(self, workspace_root: Path, monkeypatch: MonkeyPatch) -> None:
        output = m.Cli.CommandOutput(exit_code=0, stdout="ok", stderr="")

        def _fake_run_raw(
            cmd: t.StrSequence,
            **kw: t.Scalar,
        ) -> r[m.Cli.CommandOutput]:
            return r[m.Cli.CommandOutput].ok(output)

        monkeypatch.setattr(u.Cli, "run_raw", staticmethod(_fake_run_raw))
        result = FlextInfraReleaseOrchestrator._run_make(workspace_root, "build")
        tm.ok(result)
        code, _out = result.value
        tm.that(code, eq=0)

    def test_failure(self, workspace_root: Path, monkeypatch: MonkeyPatch) -> None:
        def _fake_run_raw(
            cmd: t.StrSequence,
            **kw: t.Scalar,
        ) -> r[m.Cli.CommandOutput]:
            return r[m.Cli.CommandOutput].fail("failed")

        monkeypatch.setattr(u.Cli, "run_raw", staticmethod(_fake_run_raw))
        tm.fail(FlextInfraReleaseOrchestrator._run_make(workspace_root, "build"))


class TestGenerateNotes:
    """Tests for _generate_notes."""

    def test_writes_file(self, workspace_root: Path, monkeypatch: MonkeyPatch) -> None:
        FakeUtilsNamespace.Infra.reset()
        monkeypatch.setattr(_orch_mod, "u", FakeUtilsNamespace)

        def _previous_tag(*a: t.Scalar, **kw: t.Scalar) -> r[str]:
            del a, kw
            return r[str].ok("")

        def _collect_changes(*a: t.Scalar, **kw: t.Scalar) -> r[str]:
            del a, kw
            return r[str].ok("")

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_previous_tag",
            _previous_tag,
        )
        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "_collect_changes",
            _collect_changes,
        )
        notes_path = workspace_root / "notes.md"
        config = m.Infra.ReleasePhaseDispatchConfig(
            phase="publish",
            workspace_root=workspace_root,
            version="1.0.0",
            tag="v1.0.0",
            project_names=[],
            dry_run=False,
            push=False,
            dev_suffix=False,
        )
        result = FlextInfraReleaseOrchestrator()._generate_notes(
            config,
            notes_path,
        )
        tm.ok(result)
        tm.that(notes_path.exists(), eq=True)


class TestUpdateChangelog:
    """Tests for _update_changelog."""

    def test_creates_files(self, workspace_root: Path) -> None:
        notes = workspace_root / "notes.md"
        notes.write_text("# Release v1.0.0\n")
        result = u.Infra.update_changelog(
            workspace_root,
            "1.0.0",
            "v1.0.0",
            notes,
        )
        tm.ok(result)
        tm.that((workspace_root / "docs" / "CHANGELOG.md").exists(), eq=True)

    def test_appends_to_existing(self, workspace_root: Path) -> None:
        changelog = workspace_root / "docs" / "CHANGELOG.md"
        changelog.parent.mkdir(parents=True)
        changelog.write_text("# Changelog\n\n## 0.9.0 - 2025-01-01\n")
        notes = workspace_root / "notes.md"
        notes.write_text("# Release v1.0.0\n")
        tm.ok(
            u.Infra.update_changelog(
                workspace_root,
                "1.0.0",
                "v1.0.0",
                notes,
            ),
        )
        tm.that(changelog.read_text(), contains="1.0.0")


class TestBumpNextDev:
    """Tests for _bump_next_dev."""

    def test_bumps_version(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        def _bump_ok(cur: str, kind: str) -> r[str]:
            _ = cur, kind
            return r[str].ok("1.1.0")

        monkeypatch.setattr(u.Infra, "bump_version", staticmethod(_bump_ok))

        def _phase_version(*a: t.Scalar, **kw: t.Scalar) -> r[bool]:
            del a, kw
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "phase_version",
            _phase_version,
        )
        tm.ok(
            FlextInfraReleaseOrchestrator()._bump_next_dev(
                workspace_root,
                "1.0.0",
                [],
                "minor",
            ),
        )

    def test_bump_failure(self, workspace_root: Path, monkeypatch: MonkeyPatch) -> None:
        def _bump_fail(cur: str, kind: str) -> r[str]:
            _ = cur, kind
            return r[str].fail("invalid bump")

        monkeypatch.setattr(u.Infra, "bump_version", staticmethod(_bump_fail))
        tm.fail(
            FlextInfraReleaseOrchestrator()._bump_next_dev(
                workspace_root,
                "1.0.0",
                [],
                "invalid",
            ),
        )


class TestDispatchPhase:
    """Tests for _dispatch_phase."""

    @staticmethod
    def _dispatch(
        orch: FlextInfraReleaseOrchestrator,
        phase: str,
        root: Path,
    ) -> r[bool]:
        config = m.Infra.ReleasePhaseDispatchConfig(
            phase=phase,
            workspace_root=root,
            version="1.0.0",
            tag="v1.0.0",
            project_names=[],
            dry_run=False,
            push=False,
            dev_suffix=False,
        )
        return orch._dispatch_phase(config)

    def test_unknown_phase(self, workspace_root: Path) -> None:
        result = self._dispatch(
            FlextInfraReleaseOrchestrator(),
            "unknown",
            workspace_root,
        )
        tm.fail(result)
        tm.that(result.error, contains="unknown phase")

    def test_routes_validate(
        self,
        workspace_root: Path,
        monkeypatch: MonkeyPatch,
    ) -> None:
        def _phase_validate(*a: t.Scalar, **kw: t.Scalar) -> r[bool]:
            del a, kw
            return r[bool].ok(True)

        monkeypatch.setattr(
            FlextInfraReleaseOrchestrator,
            "phase_validate",
            _phase_validate,
        )
        tm.ok(
            self._dispatch(
                FlextInfraReleaseOrchestrator(),
                "validate",
                workspace_root,
            ),
        )
