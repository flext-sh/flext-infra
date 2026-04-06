from __future__ import annotations

import fcntl
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import override

import pytest
from flext_tests import tf, tm
from tests import m, t

from flext_core import r
from flext_infra import (
    FlextInfraBaseMkGenerator,
    FlextInfraSyncService,
    FlextInfraWorkspaceMakefileGenerator,
    u,
)

_S = FlextInfraSyncService
SetupFn = Callable[[_S, pytest.MonkeyPatch], None]


def _stub_gen(content: str, *, fail: bool = False) -> FlextInfraBaseMkGenerator:
    class _Gen(FlextInfraBaseMkGenerator):
        def __init__(self) -> None:
            super().__init__()

        @override
        def generate_basemk(
            self,
            config: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
        ) -> r[str]:
            _ = self
            _ = config
            return r[str].fail(content) if fail else r[str].ok(content)

    return _Gen()


def _setup_lock_fail(_svc: _S, monkeypatch: pytest.MonkeyPatch) -> None:
    def _flock(_fd: int, _op: int) -> None:
        msg = "Lock failed"
        raise OSError(msg)

    monkeypatch.setattr(fcntl, "flock", _flock)


def _setup_gen_fail(svc: _S, _monkeypatch: pytest.MonkeyPatch) -> None:
    svc.generator = _stub_gen("Generation failed", fail=True)


def _setup_gitignore_fail(_svc: _S, monkeypatch: pytest.MonkeyPatch) -> None:
    def _open(*_args: t.Scalar, **_kwargs: t.Scalar) -> None:
        msg = "Write failed"
        raise OSError(msg)

    monkeypatch.setattr(Path, "open", _open)


@pytest.fixture
def svc(tmp_path: Path) -> _S:
    return _S(canonical_root=tmp_path, workspace=tmp_path)


@pytest.mark.parametrize(
    ("base_mk", "gitignore"),
    [("", ""), ("# Old content\n", ""), ("", "*.pyc\n")],
    ids=["empty", "existing-base-mk", "existing-gitignore"],
)
def test_sync_success_scenarios(
    svc: _S,
    tmp_path: Path,
    base_mk: str,
    gitignore: str,
) -> None:
    if base_mk:
        tf.create_in(base_mk, "base.mk", tmp_path)
    if gitignore:
        tf.create_in(gitignore, ".gitignore", tmp_path)
    tm.ok(svc.execute())
    tm.that((tmp_path / "base.mk").exists(), eq=True)


@pytest.mark.parametrize(
    ("project_root", "expected_error"),
    [
        (Path("/nonexistent/path"), "does not exist"),
    ],
    ids=["project-root-not-found"],
)
def test_sync_root_validation(project_root: Path, expected_error: str) -> None:
    tm.fail(_S(workspace=project_root).execute(), has=expected_error)


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["sync", "--workspace", "{tmp}"], 0),
        (["sync", "--workspace", "/nonexistent/path"], 1),
    ],
    ids=["cli-success", "cli-failure"],
)
def test_cli_result_by_project_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    argv: t.StrSequence,
    expected: int,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [str(tmp_path) if part == "{tmp}" else part for part in argv],
    )
    tm.that(FlextInfraSyncService.main(), eq=expected)


def test_cli_forwards_canonical_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Path | None] = {}

    def _execute(
        self: _S,
    ) -> r[m.Infra.SyncResult]:
        captured["workspace_root"] = self.workspace_root
        captured["canonical_root"] = self.canonical_root
        return r[m.Infra.SyncResult].ok(
            m.Infra.SyncResult(
                files_changed=0,
                source=self.workspace_root or Path(),
                target=self.workspace_root or Path(),
            ),
        )

    monkeypatch.setattr(_S, "execute", _execute)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "sync",
            "--workspace",
            str(tmp_path),
            "--canonical-root",
            str(tmp_path.parent),
        ],
    )
    tm.that(FlextInfraSyncService.main(), eq=0)
    tm.that(captured["workspace_root"], eq=tmp_path)
    tm.that(captured["canonical_root"], eq=tmp_path.parent)


