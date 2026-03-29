"""Execution tests for the generated base.mk contract."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraBaseMkGenerator


def _render_base_mk() -> str:
    result = FlextInfraBaseMkGenerator().generate_basemk()
    tm.ok(result)
    return result.value


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_stubs(bin_dir: Path, log_path: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    _write_executable(
        bin_dir / "poetry",
        '#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "'
        + str(log_path)
        + '"\nexit 0\n',
    )
    _write_executable(
        bin_dir / "python",
        '#!/usr/bin/env bash\nprintf \'python %s\\n\' "$*" >> "'
        + str(log_path)
        + '"\nexit 0\n',
    )


def _write_project(project_root: Path, *, include_parent: bool = False) -> None:
    if include_parent:
        (project_root.parent / "base.mk").write_text(
            _render_base_mk(), encoding="utf-8"
        )
        makefile_content = "PROJECT_NAME := demo-project\ninclude ../base.mk\n"
    else:
        (project_root / "base.mk").write_text(_render_base_mk(), encoding="utf-8")
        makefile_content = "PROJECT_NAME := demo-project\ninclude base.mk\n"
    (project_root / "Makefile").write_text(makefile_content, encoding="utf-8")


def _run_make(
    project_root: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    active_env = os.environ.copy()
    for key in (
        "FILE",
        "FILES",
        "CHANGED_ONLY",
        "CHECK_GATES",
        "VALIDATE_GATES",
        "PYTEST_ARGS",
        "MATCH",
        "FAIL_FAST",
        "RUFF_ARGS",
        "PYRIGHT_ARGS",
        "CHECK_ONLY",
        "FIX",
        "MAKEFLAGS",
        "MFLAGS",
        "MAKELEVEL",
        "GNUMAKEFLAGS",
    ):
        active_env.pop(key, None)
    if env is not None:
        active_env.update(env)
    return subprocess.run(
        ["make", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        env=active_env,
    )


def test_make_help_lists_supported_options(tmp_path: Path) -> None:
    _write_project(tmp_path)
    result = _run_make(tmp_path, "help")
    tm.that(result.returncode, eq=0)
    tm.that(
        result.stdout,
        has=[
            "CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,go,type",
            "FILE=src/foo.py             Single file for check/fmt/test",
            'FILES="a.py b.py"          Multiple files for check/fmt/test',
            "CHANGED_ONLY=1              Git-changed Python files for check",
            'PYRIGHT_ARGS="--level basic" Extra args for pyright',
            "DIAG=1                      Emit extended pytest diagnostics",
            "FIX=1                       Auto-fix supported gates",
        ],
    )
    assert "check-fast" not in result.stdout


def test_make_check_file_scope_runs_mypy(tmp_path: Path) -> None:
    log_path = tmp_path / "tool.log"
    bin_dir = tmp_path / "bin"
    _write_stubs(bin_dir, log_path)
    _write_project(tmp_path)
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

    result = _run_make(
        tmp_path,
        "check",
        "FILE=src/demo.py",
        "CHECK_GATES=mypy",
        env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
    )

    tm.that(result.returncode, eq=0)
    tm.that(log_path.read_text(encoding="utf-8"), has="run mypy src/demo.py")


def test_make_check_file_scope_rejects_unsupported_gates(tmp_path: Path) -> None:
    _write_project(tmp_path)
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

    result = _run_make(
        tmp_path,
        "check",
        "FILE=src/demo.py",
        "CHECK_GATES=security",
    )

    tm.that(result.returncode, eq=2)
    tm.that(
        result.stdout + result.stderr,
        has="FILE/FILES/CHANGED_ONLY fast-path only supports lint,format,pyrefly,mypy,pyright",
    )


def test_make_boot_works_without_existing_venv_in_workspace_mode(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    project_root = workspace_root / "demo-project"
    project_root.mkdir(parents=True)
    log_path = workspace_root / "tool.log"
    bin_dir = workspace_root / "bin"
    _write_stubs(bin_dir, log_path)
    _write_project(project_root, include_parent=True)

    result = _run_make(
        project_root,
        "boot",
        env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
    )

    tm.that(result.returncode, eq=0)
    tm.that(
        log_path.read_text(encoding="utf-8"),
        has=[
            "python -m flext_infra workspace sync --workspace",
            "run python -m flext_infra deps path-sync --mode auto --apply --workspace",
            "python -m flext_infra deps internal-sync",
            "lock",
            "install --all-extras --all-groups",
        ],
    )
