"""Workspace sync environment file tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c
from flext_infra.workspace.environment import FlextInfraWorkspaceEnvironment

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p


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

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        assert (project_root / ".envrc").is_file()
        assert (project_root / ".mise.toml").is_file()

    def test_sync_preserves_custom_environment_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")
        custom_envrc = "PATH_add bin\n"
        custom_envrc_path = project_root / ".envrc"
        custom_envrc_path.write_text(custom_envrc, encoding="utf-8")

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        tm.that(custom_envrc_path.read_text(encoding="utf-8"), eq=custom_envrc)
        assert (project_root / ".mise.toml").is_file()

    def test_sync_updates_previously_generated_environment_file(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")
        envrc_path = project_root / ".envrc"
        envrc_path.write_text(
            f"{c.Infra.WORKSPACE_ENV_GENERATED_MARKER}\nold\n", encoding="utf-8"
        )

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        envrc_text = envrc_path.read_text(encoding="utf-8")
        tm.that(envrc_text, lacks="old")
        tm.that(envrc_text, has="VENV_DIR")

    def test_generated_envrc_uses_bare_python(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        envrc_text = (project_root / ".envrc").read_text(encoding="utf-8")
        tm.that(envrc_text, has='PYTHON_VERSION="$(python -c')
        tm.that(envrc_text, lacks='"${VENV_DIR}/bin/python"')

    def test_generated_mise_toml_is_registry_safe(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        mise_text = (project_root / ".mise.toml").read_text(encoding="utf-8")
        tm.that(mise_text, has='python = "3.13"')
        tm.that(mise_text, has='uv = "0.11.29"')
        tm.that(mise_text, has='ruff = "0.15.22"')
        tm.that(mise_text, lacks="mypy =")
        tm.that(mise_text, lacks="pyright =")
        tm.that(mise_text, lacks="pyrefly =")

    def test_sync_merges_custom_mise_toml_and_removes_obsolete_tools(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")
        mise_path = project_root / ".mise.toml"
        mise_path.write_text(
            (
                "[tools]\n"
                'node = "22"\n'
                'python = "3.12"\n'
                'mypy = "1.20.2"\n'
                'pyright = "1.1.410"\n'
                'pyrefly = "1.0.0"\n'
            ),
            encoding="utf-8",
        )

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        mise_text = mise_path.read_text(encoding="utf-8")
        tm.that(mise_text, has='node = "22"')
        tm.that(mise_text, has='python = "3.13"')
        tm.that(mise_text, has='uv = "0.11.29"')
        tm.that(mise_text, has='ruff = "0.15.22"')
        tm.that(mise_text, lacks="mypy =")
        tm.that(mise_text, lacks="pyright =")
        tm.that(mise_text, lacks="pyrefly =")

    def test_sync_replaces_ai_hub_generated_environment_file(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "project"
        self._write_project(project_root, "demo-project")
        envrc_path = project_root / ".envrc"
        envrc_path.write_text(
            "# @generated by ai-hub workspace tooling\nold\n", encoding="utf-8"
        )

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        envrc_text = envrc_path.read_text(encoding="utf-8")
        tm.that(envrc_text, has=c.Infra.WORKSPACE_ENV_GENERATED_MARKER)
        tm.that(envrc_text, lacks="old")

    def test_environment_sync_skips_workspace_without_pyproject(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        tm.that(result.value, eq=0)
        assert not (project_root / ".envrc").exists()
        assert not (project_root / ".mise.toml").exists()

    def test_environment_sync_removes_generated_files_without_pyproject(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".envrc").write_text(
            f"{c.Infra.WORKSPACE_ENV_GENERATED_MARKER}\nold\n", encoding="utf-8"
        )
        (project_root / ".mise.toml").write_text(
            f"{c.Infra.WORKSPACE_ENV_GENERATED_MARKER}\n[tools]\n", encoding="utf-8"
        )

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        tm.that(result.value, eq=2)
        assert not (project_root / ".envrc").exists()
        assert not (project_root / ".mise.toml").exists()

    def test_environment_sync_preserves_custom_env_without_pyproject(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        envrc_path = project_root / ".envrc"
        envrc_path.write_text("PATH_add bin\n", encoding="utf-8")

        result = FlextInfraWorkspaceEnvironment.sync_environment_files(project_root)

        tm.ok(result)
        tm.that(result.value, eq=0)
        tm.that(envrc_path.read_text(encoding="utf-8"), eq="PATH_add bin\n")
        assert not (project_root / ".mise.toml").exists()