@pytest.mark.parametrize(
    ("setup_fn", "expected_error"),
    [
        (_setup_lock_fail, "lock acquisition failed"),
        (_setup_gen_fail, "Generation failed"),
        (_setup_gitignore_fail, "Write failed"),
    ],
    ids=["lock-fail", "gen-fail", "gitignore-fail"],
)
def test_sync_error_scenarios(
    svc: _S,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    setup_fn: SetupFn,
    expected_error: str,
) -> None:
    setup_fn(svc, monkeypatch)
    tm.fail(svc.execute(), has=expected_error)


def test_gitignore_sync_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _S(workspace=tmp_path)

    def _ensure(*_args: t.Scalar, **_kwargs: t.Scalar) -> r[bool]:
        return r[bool].fail(".gitignore sync failed")

    monkeypatch.setattr(
        service,
        "_ensure_gitignore_entries",
        _ensure,
    )
    tm.fail(service.execute(), has=".gitignore sync failed")


def test_sync_updates_workspace_makefile_for_workspace_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _S(canonical_root=tmp_path, workspace=tmp_path)
    calls: list[str] = []

    def _workspace_makefile(_workspace_root: Path) -> r[bool]:
        calls.append("workspace")
        return r[bool].ok(True)

    def _project_makefile(
        _workspace_root: Path,
        _canonical_root: Path,
    ) -> r[bool]:
        calls.append("project")
        return r[bool].ok(True)

    monkeypatch.setattr(service, "_sync_workspace_makefile", _workspace_makefile)
    monkeypatch.setattr(service, "_sync_project_makefile", _project_makefile)
    tm.ok(service.execute())
    tm.that(calls, eq=["workspace"])


