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
    "BASH_ENV",
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
    rendered: str = tm.ok(result)
    return rendered


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


def _write_mise_stub(bin_dir: Path, log_path: Path, *, exit_code: int) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    _write_executable(
        bin_dir / "mise",
        '#!/bin/sh\nprintf \'mise %s\\n\' "$*" >> "'
        + str(log_path)
        + f'"\nexit {exit_code}\n',
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


def _write_pytest_diag_python_stub(
    project_root: Path, *, payload: str, exit_code: int
) -> None:
    venv_bin = project_root / ".venv" / "bin"
    venv_bin.mkdir(parents=True, exist_ok=True)
    body = (
        "#!/usr/bin/env bash\n"
        "junit_file=''\n"
        'for argument in "$@"; do\n'
        '  case "$argument" in --junitxml=*) junit_file="${argument#--junitxml=}" ;; esac\n'
        "done\n"
        'if [[ "$*" == *"-m pytest"* ]]; then\n'
        '  printf \'<testsuite tests="1" failures="0" errors="0" skipped="0" time="0.1"/>\\n\' > "$junit_file"\n'
        "  exit 0\n"
        "fi\n"
        'if [[ "$*" == *"-m flext_infra validate pytest-diag"* ]]; then\n'
        "  cat <<'FLEXT_PYTEST_DIAG_COUNTS'\n"
        f"{payload.rstrip()}\n"
        "FLEXT_PYTEST_DIAG_COUNTS\n"
        f"  exit {exit_code}\n"
        "fi\n"
        "exit 97\n"
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

    def test_make_verb_runs_pre_and_post_hooks_from_custom_mk(
        self, tmp_path: Path
    ) -> None:
        """A member verb runs custom.mk pre-<verb> and post-<verb> around its body."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_stubs(bin_dir, log_path)
        _write_project(tmp_path)
        _write_venv_python_stub(tmp_path, log_path)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "demo.py").write_text("x = 1\n", encoding="utf-8")
        # Real member Makefiles -include custom.mk (see flext-core/Makefile);
        # replicate that so the verb hook seam can see the custom hooks.
        (tmp_path / "Makefile").write_text(
            "PROJECT_NAME := demo-project\ninclude base.mk\n-include custom.mk\n",
            encoding="utf-8",
        )
        (tmp_path / "custom.mk").write_text(
            ".PHONY: pre-check post-check\n"
            "pre-check:\n\t@echo HOOK_PRE_CHECK\n"
            "post-check:\n\t@echo HOOK_POST_CHECK\n",
            encoding="utf-8",
        )
        result = _run_make(
            tmp_path,
            "check",
            "FILE=src/demo.py",
            "CHECK_GATES=mypy",
            env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        )
        output = result.stdout + result.stderr
        tm.that(result.exit_code, eq=0)
        pre_at = output.find("HOOK_PRE_CHECK")
        post_at = output.find("HOOK_POST_CHECK")
        tm.that(pre_at >= 0 and post_at >= 0, eq=True)
        tm.that(pre_at < post_at, eq=True)

    def test_make_verb_runs_what_scoped_and_verb_wide_hooks_in_order(
        self, tmp_path: Path
    ) -> None:
        """pre/post hooks run verb-wide and WHAT-scoped, ordered around the body."""
        _write_project(tmp_path)
        (tmp_path / "Makefile").write_text(
            "PROJECT_NAME := demo-project\ninclude base.mk\n-include custom.mk\n",
            encoding="utf-8",
        )
        _write_pytest_diag_python_stub(
            tmp_path,
            payload=(
                "failed_count=0\nerror_count=0\nwarning_count=0\nskipped_count=0"
            ),
            exit_code=0,
        )
        (tmp_path / "custom.mk").write_text(
            ".PHONY: pre-test post-test pre-test-contract post-test-contract\n"
            "pre-test:\n\t@echo H_PRE_TEST\n"
            "pre-test-contract:\n\t@echo H_PRE_TEST_CONTRACT\n"
            "post-test-contract:\n\t@echo H_POST_TEST_CONTRACT\n"
            "post-test:\n\t@echo H_POST_TEST\n",
            encoding="utf-8",
        )
        result = _run_make(tmp_path, "test", "DIAG=1", "MATCH=contract", "WHAT=contract")
        tm.that(result.exit_code, eq=0)
        # The pytest body reports DIAG on stderr; the four hooks print on stdout.
        # Assert the hook ordering on stdout (verb-wide before WHAT-scoped for pre,
        # WHAT-scoped before verb-wide for post) and that the body actually ran.
        stdout = result.stdout
        order = [
            stdout.find("H_PRE_TEST"),
            stdout.find("H_PRE_TEST_CONTRACT"),
            stdout.find("H_POST_TEST_CONTRACT"),
            stdout.find("H_POST_TEST"),
        ]
        tm.that(all(position >= 0 for position in order), eq=True)
        tm.that(order == sorted(order), eq=True)
        tm.that(result.stdout + result.stderr, has="DIAG COMPLETED")

    def test_make_verbs_dispatch_custom_what_handlers(self, tmp_path: Path) -> None:
        """Every verb runs _custom_<verb>_<what> from custom.mk for a custom WHAT."""
        _write_project(tmp_path)
        (tmp_path / "Makefile").write_text(
            "PROJECT_NAME := demo-project\ninclude base.mk\n-include custom.mk\n",
            encoding="utf-8",
        )
        (tmp_path / "custom.mk").write_text(
            ".PHONY: _custom_build_proto _custom_test_dbt _custom_docs_dbt "
            "_custom_run_x\n"
            "_custom_build_proto:\n\t@echo CUSTOM_BUILD_PROTO\n"
            "_custom_test_dbt:\n\t@echo CUSTOM_TEST_DBT\n"
            "_custom_docs_dbt:\n\t@echo CUSTOM_DOCS_DBT\n"
            "_custom_run_x:\n\t@echo CUSTOM_RUN_X\n",
            encoding="utf-8",
        )
        for verb, what, marker in (
            ("build", "proto", "CUSTOM_BUILD_PROTO"),
            ("test", "dbt", "CUSTOM_TEST_DBT"),
            ("docs", "dbt", "CUSTOM_DOCS_DBT"),
            ("run", "x", "CUSTOM_RUN_X"),
        ):
            result = _run_make(tmp_path, verb, f"WHAT={what}")
            output = result.stdout + result.stderr
            tm.that(result.exit_code, eq=0)
            tm.that(output, has=marker)

    def test_make_run_verb_requires_and_validates_what(self, tmp_path: Path) -> None:
        """run needs WHAT and fails clearly when the custom handler is absent."""
        _write_project(tmp_path)
        (tmp_path / "Makefile").write_text(
            "PROJECT_NAME := demo-project\ninclude base.mk\n-include custom.mk\n",
            encoding="utf-8",
        )
        (tmp_path / "custom.mk").write_text("# no handlers\n", encoding="utf-8")
        no_what = _run_make(tmp_path, "run")
        tm.that(no_what.exit_code, ne=0)
        tm.that(no_what.stdout + no_what.stderr, has="requires WHAT")
        missing = _run_make(tmp_path, "run", "WHAT=nope")
        tm.that(missing.exit_code, ne=0)
        tm.that(missing.stdout + missing.stderr, has="no custom handler")


    def test_make_build_uses_mise_uv_and_propagates_failure(
        self, tmp_path: Path
    ) -> None:
        """Fail the target when the Mise-managed uv builder fails."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_mise_stub(bin_dir, log_path, exit_code=23)
        _write_project(tmp_path)

        result = _run_make(
            tmp_path, "build", env={"PATH": f"{bin_dir}:{os.environ['PATH']}"}
        )

        tm.that(result.exit_code, ne=0)
        tm.that(
            log_path.read_text(encoding="utf-8").splitlines(),
            eq=[f"mise exec -- uv build --project {tmp_path} --no-sources"],
        )
        tm.that(result.stdout, lacks="Build complete")

    def test_make_help_lists_supported_options(self, tmp_path: Path) -> None:
        """Verify generated help advertises every supported option."""
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

    def test_make_help_documents_and_lists_custom_hooks(self, tmp_path: Path) -> None:
        """Help documents the hook contract and lists custom.mk-defined hooks."""
        _write_project(tmp_path)
        (tmp_path / "Makefile").write_text(
            "PROJECT_NAME := demo-project\ninclude base.mk\n-include custom.mk\n",
            encoding="utf-8",
        )
        (tmp_path / "custom.mk").write_text(
            ".PHONY: pre-check post-test-all _custom_check_myscan\n"
            "pre-check:\n\t@true\n"
            "post-test-all:\n\t@true\n"
            "_custom_check_myscan:\n\t@true\n",
            encoding="utf-8",
        )
        result = _run_make(tmp_path, "help")
        tm.that(result.exit_code, eq=0)
        # The hook contract is documented.
        tm.that(
            result.stdout,
            has=[
                "Custom hooks",
                "pre-<verb>",
                "post-<verb>",
            ],
        )
        # The actual custom.mk hooks and custom WHATs are discovered and listed.
        tm.that(
            result.stdout,
            has=[
                "pre-check",
                "post-test-all",
                "_custom_check_myscan",
            ],
        )


    def test_rendered_base_mk_declares_cli_group_roots(self) -> None:
        """Verify generated command roots use canonical CLI groups."""
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

    def test_rendered_base_mk_sanitizes_validation_env(self) -> None:
        """Verify base validation clears inherited Python import paths."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has='BASE_INFRA_VALIDATE := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(WORKSPACE_ROOT)/flext-infra/src" $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python) -m flext_infra validate',
        )

    def test_rendered_base_mk_validates_canonical_root_in_workspace_preflight(
        self,
    ) -> None:
        """Verify project preflight validates the canonical workspace root."""
        rendered = _render_base_mk()
        tm.that(
            rendered, has='basemk-validate --workspace "$(WORKSPACE_ROOT)/flext-infra"'
        )
        tm.that(rendered, lacks="AUTO_SYNC_BASE_AND_SCRIPTS")

    def test_rendered_base_mk_disables_addopts_coverage_for_filtered_tests(
        self,
    ) -> None:
        """Verify filtered test runs disable global coverage addopts."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has='if [ -n "$$_files" ] || [ -n "$(MATCH)" ]; then _coverage_args="--no-cov"; fi;',
        )

    def test_rendered_base_mk_preserves_project_coverage_source(self) -> None:
        """Keep coverage source owned by each project's pytest configuration."""
        rendered = _render_base_mk()
        tm.that(rendered, has='_coverage_args="--cov-report=xml:$$coverage_file";')
        tm.that(rendered, lacks='_coverage_args="--cov=$(SRC_DIR)')
        tm.that(rendered, lacks='_coverage_args="--cov --cov-report')

    def test_make_pytest_diag_accepts_exact_numeric_counts(
        self, tmp_path: Path
    ) -> None:
        """Accept the four-key machine-output contract before sourcing it."""
        _write_project(tmp_path)
        _write_pytest_diag_python_stub(
            tmp_path,
            payload=("failed_count=0\nerror_count=0\nwarning_count=0\nskipped_count=0"),
            exit_code=0,
        )

        result = _run_make(tmp_path, "test", "DIAG=1", "MATCH=contract")

        tm.that(result.exit_code, eq=0)
        tm.that(
            result.stdout + result.stderr,
            has="DIAG COMPLETED | failed=0 errors=0 warnings=0 skipped=0",
        )

    def test_make_pytest_diag_preserves_producer_failure(self, tmp_path: Path) -> None:
        """Stop with the producer status and its exact stdout evidence."""
        _write_project(tmp_path)
        _write_pytest_diag_python_stub(
            tmp_path, payload="diagnostic producer failed", exit_code=23
        )

        result = _run_make(tmp_path, "test", "DIAG=1", "MATCH=contract")

        output = result.stdout + result.stderr
        tm.that(result.exit_code, ne=0)
        tm.that(output, has="pytest diagnostic extraction failed (exit=23)")
        tm.that(output, has="diagnostic producer failed")

    def test_make_pytest_diag_rejects_payload_before_sourcing(
        self, tmp_path: Path
    ) -> None:
        """Reject shell text from a successful producer without executing it."""
        marker = tmp_path / "injected-marker"
        _write_project(tmp_path)
        _write_pytest_diag_python_stub(
            tmp_path,
            payload=(f"failed_count=0\nerror_count=0\ntouch {marker}\nskipped_count=0"),
            exit_code=0,
        )

        result = _run_make(tmp_path, "test", "DIAG=1", "MATCH=contract")

        output = result.stdout + result.stderr
        tm.that(result.exit_code, ne=0)
        tm.that(output, has="invalid pytest diagnostic counts contract")
        tm.that(marker.exists(), eq=False)

    def test_rendered_base_mk_changed_only_filters_deleted_and_untracked(self) -> None:
        """Verify changed-only discovery includes live tracked and untracked files."""
        rendered = _render_base_mk()
        tm.that(
            rendered,
            has=[
                "git diff --name-only --diff-filter=ACMRTUXB HEAD -- '*.py'",
                "git ls-files --others --exclude-standard -- '*.py'",
            ],
        )

    def test_make_check_file_scope_runs_mypy(self, tmp_path: Path) -> None:
        """Verify file-scoped checks invoke Mypy for the selected file."""
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

    def test_rendered_base_mk_bounds_every_mypy_process(self) -> None:
        """Verify generated Mypy and dmypy commands inherit the finite cap."""
        rendered = _render_base_mk()
        tm.that(rendered, has="MYPY_MEMORY_LIMIT_MB ?= 6144")
        tm.that(rendered, has="MYPY_TIMEOUT_SECONDS ?= 600")
        tm.that(
            rendered,
            has='timeout --signal=TERM --kill-after=5s "$(MYPY_TIMEOUT_SECONDS)s" prlimit --as=$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )):$$(( $(MYPY_MEMORY_LIMIT_MB) * 1024 * 1024 )) --',
        )
        tm.that(rendered, has="MYPY_MEMORY_LIMIT_MB must be a positive integer")
        tm.that(rendered, has="MYPY_MEMORY_LIMIT_MB must be less than or equal to 6144")
        tm.that(rendered, has="MYPY_TIMEOUT_SECONDS must be a positive integer")
        tm.that(rendered, has="MYPY_TIMEOUT_SECONDS must be less than or equal to 600")
        tm.that(rendered, has='if [ "$$code" -eq 124 ]')
        tm.that(rendered, has="Mypy $$reason")
        tm.that(rendered.count("$(MYPY_BOUNDED)"), eq=6)

    def test_make_mypy_semantic_failure_is_not_reported_as_resource_limit(
        self, tmp_path: Path
    ) -> None:
        """Keep an ordinary Mypy diagnostic distinct from a resource failure."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_stubs(bin_dir, log_path)
        _write_executable(
            bin_dir / "poetry",
            "#!/usr/bin/env bash\n"
            "echo 'demo.py:1: error: incompatible type' >&2\n"
            "exit 1\n",
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
            env={"PATH": f"{bin_dir}:{os.environ['PATH']}"},
        )

        output = result.stdout + result.stderr
        tm.that(result.exit_code, ne=0)
        tm.that(output, has="Mypy type check failed under enforced limits")
        tm.that("Mypy resource limit triggered" in output, eq=False)

    def test_make_mypy_timeout_is_reported_as_resource_limit(
        self, tmp_path: Path
    ) -> None:
        """Classify the timeout wrapper's exit code as a resource failure."""
        log_path = tmp_path / "tool.log"
        bin_dir = tmp_path / "bin"
        _write_stubs(bin_dir, log_path)
        _write_executable(bin_dir / "poetry", "#!/usr/bin/env bash\nexit 124\n")
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

        output = result.stdout + result.stderr
        tm.that(result.exit_code, ne=0)
        tm.that(output, has="Mypy resource limit triggered")

    def test_make_daemon_start_dry_run_sets_server_timeout(
        self, tmp_path: Path
    ) -> None:
        """Keep the persistent dmypy server bounded without starting it."""
        _write_project(tmp_path)

        result = _run_make(tmp_path, "--dry-run", "daemon-start-mypy")

        tm.that(result.exit_code, eq=0)
        tm.that(result.stdout, has='start --timeout "600" -- --config-file')

    def test_make_check_file_scope_unsets_python_path_env(self, tmp_path: Path) -> None:
        """Verify file-scoped checks clear inherited Python path variables."""
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
        """Verify full checks clear inherited Python path variables."""
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
        """Verify full checks forward fix and analyzer arguments."""
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
        """Verify check-only fast paths never forward write-enabled fixes."""
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
        """Verify file-scoped checks reject gates without fast-path support."""
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
        """Verify boot invokes dependency setup without requiring an existing venv."""
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
                "run python -m flext_infra deps extra-paths",
                "uv lock",
                "uv sync --all-extras --all-groups",
            ],
        )
