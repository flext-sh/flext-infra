"""Workspace Makefile generator tests through the public generator API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import cli
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_core import FlextTypes as t


def _write_workspace_root(tmp_path: Path) -> Path:
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    (workspace_root / "pyproject.toml").write_text(
        "[project]\nname='workspace-root'\nversion='0.1.0'\n",
        encoding="utf-8",
    )
    return workspace_root


def _assert_contains_all(text: str, parts: list[str]) -> None:
    for part in parts:
        assert part in text


class TestsFlextInfraWorkspaceMakefileGenerator:
    """Behavior contract for test_makefile_generator."""

    def test_workspace_makefile_generator_sanitizes_orchestrator_env(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                'WORKSPACE_PYTHON := env -u PYTHONPATH -u MYPYPATH PYTHONPATH="$(WORKSPACE_PYTHONPATH)" $(PY)',
                'WORKSPACE_FLEXT_INFRA := FLEXT_WORKSPACE_ROOT="$(CURDIR)" $(WORKSPACE_PYTHON) -m flext_infra',
                "WORKSPACE_INFRA_WORKSPACE := $(WORKSPACE_FLEXT_INFRA) workspace",
                "ORCHESTRATOR := $(WORKSPACE_INFRA_WORKSPACE) orchestrate",
                "ORCHESTRATOR_PROJECTS :=",
                "--projects $(proj)",
            ],
        )

    def test_workspace_makefile_generator_declares_canonical_workspace_variables(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                "PROJECT ?=",
                "PROJECTS ?=",
                "DEPS_REPORT ?= 1",
                "PR_BRANCH ?= 0.1.0",
                "WORKSPACE_INFRA_DEPS := $(WORKSPACE_FLEXT_INFRA) deps",
                "WORKSPACE_INFRA_MAINTENANCE := $(WORKSPACE_FLEXT_INFRA) maintenance run",
                "WORKSPACE_INFRA_RELEASE := $(WORKSPACE_FLEXT_INFRA) release run",
                "WORKSPACE_INFRA_VALIDATE := $(WORKSPACE_FLEXT_INFRA) validate",
                "WORKSPACE_INFRA_GITHUB := $(WORKSPACE_FLEXT_INFRA) github",
            ],
        )

    def test_workspace_makefile_generator_reuses_mod_and_boot_feedback(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        assert makefile_text.count("$(MAKE) _mod") == 1
        _assert_contains_all(
            makefile_text,
            [
                "Run 'make boot'.",
                "Run 'make boot' first to create the environment.",
                "re-run: make boot",
            ],
        )

    def test_workspace_makefile_generator_declares_workspace_boot_separation(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                "FLEXT_PROJECTS :=",
                "WORKSPACE_PROJECTS :=",
                "BOOT_VALIDATE_PROJECTS := $(strip $(filter $(WORKSPACE_PROJECTS),$(SELECTED_PROJECTS)))",
                "tool.flext.workspace or tool.uv.workspace",
                'gitmodules = root / ".gitmodules"',
                '$(MAKE) val WHAT=workspace VALIDATE_SCOPE=workspace PROJECTS="$(BOOT_VALIDATE_PROJECTS)"',
                "Skipping workspace validation (no managed workspace projects selected).",
            ],
        )

    def test_workspace_makefile_generator_does_not_persist_external_project_names(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        assert "sample-external-alpha" not in makefile_text
        assert "sample-external-beta" not in makefile_text

    def test_workspace_makefile_generator_emits_parseable_discovery_commands(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        outcome = cli.run_raw(
            ["make", "-C", str(workspace_root), "--dry-run", "help"],
        )

        assert outcome.success and outcome.value.exit_code == 0

    def test_workspace_makefile_generator_ignores_projects_outside_workspace_scope(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)
        (workspace_root / "pyproject.toml").write_text(
            """
    [project]
    name='workspace-root'
    version='0.1.0'

    [tool.uv.workspace]
    members=['flext-core']
    """.strip()
            + "\n",
            encoding="utf-8",
        )
        docs_dir = workspace_root / "docs"
        docs_dir.mkdir()
        docs_config: dict[str, t.JsonValue] = {
            "scope": {
                "exclude_roots": [
                    "sample-external-alpha",
                    "sample-external-beta",
                ],
            },
        }
        cli.write_json_file(
            docs_dir / "docs_config.json",
            docs_config,
        ).unwrap()
        project_names = ("flext-core", "sample-external-alpha", "sample-external-beta")
        for project_name in project_names:
            project_dir = workspace_root / project_name
            project_dir.mkdir()
            dependencies = "['flext-core']" if project_name != "flext-core" else "[]"
            (project_dir / "pyproject.toml").write_text(
                (
                    "[project]\n"
                    f"name='{project_name}'\n"
                    "version='0.1.0'\n"
                    f"dependencies={dependencies}\n"
                ),
                encoding="utf-8",
            )

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        outcome = cli.run_raw(
            ["make", "-C", str(workspace_root), "-pn"],
        )

        assert outcome.success and outcome.value.exit_code == 0
        stdout = outcome.value.stdout
        assert "sample-external-alpha" not in stdout
        assert "sample-external-beta" not in stdout
        assert "INDEPENDENT_PROJECTS :=" not in stdout
        assert "ATTACHABLE_PROJECTS :=" not in stdout

    def test_workspace_makefile_generator_uses_check_only_for_maintenance_validation(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            ["$(WORKSPACE_INFRA_MAINTENANCE) --check-only || exit 1"],
        )

    def test_workspace_makefile_generator_limits_absolute_path_scan_to_sources(
        self,
        tmp_path: Path,
    ) -> None:
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        assert result.success, result.error
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                "git grep -nE '/home/.*/flext|file:///home/.*/flext' -- '*.py' '**/*.py' '*.toml' '**/*.toml' '*.yml' '**/*.yml' '*.yaml' '**/*.yaml' '*.json' '**/*.json' '.gitignore' 'base.mk' '**/base.mk' ':!.reports/**' ':!**/*.bak' ':!docs/**'",
            ],
        )
