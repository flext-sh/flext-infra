"""Workspace Makefile dry-run tests through generated public targets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli, m as cli_m
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)
from flext_tests import tm

if TYPE_CHECKING:
    from pathlib import Path


def _write_workspace_makefile_fixture(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "pyproject.toml").write_text(
        (
            "[project]\n"
            "name = 'workspace-root'\n"
            "version = '0.1.0'\n"
            "\n"
            "[tool.flext.workspace]\n"
            "members = ['demo-a', 'demo-b']\n"
        ),
        encoding="utf-8",
    )
    (workspace_root / ".taplo.toml").write_text("", encoding="utf-8")
    for project_name in ("demo-a", "demo-b"):
        project_root = workspace_root / project_name
        project_root.mkdir()
        (project_root / "pyproject.toml").write_text(
            (f"[project]\nname = '{project_name}'\nversion = '0.1.0'\n"),
            encoding="utf-8",
        )
    result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
    tm.ok(result)
    return workspace_root


def _run_workspace_make_dry_run(
    workspace_root: Path,
    *args: str,
) -> cli_m.Cli.CommandOutput:
    outcome = cli.run_raw(
        ["make", "-C", str(workspace_root), "--dry-run", *args],
        remove_env_keys=(
            "CHANGED_ONLY",
            "CHECK_GATES",
            "DOCS_PHASE",
            "FAIL_FAST",
            "FILE",
            "FILES",
            "MAKEFLAGS",
            "MATCH",
            "PROJECT",
            "PROJECTS",
            "PYRIGHT_ARGS",
            "PYTEST_ARGS",
            "PR_BRANCH",
            "RUFF_ARGS",
            "VALIDATE_GATES",
            "VERBOSE",
            "WHAT",
        ),
    )
    if outcome.failure:
        msg = f"make dry-run invocation failed: {outcome.error}"
        raise RuntimeError(msg)
    return outcome.value


class TestsFlextInfraWorkspaceMakefileDryRun:
    """Behavior contract for test_makefile_dry_run."""

    def test_workspace_makefile_dry_run_mod_respects_project_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_mod", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="--projects demo-a")
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" demo-a/pyproject.toml'
            in output
        )
        tm.that(output, has="ruff format demo-a --quiet")
        tm.that(output, lacks="pyproject.toml */pyproject.toml")
        tm.that(output, lacks="ruff format . --quiet")

    def test_workspace_makefile_dry_run_mod_without_selection_uses_workspace_scope(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_mod")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="modernize --apply")
        # NOTE (multi-agent, mro-wkii.17.9): workspace rendering no longer
        # promises the removed deps path-sync command.
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" pyproject.toml demo-a/pyproject.toml demo-b/pyproject.toml'
            in output
        )
        tm.that(output, has="ruff format . --quiet")
        tm.that(output, lacks="--projects demo-a")
        tm.that(output, lacks="--projects demo-b")

    def test_workspace_makefile_dry_run_fmt_respects_project_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_fmt", "PROJECT=demo-b")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='_fmt_target="demo-b"')
        tm.that(output, has="ruff format $_fmt_target --quiet")
        tm.that(output, has='md_roots="demo-b"')
        tm.that(output, has="find \"$md_root\" -type f -name '*.md'")
        tm.that(output, lacks='_fmt_target="."')

    def test_workspace_makefile_dry_run_up_forwards_selection_to_mod_and_constraints(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_up", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='make _mod PROJECT="demo-a"')
        assert (
            "modernize --apply --rewrite-constraints --constraint-policy floor"
            in output
        )
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" demo-a/pyproject.toml'
            in output
        )
        tm.that(output, has="detect --quiet --no-fail")
        assert (
            f'--output "{workspace_root}/.reports/dependencies/detect-runtime-dev-latest.json"'
            in output
        )

    def test_workspace_makefile_dry_run_types_writes_dependency_report(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_types")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="detect --typings --quiet --no-fail")
        assert (
            f'--output "{workspace_root}/.reports/dependencies/detect-runtime-dev-latest.json"'
            in output
        )

    def test_workspace_makefile_dry_run_constraints_rewrites_dependency_floors(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(
            workspace_root,
            "_constraints",
            "PROJECT=demo-a",
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        assert (
            "modernize --apply --rewrite-constraints --constraint-policy floor"
            in output
        )
        tm.that(output, has="--projects demo-a")
        tm.that(output, lacks="path-sync --mode auto --apply")
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" demo-a/pyproject.toml'
            in output
        )

    def test_workspace_makefile_dry_run_gen_forwards_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_gen", "PROJECT=demo-b")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='--no-print-directory _mod PROJECT="demo-b"')
        tm.that(output, has='--no-print-directory _sync PROJECT="demo-b"')

    def test_workspace_makefile_dry_run_sync_respects_project_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_sync", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="workspace sync \\")
        tm.that(output, has=f'--workspace "{workspace_root}/$proj"')
        tm.that(output, has=f'--canonical-root "{workspace_root}"')
        tm.that(output, has="for proj in demo-a; do")
        tm.that(output, has=f'init --workspace "{workspace_root}/$proj" --apply')
        tm.that(output, lacks=f'workspace sync --workspace "{workspace_root}" --apply')

    def test_workspace_makefile_dry_run_ship_save_dispatches_to_registry(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "ship", "WHAT=save")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="save"')
        tm.that(output, has='PR_BRANCH="')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch ship")

    def test_workspace_makefile_dry_run_build_what_mod_dispatches_to_registry(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "build", "WHAT=mod")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="mod"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch build")

    def test_workspace_makefile_dry_run_build_default_runs_orchestrator(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "build")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT=""')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch build")

    def test_workspace_makefile_dry_run_check_what_pol_dispatches_to_registry(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "check", "WHAT=pol")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="pol"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch check")

    def test_workspace_makefile_dry_run_check_what_gate_forwards_check_gates(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "check", "WHAT=loc-cap")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="loc-cap"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch check")

    def test_workspace_makefile_dry_run_boot_what_stat_dispatches_to_registry(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "boot", "WHAT=stat")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="stat"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch boot")

    def test_workspace_makefile_dry_run_docs_dispatches_to_registry(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(
            workspace_root,
            "docs",
            "DOCS_PHASE=validate",
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='DOCS_PHASE="validate"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch docs")
