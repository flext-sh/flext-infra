"""Public ``infra`` facade contract for workspace environment sync."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, infra, m
from flext_tests import tm


def _write_pyproject(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _ = (root / "pyproject.toml").write_text(
        '[project]\nname = "workspace"\nversion = "0.1.0"\nrequires-python = ">=3.13"\n',
        encoding="utf-8",
    )


class TestsFlextInfraFacadeEnvironmentSync:
    """Pin direnv ownership without competing with codegen's Mise owner."""

    def test_sync_creates_envrc_without_creating_mise(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=workspace)
        )
        tm.ok(result)
        envrc = (workspace / ".envrc").read_text(encoding="utf-8")
        tm.that("strict_env" in envrc, eq=True)
        tm.that('PROJECT_ROOT="$(find_up pyproject.toml)"' in envrc, eq=True)
        tm.that((workspace / ".mise.toml").exists(), eq=False)

    def test_sync_preserves_custom_envrc_without_force(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        custom = workspace / ".envrc"
        _ = custom.write_text("PATH_add bin\n", encoding="utf-8")
        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=workspace)
        )
        tm.ok(result)
        tm.that(custom.read_text(encoding="utf-8"), eq="PATH_add bin\n")

    def test_sync_force_converts_custom_envrc_to_generated(
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        custom = workspace / ".envrc"
        _ = custom.write_text("PATH_add bin\n", encoding="utf-8")
        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(
                repository_root=workspace, force=True
            )
        )
        tm.ok(result)
        content = custom.read_text(encoding="utf-8")
        tm.that("strict_env" in content, eq=True)
        tm.that("PATH_add bin" in content, eq=False)
        tm.that(
            any(
                marker in content for marker in c.Infra.WORKSPACE_ENV_GENERATED_MARKERS
            ),
            eq=True,
        )

    def test_sync_never_mutates_codegen_owned_mise(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        mise = workspace / ".mise.toml"
        custom = '[tools]\nnode = "22"\npython = "3.14"\n'
        _ = mise.write_text(custom, encoding="utf-8")
        result = infra.sync_environment_files(
<<<<<<< Updated upstream
            m.Infra.WorkspaceEnvironmentSyncRequest(
                repository_root=workspace, force=True
=======
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        merged = mise.read_text(encoding="utf-8")
        tm.that('node = "22"' in merged, eq=True)
        tm.that('python = "3.13"' in merged, eq=True)
        tm.that("mypy" in merged, eq=False)
        tm.that("ruff" in merged, eq=False)

    def test_sync_renders_mise_python_from_pyproject(self, tmp_path: Path) -> None:
        """The workspace requires-python floor overrides the SSOT python pin."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace, requires_python=">=3.14")

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        rendered = (workspace / ".mise.toml").read_text(encoding="utf-8")
        tm.that('python = "3.14"' in rendered, eq=True)

    def test_sync_composes_project_mise_tools_from_yaml(self, tmp_path: Path) -> None:
        """A project extends the generated tool table from its own YAML."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        config_dir = workspace / "config"
        config_dir.mkdir()
        (config_dir / "tooling.yaml").write_text(
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            '      node: "26"\n'
            '      docker-compose: "5.5"\n',
            encoding="utf-8",
        )

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        tools = tomllib.loads((workspace / ".mise.toml").read_text(encoding="utf-8"))[
            "tools"
        ]
        tm.that(tools["node"], eq="26")
        tm.that(tools["docker-compose"], eq="5.5")

    def test_sync_ignores_non_owner_yaml_managed_artifact_blocks(
        self, tmp_path: Path
    ) -> None:
        """Only config/tooling.yaml owns ManagedArtifacts."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        config_dir = workspace / "config"
        config_dir.mkdir()
        for filename, version in (("one.yaml", "20"), ("two.yaml", "22")):
            (config_dir / filename).write_text(
                f'ManagedArtifacts:\n  Mise:\n    tools:\n      node: "{version}"\n',
                encoding="utf-8",
>>>>>>> Stashed changes
            )
        )
        tm.ok(result)
        tm.that(mise.read_text(encoding="utf-8"), eq=custom)

<<<<<<< Updated upstream
    def test_sync_removes_generated_envrc_without_pyproject(
=======
        tm.ok(result)
        tools = tomllib.loads((workspace / ".mise.toml").read_text(encoding="utf-8"))[
            "tools"
        ]
        tm.that("node" in tools, eq=False)

    def test_sync_rejects_project_collision_with_fleet_mise_tool(
>>>>>>> Stashed changes
        self, tmp_path: Path
    ) -> None:
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        setup = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=workspace)
        )
        tm.ok(setup)
        (workspace / "pyproject.toml").unlink()
        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=workspace)
        )
        tm.ok(result)
        tm.that((workspace / ".envrc").exists(), eq=False)
