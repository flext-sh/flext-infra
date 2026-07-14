"""Execution tests for the generated base.mk contract."""

from __future__ import annotations

import os
import stat
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from tests import m, p, u

if TYPE_CHECKING:
    from pathlib import Path

_MAKE_ISOLATION_ENV_KEYS = (
    "FLEXT_ROOT",
    "FLEXT_STANDALONE",
    "FLEXT_WORKSPACE_ROOT",
    "PROJECT",
    "PROJECTS",
    "WORKSPACE_ROOT",
)
_MAKE_TEST_ENV_KEYS = (
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
    "MAKEOVERRIDES",
    "MFLAGS",
    "MAKELEVEL",
    "GNUMAKEFLAGS",
    *_MAKE_ISOLATION_ENV_KEYS,
)


def _render_base_mk() -> str:
    result = FlextInfraBaseMkGenerator().generate_basemk()
    tm.ok(result)
    return result.unwrap()


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
    _write_executable(
        bin_dir / "uv",
        '#!/usr/bin/env bash\nprintf \'uv %s\\n\' "$*" >> "'
        + str(log_path)
        + '"\nif [ "$1" = "sync" ]; then\n'
        + "  mkdir -p .venv/bin\n"
        + '  cp "$(dirname "$0")/python" .venv/bin/python\n'
        + "fi\nexit 0\n",
    )


def _write_venv_python_stub(
    project_root: Path, log_path: Path, *, include_env: bool = False
) -> None:
    venv_bin = project_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    body = (
        "#!/usr/bin/env bash\nprintf "
        "'PYTHONPATH=%s MYPYPATH=%s python %s\\n' "
        '"${PYTHONPATH-unset}" "${MYPYPATH-unset}" "$*" >> "'
        + str(log_path)
        + '"\nexit 0\n'
        if include_env
        else '#!/usr/bin/env bash\nprintf \'python %s\\n\' "$*" >> "'
        + str(log_path)
        + '"\nexit 0\n'
    )
    _write_executable(venv_bin / "python", body)


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
) -> p.Cli.CommandOutput:
    active_env = os.environ.copy()
    for key in _MAKE_TEST_ENV_KEYS:
        active_env.pop(key, None)
    if env is not None:
        active_env.update(env)
    result = u.Cli.run_raw(
        ["make", *args],
        cwd=project_root,
        env=active_env,
        remove_env_keys=_MAKE_TEST_ENV_KEYS,
    )
    if result.success:
        return result.value
    return m.Cli.CommandOutput(
        stdout="", stderr=result.error or "make execution failed", exit_code=1
    )


