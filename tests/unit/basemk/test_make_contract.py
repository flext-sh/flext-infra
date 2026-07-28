"""Execution tests for the generated canonical Make contract."""

from __future__ import annotations

import os
import stat
from typing import TYPE_CHECKING

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_tests import tm
from tests import p, u

if TYPE_CHECKING:
    from pathlib import Path


_ISOLATED_ENV_KEYS = (
    "APPLY",
    "CHECK_GATES",
    "MAKEFLAGS",
    "MAKELEVEL",
    "MAKEOVERRIDES",
    "MFLAGS",
    "PYTEST_ARGS",
    "UV",
    "UV_BUILD_EXIT",
    "UV_PROJECT",
    "UV_PROJECT_ENVIRONMENT",
    "VIRTUAL_ENV",
    "WHAT",
)


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _write_uv_stub(bin_dir: Path, log_path: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    _write_executable(
        bin_dir / "uv",
        "#!/bin/sh\n"
        f"printf 'uv %s\\n' \"$*\" >> '{log_path}'\n"
        'if [ "$1" = "venv" ]; then\n'
        '  target="$3"\n'
        '  mkdir -p "$target/bin"\n'
        "  printf '#!/bin/sh\\nexit 0\\n' > \"$target/bin/python\"\n"
        '  chmod +x "$target/bin/python"\n'
        "fi\n"
        'if [ "$1" = "build" ]; then exit "${UV_BUILD_EXIT:-0}"; fi\n'
        "exit 0\n",
    )


def _write_project(project_root: Path, log_path: Path) -> Path:
    rendered = tm.ok(FlextInfraBaseMkGenerator().generate_basemk())
    (project_root / "Makefile").write_text(rendered, encoding="utf-8")
    runtime_python = project_root / ".venv" / "bin" / "python"
    runtime_python.parent.mkdir(parents=True, exist_ok=True)
    _write_executable(runtime_python, "#!/bin/sh\nexit 0\n")
    bin_dir = project_root / "bin"
    _write_uv_stub(bin_dir, log_path)
    return bin_dir


def _run_make(
    project_root: Path, *args: str, bin_dir: Path, env: dict[str, str] | None = None
) -> p.Cli.CommandOutput:
    active_env = os.environ.copy()
    for key in _ISOLATED_ENV_KEYS:
        active_env.pop(key, None)
    active_env["PATH"] = f"{bin_dir}:{active_env['PATH']}"
    active_env["UV"] = str(bin_dir / "uv")
    if env is not None:
        active_env.update(env)
    return tm.ok(
        u.Cli.run_raw(
            ["make", *args],
            cwd=project_root,
            env=active_env,
            remove_env_keys=_ISOLATED_ENV_KEYS,
        )
    )


class TestsFlextInfraBasemkMakeContract:
    """Exercise the public generated Make verbs against real GNU Make."""

    def test_make_help_lists_the_canonical_surface(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(tmp_path, "help", bin_dir=bin_dir)

        tm.that(result.exit_code, eq=0)
        tm.that(
            result.stdout,
            has=[
                "unnamed [standalone]",
                "setup",
                "check      WHAT=all",
                "test       WHAT=all",
                "format     WHAT=check APPLY=Y",
                "codegen    WHAT=check APPLY=Y",
                "worktree   WHAT=list",
            ],
        )

    def test_make_setup_uses_unpinned_external_uv(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(tmp_path, "setup", bin_dir=bin_dir)

        tm.that(result.exit_code, eq=0)
        log = log_path.read_text(encoding="utf-8")
        tm.that(log, has=["uv venv --clear", "uv sync --project"])
        tm.that(log, has="uv pip install --python")
        tm.that(log, has="uv pip check --python")
        tm.that(log, lacks=["UV_VERSION", "3.13."])

    def test_make_build_uses_uv_and_preserves_failure(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(
            tmp_path, "build", bin_dir=bin_dir, env={"UV_BUILD_EXIT": "23"}
        )

        tm.that(result.exit_code, ne=0)
        tm.that(
            log_path.read_text(encoding="utf-8"), has=f"uv build --project {tmp_path}"
        )

    def test_make_check_runs_only_selected_gate(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "tests").mkdir()

        result = _run_make(tmp_path, "check", "CHECK_GATES=lint", bin_dir=bin_dir)

        tm.that(result.exit_code, eq=0)
        log = log_path.read_text(encoding="utf-8")
        tm.that(log, has="ruff check --no-fix")
        tm.that(log, lacks=["ruff format", "pyrefly", "mypy", "pyright"])

    def test_make_rejects_unknown_check_gate(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(tmp_path, "check", "CHECK_GATES=unknown", bin_dir=bin_dir)

        tm.that(result.exit_code, ne=0)
        tm.that(
            f"{result.stdout}\n{result.stderr}", has="unsupported CHECK_GATES: unknown"
        )

    def test_make_test_forwards_the_public_selector(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(
            tmp_path, "test", "PYTEST_ARGS=-k selected_case", bin_dir=bin_dir
        )

        tm.that(result.exit_code, eq=0)
        tm.that(
            log_path.read_text(encoding="utf-8"),
            has="python -m pytest -k selected_case",
        )

    def test_make_format_defaults_to_check_mode(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(tmp_path, "format", bin_dir=bin_dir)

        tm.that(result.exit_code, eq=0)
        log = log_path.read_text(encoding="utf-8")
        tm.that(log, has=["ruff check --no-fix", "ruff format --check"])
        tm.that(log, lacks="ruff check --fix")

    def test_make_apply_selects_the_guarded_apply_handler(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(tmp_path, "format", "APPLY=Y", bin_dir=bin_dir)

        tm.that(result.exit_code, eq=0)
        log = log_path.read_text(encoding="utf-8")
        tm.that(log, has=["ruff check --fix", "ruff format"])
        tm.that(log, lacks="ruff format --check")

    def test_make_runs_pre_and_post_hooks(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)
        hooks_path = tmp_path / "hooks.log"
        (tmp_path / "custom.mk").write_text(
            "pre-build:\n"
            f"\t@printf 'pre\\n' >> '{hooks_path}'\n"
            "post-build-artifacts:\n"
            f"\t@printf 'post\\n' >> '{hooks_path}'\n",
            encoding="utf-8",
        )

        result = _run_make(tmp_path, "build", bin_dir=bin_dir)

        tm.that(result.exit_code, eq=0)
        tm.that(hooks_path.read_text(encoding="utf-8"), eq="pre\npost\n")

    def test_make_rejects_unknown_what_without_fallback(self, tmp_path: Path) -> None:
        log_path = tmp_path / "uv.log"
        bin_dir = _write_project(tmp_path, log_path)

        result = _run_make(tmp_path, "build", "WHAT=unknown", bin_dir=bin_dir)

        tm.that(result.exit_code, ne=0)
        tm.that(f"{result.stdout}\n{result.stderr}", has="_custom_build_unknown")
