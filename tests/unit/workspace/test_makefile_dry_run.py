"""Workspace Makefile dry-run tests through generated public targets."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli, p as cli_p
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
    config_dir = workspace_root / "config"
    config_dir.mkdir()
    member_records = "".join(
        (
            f"\n  - name: {project_name}\n"
            f"    distribution: {project_name}\n"
            "    provider: flext-sh\n"
            f"    url: https://github.com/flext-sh/{project_name}.git\n"
            "    branch: main\n"
            f"    path: {project_name}\n"
            "    role: workspace-member\n"
            "    state: active\n"
            "    profile: workspace-member\n"
            "    checkout: submodule\n"
            "    codegen: conform\n"
            "    package: true\n"
            "    editable: true\n"
            "    read_only: false"
        )
        for project_name in ("demo-a", "demo-b")
    )
    (config_dir / "workspace.yaml").write_text(
        (
            "version: 2\n"
            "name: workspace-root\n"
            "repository:\n"
            "  name: workspace-root\n"
            "  distribution: workspace-root\n"
            "  provider: flext-sh\n"
            "  url: https://github.com/flext-sh/workspace-root.git\n"
            "  branch: main\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  profile: workspace-root\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            f"members:{member_records}\n"
            "content_only: []\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )
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
    workspace_root: Path, *args: str
) -> cli_p.Cli.CommandOutput:
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
        self, tmp_path: Path
    ) -> None:
        """Verify modernize and path sync honor one selected project."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_mod", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="--projects demo-a")
        tm.that(output, has="extra-paths --apply --projects demo-a")
        tm.that(output, lacks="pyproject.toml */pyproject.toml")
        tm.that(output, lacks=["taplo format", "ruff format"])

    def test_workspace_makefile_dry_run_mod_without_selection_uses_workspace_scope(
        self, tmp_path: Path
    ) -> None:
        """Verify unscoped modernization covers the workspace once."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_mod")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="modernize --apply")
        # NOTE (multi-agent, mro-wkii.17.9): workspace rendering no longer
        # promises the removed deps path-sync command.
        tm.that(output, has="extra-paths --apply")
        tm.that(output, lacks=["taplo format", "ruff format"])
        tm.that(output, lacks="--projects demo-a")
        tm.that(output, lacks="--projects demo-b")

    def test_workspace_makefile_dry_run_fmt_respects_project_selection(
        self, tmp_path: Path
    ) -> None:
        """Verify formatting targets only the selected project."""
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
        self, tmp_path: Path
    ) -> None:
        """Verify upgrade forwards project scope to every dependency phase."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_up", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='make _mod PROJECT="demo-a"')
        tm.that(
            output,
            has="modernize --apply --rewrite-constraints --constraint-policy floor",
        )
        tm.that(output, lacks="taplo format")
        tm.that(output, has="detect --quiet --no-fail")
        tm.that(
            output,
            has=f'--output "{workspace_root}/.reports/dependencies/detect-runtime-dev-latest.json"',
        )

    def test_workspace_makefile_dry_run_types_writes_dependency_report(
        self, tmp_path: Path
    ) -> None:
        """Verify the types route writes the canonical dependency report."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_types")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="detect --typings --quiet --no-fail")
        tm.that(
            output,
            has=f'--output "{workspace_root}/.reports/dependencies/detect-runtime-dev-latest.json"',
        )

    def test_workspace_makefile_dry_run_constraints_rewrites_dependency_floors(
        self, tmp_path: Path
    ) -> None:
        """Refresh the root lock before rewriting floors for the selected project."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(
            workspace_root, "_constraints", "PROJECT=demo-a"
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="uv lock --upgrade")
        tm.that(
            output,
            has="modernize --apply --rewrite-constraints --constraint-policy floor",
        )
        tm.that(output, has="--projects demo-a")
        tm.that(output, lacks="uv lock --directory")
        tm.that(output, lacks="path-sync --mode auto --apply")
        tm.that(output, lacks="taplo format")

    def test_workspace_makefile_dry_run_boot_composes_native_repair_targets(
        self, tmp_path: Path
    ) -> None:
        """Compose submodule repair before locked environment repair."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_boot_default")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        submodules_position = output.index("make --no-print-directory _boot_submodules")
        venv_position = output.index("make --no-print-directory _boot_venv")
        tm.that(submodules_position < venv_position, eq=True)
        tm.that(output, lacks=["uv lock", "uv lock --directory"])

    def test_workspace_makefile_dry_run_boot_venv_is_native_and_locked(
        self, tmp_path: Path
    ) -> None:
        """Repair the root environment without dispatcher or submodule operations."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_boot_venv")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(
            output,
            has="uv sync --locked --all-packages --all-groups --all-extras --reinstall",
        )
        tm.that(output, lacks=["uv lock", "submodule", "scripts.dispatch"])

    def test_workspace_makefile_dry_run_boot_submodules_isolated_from_venv(
        self, tmp_path: Path
    ) -> None:
        """Keep submodule repair isolated from environment mutation."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_boot_submodules")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has="git submodule update")
        tm.that(output, lacks=["uv sync", "uv lock", "scripts.dispatch"])

    def test_workspace_makefile_dry_run_gen_forwards_selection(
        self, tmp_path: Path
    ) -> None:
        """Verify generation forwards selection to modernization and sync."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "_gen", "PROJECT=demo-b")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='--no-print-directory _mod PROJECT="demo-b"')
        tm.that(output, has='--no-print-directory _sync PROJECT="demo-b"')

    def test_workspace_makefile_dry_run_sync_respects_project_selection(
        self, tmp_path: Path
    ) -> None:
        """Verify workspace sync iterates only the selected project."""
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
        self, tmp_path: Path
    ) -> None:
        """Verify ship-save dispatches through the command registry."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "ship", "WHAT=save")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="save"')
        tm.that(output, has='PR_BRANCH="')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch ship")

    def test_workspace_makefile_dry_run_build_what_mod_dispatches_to_registry(
        self, tmp_path: Path
    ) -> None:
        """Verify build-mod dispatches through the command registry."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "build", "WHAT=mod")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="mod"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch build")

    def test_workspace_makefile_dry_run_build_default_runs_orchestrator(
        self, tmp_path: Path
    ) -> None:
        """Verify default build dispatches the build orchestrator."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "build")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT=""')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch build")

    def test_workspace_makefile_dry_run_check_what_pol_dispatches_to_registry(
        self, tmp_path: Path
    ) -> None:
        """Verify the policy check dispatches through the command registry."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "check", "WHAT=pol")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="pol"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch check")

    def test_workspace_makefile_dry_run_check_what_gate_forwards_check_gates(
        self, tmp_path: Path
    ) -> None:
        """Verify named check gates are forwarded through dispatch."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "check", "WHAT=loc-cap")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="loc-cap"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch check")

    def test_workspace_makefile_dry_run_boot_what_stat_dispatches_to_registry(
        self, tmp_path: Path
    ) -> None:
        """Verify boot status dispatches through the command registry."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "boot", "WHAT=stat")
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='WHAT="stat"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch boot")

    def test_workspace_makefile_dry_run_docs_dispatches_to_registry(
        self, tmp_path: Path
    ) -> None:
        """Verify documentation phases dispatch through the registry."""
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(
            workspace_root, "docs", "DOCS_PHASE=validate"
        )
        output = process.stdout + process.stderr

        tm.that(process.exit_code, eq=0)
        tm.that(output, has='DOCS_PHASE="validate"')
        tm.that(output, has="uv run --all-packages python -m scripts.dispatch docs")
