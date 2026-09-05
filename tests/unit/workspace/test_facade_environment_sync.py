"""Public ``infra`` facade contract for workspace environment sync."""

from __future__ import annotations

import tomllib
from pathlib import Path

from flext_infra import c, infra, m, u
from flext_tests import tm


def _write_pyproject(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    _ = (root / "pyproject.toml").write_text(
        '[project]\nname = "workspace"\nversion = "0.1.0"\nrequires-python = ">=3.13"\n',
        encoding="utf-8",
    )


class TestsFlextInfraFacadeEnvironmentSync:
    """Pin direnv ownership without competing with codegen's Mise owner."""

    def test_sync_creates_environment_files_from_ssot_templates(
        self, tmp_path: Path
    ) -> None:
        """A Python workspace gains the canonical .envrc, and only that.

        ``codegen conform`` exclusively owns ``.mise.toml`` so environment sync
        cannot race toolchain publication, which is why sync writes no Mise
        file here.
        """
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(repository_root=workspace)
        )
        tm.ok(result)
        envrc = (workspace / ".envrc").read_text(encoding="utf-8")
        tm.that((workspace / ".mise.toml").exists(), eq=False)
        tm.that("strict_env" in envrc, eq=True)
        tm.that('PROJECT_ROOT="$(find_up pyproject.toml)"' in envrc, eq=True)
        tm.that('PROJECT_ROOT="${PROJECT_ROOT%/*}"' in envrc, eq=True)
        tm.that('PROJECT_SCRATCH="${PROJECT_ROOT}/.test-tmp"' in envrc, eq=True)
        tm.that('export TMPDIR="${PROJECT_SCRATCH}"' in envrc, eq=True)
        tm.that('export GOTMPDIR="${PROJECT_SCRATCH}"' in envrc, eq=True)

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
            m.Infra.WorkspaceEnvironmentSyncRequest(
                repository_root=workspace, force=True
            )
        )
        tm.ok(result)
        tm.that(mise.read_text(encoding="utf-8"), eq=custom)

    def test_sync_removes_generated_files_without_pyproject(
        self, tmp_path: Path
    ) -> None:
        """Non-Python workspaces lose generated environment files."""
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

        # `.mise.toml` is owned by `codegen conform` (see the composition
        # contract below); environment sync removes only the files it writes.
        tm.ok(result)
        tm.that(result.value.changed_files, eq=(workspace / ".envrc",))
        tm.that((workspace / ".envrc").exists(), eq=False)


class TestsFlextInfraProjectMiseComposition:
    """``.mise.toml`` composition contract, owned by ``codegen conform``.

    Environment sync stopped writing ``.mise.toml`` when the toolchain
    transaction made ``codegen conform`` its exclusive owner, so the project
    overlay contract is proven against the composition owner that survives.
    """

    def test_project_yaml_extends_the_generated_tool_table(
        self, tmp_path: Path
    ) -> None:
        """A project extends the generated tool table from its own YAML."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        config_dir = workspace / "config"
        config_dir.mkdir()
        (config_dir / "tooling.yaml").write_text(
            "ManagedArtifacts:\n"
            "  Mise:\n"
            "    tools:\n"
            "      node:\n"
            '        version: "26"\n'
            "      docker-compose:\n"
            '        version: "5.5"\n',
            encoding="utf-8",
        )

        composed = u.Infra.compose_mise_toml(workspace, '[tools]\npython = "3.13"\n')

        tools = tomllib.loads(tm.ok(composed))["tools"]
        tm.that(tools["node"], eq="26")
        tm.that(tools["docker-compose"], eq="5.5")
        tm.that(tools["python"], eq="3.13")

    def test_duplicate_project_selectors_are_rejected(self, tmp_path: Path) -> None:
        """Two YAML owners cannot silently select the same local tool."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        config_dir = workspace / "config"
        config_dir.mkdir()
        for filename, version in (("one.yaml", "20"), ("two.yaml", "22")):
            (config_dir / filename).write_text(
                "ManagedArtifacts:\n  Mise:\n    tools:\n      node:\n"
                f'        version: "{version}"\n',
                encoding="utf-8",
            )

        composed = u.Infra.compose_mise_toml(workspace, "[tools]\n")

        tm.that(composed.failure, eq=True)
        tm.that(composed.error or "", has=["node", "one.yaml", "two.yaml"])

    def test_project_collision_with_a_fleet_tool_is_rejected(
        self, tmp_path: Path
    ) -> None:
        """A project tool may extend the fleet table but never override it."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        config_dir = workspace / "config"
        config_dir.mkdir()
        (config_dir / "tooling.yaml").write_text(
            "ManagedArtifacts:\n  Mise:\n    tools:\n      python:\n"
            '        version: "3.14"\n',
            encoding="utf-8",
        )

        composed = u.Infra.compose_mise_toml(workspace, '[tools]\npython = "3.13"\n')

        tm.that(composed.failure, eq=True)
        tm.that(
            composed.error or "",
            has=["python", "global .mise.toml template", "tooling.yaml"],
        )