def test_workspace_makefile_generator_sanitizes_orchestrator_env(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    generator = FlextInfraWorkspaceMakefileGenerator()
    tm.ok(generator.generate(tmp_path))
    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    tm.that(
        makefile_text,
        has=[
            'WORKSPACE_PYTHON := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(WORKSPACE_PYTHONPATH)" $(PY)',
            'WORKSPACE_FLEXT_INFRA := FLEXT_WORKSPACE_ROOT="$(CURDIR)" $(WORKSPACE_PYTHON) -m flext_infra',
            "WORKSPACE_INFRA_WORKSPACE := $(WORKSPACE_FLEXT_INFRA) workspace",
            "ORCHESTRATOR := $(WORKSPACE_INFRA_WORKSPACE) orchestrate",
            'ORCHESTRATOR_PROJECTS := --projects "$(SELECTED_PROJECTS)"',
        ],
    )


def test_workspace_makefile_generator_declares_canonical_workspace_variables(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    generator = FlextInfraWorkspaceMakefileGenerator()
    tm.ok(generator.generate(tmp_path))
    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    tm.that(
        makefile_text,
        has=[
            "PROJECT ?=",
            "PROJECTS ?=",
            "DEPS_REPORT ?= 1",
            "PR_BRANCH ?= 0.1.0",
            "WORKSPACE_INFRA_DEPS := $(WORKSPACE_FLEXT_INFRA) deps",
            "WORKSPACE_INFRA_MAINTENANCE := $(WORKSPACE_FLEXT_INFRA) maintenance run",
            "WORKSPACE_INFRA_RELEASE := $(WORKSPACE_FLEXT_INFRA) release run",
            "WORKSPACE_INFRA_VALIDATE := $(WORKSPACE_FLEXT_INFRA) validate",
            "WORKSPACE_INFRA_GITHUB := $(WORKSPACE_FLEXT_INFRA) github",
        ],
    )


def test_workspace_makefile_generator_reuses_mod_and_boot_feedback(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    generator = FlextInfraWorkspaceMakefileGenerator()
    tm.ok(generator.generate(tmp_path))
    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    tm.that(makefile_text.count("$(MAKE) mod"), eq=2)
    tm.that(
        makefile_text,
        has=[
            "Run 'make boot'.",
            "Run 'make boot' first to create the environment.",
            "re-run: make boot",
        ],
    )


def test_sync_updates_project_makefile_for_standalone_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _S(workspace=tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\n", encoding="utf-8"
    )
    calls: list[str] = []

    def _workspace_makefile(_workspace_root: Path) -> r[bool]:
        calls.append("workspace")
        return r[bool].ok(True)

    def _project_makefile(
        _workspace_root: Path,
        _canonical_root: Path,
    ) -> r[bool]:
        calls.append("project")
        return r[bool].ok(True)

    monkeypatch.setattr(service, "_sync_workspace_makefile", _workspace_makefile)
    monkeypatch.setattr(service, "_sync_project_makefile", _project_makefile)
    tm.ok(service.execute())
    tm.that(calls, eq=["project"])


def test_sync_regenerates_project_makefile_without_legacy_passthrough(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='demo'\ndescription='Demo project'\nrequires-python='>=3.13'\n",
        encoding="utf-8",
    )
    (tmp_path / "Makefile").write_text(
        "# legacy custom target\ncustom-target:\n\t@echo legacy\n",
        encoding="utf-8",
    )

    tm.ok(_S(workspace=tmp_path).execute())

    makefile_text = (tmp_path / "Makefile").read_text(encoding="utf-8")
    tm.that("custom-target" in makefile_text, eq=False)
    tm.that(makefile_text, has="-include custom.mk")
    tm.that((tmp_path / "custom.mk").exists(), eq=False)


def test_atomic_write_ok(tmp_path: Path) -> None:
    target = tmp_path / "test.txt"
    tm.ok(u.Cli.atomic_write_text_file(target, "test content"), eq=True)
    tm.that(target.read_text(encoding="utf-8"), eq="test content")


def test_atomic_write_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _temp(*_args: t.Scalar, **_kwargs: t.Scalar) -> None:
        msg = "Temp file failed"
        raise OSError(msg)

    monkeypatch.setattr(
        tempfile,
        "mkstemp",
        _temp,
    )
    tm.fail(
        u.Cli.atomic_write_text_file(tmp_path / "t.txt", "c"),
        has="atomic_write_text_file",
    )


@pytest.mark.parametrize(
    ("generated", "ok_result", "expected"),
    [
        ("# Same content\n", True, True),
        ("Generation failed", False, "Generation failed"),
    ],
    ids=["no-change", "generation-failure"],
)
def test_sync_basemk_scenarios(
    tmp_path: Path,
    generated: str,
    ok_result: bool,
    expected: bool | str,
) -> None:
    service = _S()
    tf.create_in("# Same content\n", "base.mk", tmp_path)
    service.generator = _stub_gen(generated, fail=not ok_result)
    result = service._sync_basemk(tmp_path, None)
    if ok_result:
        tm.ok(result, eq=expected)
        return
    tm.fail(result, has=str(expected))


@pytest.mark.parametrize(
    ("initial_content", "entries", "expected"),
    [
        ("*.pyc\n", [".reports/", ".venv/"], True),
        (".reports/\n.venv/\n__pycache__/\n", [".reports/", ".venv/"], False),
    ],
    ids=["missing-entries", "entries-present"],
)
def test_gitignore_entry_scenarios(
    tmp_path: Path,
    initial_content: str,
    entries: t.StrSequence,
    expected: bool,
) -> None:
    tf.create_in(initial_content, ".gitignore", tmp_path)
    tm.ok(_S()._ensure_gitignore_entries(tmp_path, entries), eq=expected)
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    for entry in entries:
        tm.that(content, has=entry)


def test_gitignore_write_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tf.create_in("*.pyc\n", ".gitignore", tmp_path)

    def _open(*_args: t.Scalar, **_kwargs: t.Scalar) -> None:
        msg = "Write failed"
        raise OSError(msg)

    monkeypatch.setattr(
        Path,
        "open",
        _open,
    )
    tm.fail(
        _S()._ensure_gitignore_entries(tmp_path, [".reports/"]),
        has=".gitignore update failed",
    )
