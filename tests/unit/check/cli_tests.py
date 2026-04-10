"""Public CLI tests for workspace quality checks."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraWorkspaceChecker
from tests import u


class TestWorkspaceCheckCli:
    """Exercise the public check CLI without patching internal services."""

    @staticmethod
    def _create_workspace(
        tmp_path: Path,
        *,
        project_names: tuple[str, ...] = ("flext-core",),
    ) -> Path:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        for project_name in project_names:
            _ = u.Infra.Tests.mk_project(
                workspace,
                project_name,
                pyproject=(f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n'),
                with_src=True,
            )
        return workspace

    @staticmethod
    def _write_module(workspace: Path, project_name: str, content: str) -> Path:
        module_path = workspace / project_name / "src" / "module.py"
        module_path.write_text(content, encoding="utf-8")
        return module_path

    def test_resolve_gates_maps_type_alias(self) -> None:
        result = FlextInfraWorkspaceChecker.resolve_gates(["lint", "type", "lint"])
        tm.ok(result)
        tm.that(result.value, eq=["lint", "pyrefly"])

    def test_run_cli_returns_zero_for_passing_project(self, tmp_path: Path) -> None:
        workspace = self._create_workspace(tmp_path)
        _ = self._write_module(workspace, "flext-core", "value = 1\n")

        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "run",
                "--workspace",
                str(workspace),
                "--gates",
                "lint",
                "--projects",
                "flext-core",
            ],
        )

        tm.that(exit_code, eq=0)

    def test_run_cli_returns_one_for_failing_project(self, tmp_path: Path) -> None:
        workspace = self._create_workspace(tmp_path)
        _ = self._write_module(workspace, "flext-core", "def broken(:\n")

        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "run",
                "--workspace",
                str(workspace),
                "--gates",
                "lint",
                "--projects",
                "flext-core",
            ],
        )

        tm.that(exit_code, eq=1)

    def test_run_cli_returns_one_for_report_directory_error(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._create_workspace(tmp_path)
        _ = self._write_module(workspace, "flext-core", "value = 1\n")
        blocked = tmp_path / "blocked"
        blocked.write_text("not a directory\n", encoding="utf-8")

        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "run",
                "--workspace",
                str(workspace),
                "--gates",
                "lint",
                "--projects",
                "flext-core",
                "--reports-dir",
                str(blocked / "check"),
            ],
        )

        tm.that(exit_code, eq=1)

    def test_run_cli_handles_multiple_projects(self, tmp_path: Path) -> None:
        workspace = self._create_workspace(
            tmp_path,
            project_names=("proj1", "proj2"),
        )
        _ = self._write_module(workspace, "proj1", "value = 1\n")
        _ = self._write_module(workspace, "proj2", "other = 2\n")

        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "run",
                "--workspace",
                str(workspace),
                "--gates",
                "lint",
                "--projects",
                "proj1",
                "--projects",
                "proj2",
            ],
        )

        tm.that(exit_code, eq=0)

    def test_run_cli_fix_rewrites_source_with_forwarded_ruff_args(
        self,
        tmp_path: Path,
    ) -> None:
        workspace = self._create_workspace(tmp_path)
        module_path = self._write_module(
            workspace,
            "flext-core",
            "import os\n\nvalue = 1\n",
        )

        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "run",
                "--workspace",
                str(workspace),
                "--gates",
                "lint",
                "--fix",
                "--ruff-args",
                "--select F401",
                "--projects",
                "flext-core",
            ],
        )

        tm.that(exit_code, eq=0)
        tm.that("import os" in module_path.read_text(encoding="utf-8"), eq=False)

    def test_run_cli_check_only_preserves_source(self, tmp_path: Path) -> None:
        workspace = self._create_workspace(tmp_path)
        module_path = self._write_module(
            workspace,
            "flext-core",
            "import os\n\nvalue = 1\n",
        )

        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "run",
                "--workspace",
                str(workspace),
                "--gates",
                "lint",
                "--fix",
                "--check-only",
                "--ruff-args",
                "--select F401",
                "--projects",
                "flext-core",
            ],
        )

        tm.that(exit_code, eq=1)
        tm.that(
            module_path.read_text(encoding="utf-8"),
            eq="import os\n\nvalue = 1\n",
        )

    def test_run_cli_rejects_shared_dry_run_flag(self) -> None:
        exit_code = FlextInfraWorkspaceChecker.run_cli(
            [
                "--dry-run",
                "run",
                "--projects",
                "flext-core",
            ],
        )

        tm.that(exit_code, eq=2)
