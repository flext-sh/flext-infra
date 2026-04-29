"""Workspace Makefile dry-run tests through generated public targets."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from flext_infra import FlextInfraWorkspaceMakefileGenerator


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
    assert result.success, result.error
    return workspace_root


def _run_workspace_make_dry_run(
    workspace_root: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key in (
        "CHANGED_ONLY",
        "CHECK_GATES",
        "FAIL_FAST",
        "FILE",
        "FILES",
        "MAKEFLAGS",
        "MATCH",
        "PROJECT",
        "PROJECTS",
        "PYRIGHT_ARGS",
        "PYTEST_ARGS",
        "RUFF_ARGS",
        "VALIDATE_GATES",
        "VERBOSE",
    ):
        env.pop(key, None)
    return subprocess.run(
        ["make", "-C", str(workspace_root), "--dry-run", *args],
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )


class TestsFlextInfraWorkspaceMakefileDryRun:
    """Behavior contract for test_makefile_dry_run."""

    def test_workspace_makefile_dry_run_mod_respects_project_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "mod", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert "--projects demo-a" in output
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" demo-a/pyproject.toml'
            in output
        )
        assert "ruff format demo-a --quiet" in output
        assert "pyproject.toml */pyproject.toml" not in output
        assert "ruff format . --quiet" not in output

    def test_workspace_makefile_dry_run_mod_without_selection_uses_workspace_scope(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "mod")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert "modernize --apply" in output
        assert "path-sync --mode auto --apply" in output
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" pyproject.toml demo-a/pyproject.toml demo-b/pyproject.toml'
            in output
        )
        assert "ruff format . --quiet" in output
        assert "--projects demo-a" not in output
        assert "--projects demo-b" not in output

    def test_workspace_makefile_dry_run_fmt_respects_project_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "fmt", "PROJECT=demo-b")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert '_fmt_target="demo-b"' in output
        assert "ruff format $_fmt_target --quiet" in output
        assert "find demo-b -type f -name '*.go'" in output
        assert 'md_roots="demo-b"' in output
        assert "find \"$md_root\" -type f -name '*.md'" in output
        assert '_fmt_target="."' not in output

    def test_workspace_makefile_dry_run_up_forwards_selection_to_mod_and_constraints(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "up", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert 'make mod PROJECT="demo-a"' in output
        assert (
            "modernize --apply --rewrite-constraints --constraint-policy floor"
            in output
        )
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" demo-a/pyproject.toml'
            in output
        )
        assert "detect --quiet --no-fail" in output
        assert (
            f'--output "{workspace_root}/.reports/dependencies/detect-runtime-dev-latest.json"'
            in output
        )

    def test_workspace_makefile_dry_run_types_writes_dependency_report(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "types")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert "detect --typings --quiet --no-fail" in output
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
            "constraints",
            "PROJECT=demo-a",
        )
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert (
            "modernize --apply --rewrite-constraints --constraint-policy floor"
            in output
        )
        assert "--projects demo-a" in output
        assert "path-sync --mode auto --apply" not in output
        assert (
            f'taplo format --config "{workspace_root}/.taplo.toml" demo-a/pyproject.toml'
            in output
        )

    def test_workspace_makefile_dry_run_gen_forwards_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "gen", "PROJECT=demo-b")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert '--no-print-directory mod PROJECT="demo-b"' in output
        assert '--no-print-directory sync PROJECT="demo-b"' in output

    def test_workspace_makefile_dry_run_sync_respects_project_selection(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_makefile_fixture(tmp_path)
        process = _run_workspace_make_dry_run(workspace_root, "sync", "PROJECT=demo-a")
        output = process.stdout + process.stderr

        assert process.returncode == 0
        assert "workspace sync \\" in output
        assert f'--workspace "{workspace_root}/$proj"' in output
        assert f'--canonical-root "{workspace_root}"' in output
        assert "for proj in demo-a; do" in output
        assert f'init --workspace "{workspace_root}/$proj" --apply' in output
        assert f'workspace sync --workspace "{workspace_root}" --apply' not in output
