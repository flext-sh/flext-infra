"""Public ``infra`` facade contract for workspace environment sync.

Consumers must reach environment-file sync through the public service facade
(``from flext_infra import infra``). These tests pin that contract against the
canonical codegen SSOT templates.
"""

from __future__ import annotations

import tomllib
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
        """A Python workspace gains the canonical .envrc this service owns.

        ``.mise.toml`` is projected by ``codegen conform``, not by the workspace
        environment service; its contract is covered at that owner.
        """
        workspace = tmp_path / "workspace"
        _write_pyproject(workspace)

        result = infra.sync_environment_files(
            m.Infra.WorkspaceEnvironmentSyncRequest(workspace_root=workspace)
        )

        tm.ok(result)
        tm.that(result.value.changed, eq=True)
        envrc = (workspace / ".envrc").read_text(encoding="utf-8")
        tm.that("strict_env" in envrc, eq=True)
        tm.that("DIRENV_DIR" in envrc, eq=False)
        tm.that('PROJECT_ROOT="$(find_up pyproject.toml)"' in envrc, eq=True)
        tm.that('PROJECT_ROOT="${PROJECT_ROOT%/*}"' in envrc, eq=True)
        tm.that('PROJECT_SCRATCH="${PROJECT_ROOT}/.test-tmp"' in envrc, eq=True)
        tm.that('export TMPDIR="${PROJECT_SCRATCH}"' in envrc, eq=True)
        tm.that('export GOTMPDIR="${PROJECT_SCRATCH}"' in envrc, eq=True)

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
