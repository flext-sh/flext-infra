"""Workspace sync environment file tests."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c
from flext_infra.workspace.sync import FlextInfraSyncService
from tests.protocols import p


class TestsFlextInfraWorkspaceSyncEnvironment:
    """Behavior contract for generated workspace environment files."""

    @staticmethod
    def _write_project(project_root: Path, name: str) -> None:
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "pyproject.toml").write_text(
            (
                "[project]\n"
                f'name = "{name}"\n'
                'version = "0.1.0"\n'
                'description = "Demo project"\n'
                'requires-python = ">=3.13"\n'
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _error_text[ValueT](result: p.Result[ValueT]) -> str:
        return result.error or ""

    def test_sync_writes_environment_files(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace=project_root,
        ).execute()

        assert result.success, self._error_text(result)
        assert ".direnv/" in (project_root / ".gitignore").read_text(encoding="utf-8")
        assert (project_root / ".envrc").is_file()
        assert (project_root / ".mise.toml").is_file()

    def test_sync_preserves_custom_environment_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")
        custom_envrc = "PATH_add bin\n"
        custom_envrc_path = project_root / ".envrc"
        custom_envrc_path.write_text(custom_envrc, encoding="utf-8")

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace=project_root,
        ).execute()

        assert result.success, self._error_text(result)
        assert custom_envrc_path.read_text(encoding="utf-8") == custom_envrc
        assert (project_root / ".mise.toml").is_file()

    def test_sync_updates_previously_generated_environment_file(
        self,
        tmp_path: Path,
    ) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")
        envrc_path = project_root / ".envrc"
        envrc_path.write_text(
            f"{c.Infra.WORKSPACE_ENV_GENERATED_MARKER}\nold\n",
            encoding="utf-8",
        )

        result = FlextInfraSyncService(
            canonical_root=project_root.parent,
            workspace=project_root,
        ).execute()

        assert result.success, self._error_text(result)
        envrc_text = envrc_path.read_text(encoding="utf-8")
        assert "old" not in envrc_text
        assert "VENV_DIR" in envrc_text
