"""Public ``infra`` facade contract for workspace environment sync and base.mk.

Consumers (ai-hub and other governed hubs) must reach environment-file sync
and base.mk generation exclusively through the public service facade
(``from flext_infra import infra``) — never by importing internal modules.
These tests pin that contract against the canonical codegen SSOT templates.
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, infra, m
from flext_tests import tm


def _write_pyproject(root: Path, *, requires_python: str = ">=3.13") -> None:
    root.mkdir(parents=True, exist_ok=True)
    _ = (root / "pyproject.toml").write_text(
        (
            "[project]\n"
            'name = "workspace"\n'
            'version = "0.1.0"\n'
            f'requires-python = "{requires_python}"\n'
        ),
        encoding="utf-8",
    )


class TestsFlextInfraFacadeEnvironmentSync:
    """Behavior contract for ``infra.sync_environment_files``."""

    def test_sync_creates_environment_files_from_ssot_templates(
        self, tmp_path: Path
    ) -> None:
        """A Python workspace gains canonical .envrc and .mise.toml."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        tm.that(result.value.changed, eq=True)
        envrc = (workspace / ".envrc").read_text(encoding="utf-8")
        mise = (workspace / ".mise.toml").read_text(encoding="utf-8")
        tm.that("strict_env" in envrc, eq=True)
        tm.that('python = "3.13"' in mise, eq=True)

    def test_sync_preserves_custom_envrc_without_force(self, tmp_path: Path) -> None:
        """Custom (non-generated) .envrc content is never clobbered."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        custom = workspace / ".envrc"
        _ = custom.write_text("PATH_add bin\n", encoding="utf-8")

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        tm.that(custom.read_text(encoding="utf-8"), eq="PATH_add bin\n")

    def test_sync_force_converts_custom_envrc_to_generated(
        self, tmp_path: Path
    ) -> None:
        """Force replaces custom .envrc with the canonical generated file."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        custom = workspace / ".envrc"
        _ = custom.write_text("PATH_add bin\n", encoding="utf-8")

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(
                workspace_root=workspace, force=True
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

    def test_sync_merges_custom_mise_tools_and_prunes_forbidden(
        self, tmp_path: Path
    ) -> None:
        """Custom .mise.toml keeps user tools, gains pins, loses linters."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        mise = workspace / ".mise.toml"
        _ = mise.write_text(
            '[tools]\nnode = "22"\npython = "3.12"\nmypy = "1.20.2"\nruff = "0.9.0"\n',
            encoding="utf-8",
        )

        result = infra.sync_environment_files(
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

    def test_sync_removes_generated_files_without_pyproject(
        self, tmp_path: Path
    ) -> None:
        """Non-Python workspaces lose generated environment files."""
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)
        setup = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )
        tm.ok(setup)
        (workspace / "pyproject.toml").unlink()

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        tm.that((workspace / ".envrc").exists(), eq=False)
        tm.that((workspace / ".mise.toml").exists(), eq=False)


class TestsFlextInfraFacadeBaseMk:
    """Behavior contract for ``infra.generate_basemk``."""

    def test_generate_basemk_returns_rendered_content(self) -> None:
        """The facade renders base.mk content for a named project."""
        result = infra.generate_basemk(
            m.Infra.BaseMkRenderRequest(project_name="sample-project")
        )

        tm.ok(result)
        tm.that("sample-project" in result.value.content, eq=True)
        tm.that(".PHONY" in result.value.content, eq=True)