class TestsFlextInfraBasemkMakeContract:
    """Behavior contract for test_make_contract."""

    def test_make_help_lists_supported_options(self, tmp_path: Path) -> None:
        """Expose every supported generated Make option through help."""
        _write_project(tmp_path)
        result = _run_make(tmp_path, "help")
        tm.that(result.exit_code, eq=0)
        tm.that(
            result.stdout,
            has=[
                "CHECK_GATES=lint,format,pyrefly,mypy,pyright,security,markdown,smells,type",
                "FILE=src/foo.py             Single file for check/fmt/test",
                'FILES="a.py b.py"          Multiple files for check/fmt/test',
                "CHANGED_ONLY=1              Git-changed Python files for check",
                "CHECK_ONLY=1                Dry-run format/check (no writes)",
                'PYRIGHT_ARGS="--level basic" Extra args for pyright',
                "DIAG=1                      Emit extended pytest diagnostics",
                "FIX=1                       Auto-fix supported gates",
            ],
        )
        tm.that(result.stdout, lacks="check-fast")

    def test_rendered_base_mk_declares_cli_group_roots(self) -> None:
        """Declare each canonical flext-infra CLI group command."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has=[
                "PROJECT_INFRA_HOME := $(WORKSPACE_ROOT)/flext-infra",
                "PROJECT_INFRA_SRC := $(PROJECT_INFRA_HOME)/src",
                'PROJECT_INFRA_BOOT := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(PROJECT_INFRA_SRC)" $(POETRY) run python -m flext_infra',
                'PROJECT_INFRA_ROOT := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(PROJECT_INFRA_SRC)" $(VENV_PYTHON) -m flext_infra',
                'PROJECT_INFRA_CHECK := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) check',
                'PROJECT_INFRA_CODEGEN := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) codegen',
                'PROJECT_INFRA_DEPS := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_BOOT) deps',
                'PROJECT_INFRA_DOCS := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) docs',
                'PROJECT_INFRA_GITHUB := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) github',
                'PROJECT_INFRA_VALIDATE := FLEXT_WORKSPACE_ROOT="$(WORKSPACE_ROOT)" $(PROJECT_INFRA_ROOT) validate',
            ],
        )

    def test_rendered_base_mk_sanitizes_workspace_validation_env(self) -> None:
        """Sanitize inherited Python paths for workspace validation."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has='BASE_INFRA_VALIDATE := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(WORKSPACE_ROOT)/flext-infra/src" $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python) -m flext_infra validate',
        )

    def test_rendered_base_mk_keeps_workspace_preflight_read_only(self) -> None:
        """Validate canonical state without applying or deleting files."""
        rendered = _render_base_mk()
        preflight = rendered.split("define VALIDATE_CANONICAL_BASE_MK", 1)[1].split(
            "endef", 1
        )[0]
        tm.that(
            preflight,
            has=[
                'basemk-validate --workspace "$(WORKSPACE_ROOT)"',
                "build WHAT=sync PROJECT=$(PROJECT_NAME)",
            ],
            lacks=["workspace sync", "--apply"],
        )
        tm.that(
            rendered,
            has="Project-local .venv violates the workspace environment contract",
            lacks="rm -rf .venv",
        )
        tm.that(
            rendered, has='basemk-validate --workspace "$(WORKSPACE_ROOT)/flext-infra"'
        )
        tm.that(rendered, lacks="AUTO_SYNC_BASE_AND_SCRIPTS")

    def test_rendered_base_mk_disables_addopts_coverage_for_filtered_tests(
        self,
    ) -> None:
        """Avoid mixing filtered test selection with whole-suite coverage."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has='if [ -n "$$_files" ] || [ -n "$(MATCH)" ]; then _coverage_args="--no-cov"; fi;',
        )

    def test_rendered_base_mk_changed_only_filters_deleted_and_untracked(self) -> None:
        """Select only extant tracked or untracked Python files."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has=[
                "git diff --name-only --diff-filter=ACMRTUXB HEAD -- '*.py'",
                "git ls-files --others --exclude-standard -- '*.py'",
            ],
        )

    def test_make_check_file_scope_runs_mypy(self, tmp_path: Path) -> None:
        """Dispatch a file-scoped Mypy check through the generated Makefile."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_stubs(bin_dir, log_path)
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, log_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

        result = _run_make(
            tmp_path,
            "check",
            "FILE=src/demo.py",
            "CHECK_GATES=mypy",
            env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        )

        tm.that(result.exit_code, eq=0)
        tm.that(log_path.read_text(encoding="utf-8"), has="run mypy src/demo.py")

    def test_make_check_file_scope_unsets_python_path_env(self, tmp_path: Path) -> None:
        """Remove inherited Python path variables from file-scoped checks."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        _write_executable(
            bin_dir / "poetry",
            '#!/usr/bin/env bash\nprintf \'PYTHONPATH=%s MYPYPATH=%s %s\\n\' "${PYTHONPATH-unset}" "${MYPYPATH-unset}" "$*" >> "'
            + str(log_path)
            + '"\nexit 0\n',
        )
        _write_executable(
            bin_dir / "python",
            '#!/usr/bin/env bash\nprintf \'python %s\\n\' "$*" >> "'
            + str(log_path)
            + '"\nexit 0\n',
        )
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, log_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

        result = _run_make(
            tmp_path,
            "check",
            "FILE=src/demo.py",
            "CHECK_GATES=mypy",
            env={
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
                "PYTHONPATH": str(tmp_path / "poison-pythonpath"),
                "MYPYPATH": str(tmp_path / "poison-mypypath"),
            },
        )

        tm.that(result.exit_code, eq=0)
        tm.that(
            log_path.read_text(encoding="utf-8"),
            has="PYTHONPATH=unset MYPYPATH=unset run mypy src/demo.py",
        )

    def test_make_check_full_run_unsets_python_path_env(self, tmp_path: Path) -> None:
        """Replace inherited Python paths with the canonical source root."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        _write_executable(
            bin_dir / "poetry",
            '#!/usr/bin/env bash\nprintf \'PYTHONPATH=%s MYPYPATH=%s %s\\n\' "${PYTHONPATH-unset}" "${MYPYPATH-unset}" "$*" >> "'
            + str(log_path)
            + '"\nexit 0\n',
        )
        _write_executable(
            bin_dir / "python",
            '#!/usr/bin/env bash\nprintf \'python %s\\n\' "$*" >> "'
            + str(log_path)
            + '"\nexit 0\n',
        )
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, log_path, include_env=True)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

        result = _run_make(
            tmp_path,
            "check",
            "CHECK_GATES=mypy",
            env={
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
                "PYTHONPATH": str(tmp_path / "poison-pythonpath"),
                "MYPYPATH": str(tmp_path / "poison-mypypath"),
            },
        )

        tm.that(result.exit_code, eq=0)
        expected_src = tmp_path / "src"
        tm.that(
            log_path.read_text(encoding="utf-8"),
            has=(
                f"PYTHONPATH={expected_src} MYPYPATH=unset "
                f"python -m flext_infra check run --workspace {tmp_path} --gates mypy"
            ),
        )

    def test_make_check_full_run_forwards_fix_and_tool_args(
        self, tmp_path: Path
    ) -> None:
        """Forward explicit fix and analyzer arguments to the check service."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_stubs(bin_dir, log_path)
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, log_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

        result = _run_make(
            tmp_path,
            "check",
            "CHECK_GATES=lint,pyright",
            "FIX=1",
            "RUFF_ARGS=--select E501",
            "PYRIGHT_ARGS=--level basic",
            env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        )

        tm.that(result.exit_code, eq=0)
        tm.that(
            log_path.read_text(encoding="utf-8"),
            has=(
                f"python -m flext_infra check run --workspace {tmp_path} --gates lint,pyright --reports-dir "
            ),
        )
        tm.that(
            log_path.read_text(encoding="utf-8"),
            has="--projects . --fix --ruff-args --select E501 --pyright-args --level basic",
        )

    def test_make_check_fast_path_check_only_suppresses_fix_writes(
        self, tmp_path: Path
    ) -> None:
        """Keep check-only file gates read-only even when fix is requested."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_stubs(bin_dir, log_path)
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, log_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

        result = _run_make(
            tmp_path,
            "check",
            "FILE=src/demo.py",
            "CHECK_GATES=lint",
            "FIX=1",
            "CHECK_ONLY=1",
            env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        )

        tm.that(result.exit_code, eq=0)
        tm.that(log_path.read_text(encoding="utf-8"), has="run ruff check src/demo.py")
        tm.that("--fix" not in log_path.read_text(encoding="utf-8"), eq=True)

    def test_make_check_file_scope_rejects_unsupported_gates(
        self, tmp_path: Path
    ) -> None:
        """Reject full-project gates from the file-scoped fast path."""
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, tmp_path / "tool.log")
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")

        result = _run_make(
            tmp_path, "check", "FILE=src/demo.py", "CHECK_GATES=security"
        )

        tm.that(result.exit_code, eq=2)
        tm.that(
            result.stdout + result.stderr,
            has="FILE/FILES/CHANGED_ONLY fast-path only supports lint,format,pyrefly,mypy,pyright",
        )

    def test_make_boot_works_without_existing_venv_in_workspace_mode(
        self, tmp_path: Path
    ) -> None:
        """Bootstrap workspace mode before the canonical environment exists."""
        workspace_root = tmp_path / "workspace"
        project_root = workspace_root / "demo-project"
        project_root.mkdir(parents=True)
        log_path = workspace_root / "tool.log"
        bin_dir = workspace_root / "bin"
        _write_stubs(bin_dir, log_path)
        _write_project(project_root, include_parent=True)

        result = _run_make(
            project_root, "boot", env={"PATH": f"{bin_dir}:{os.environ['PATH']}"}
        )

        tm.that(result.exit_code, eq=0)
        log_content = log_path.read_text(encoding="utf-8")
        tm.that(
            log_content,
            has=[
                f"python -m flext_infra validate basemk-validate --workspace {workspace_root}",
                # NOTE (multi-agent, mro-wkii.17.9): path-sync is not part of
                # the generated Make contract; conform owns pyproject output.
                "python -m flext_infra deps internal-sync",
                "uv lock",
                "uv sync --all-extras --all-groups",
            ],
        )
        tm.that(log_content, lacks="workspace sync")
