"""Workspace Makefile generator tests through the public generator API."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_cli import cli
from flext_core import FlextTypes as t
from flext_infra.workspace.workspace_makefile import (
    FlextInfraWorkspaceMakefileGenerator,
)


class TestsFlextInfraWorkspaceMakefileGenerator:
    """Behavior contract for test_makefile_generator."""

    @staticmethod
    def _write_workspace_root(tmp_path: Path) -> Path:
        """Create a committed workspace fixture on the canonical dev branch."""
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        (workspace_root / "pyproject.toml").write_text(
            "[project]\nname='workspace-root'\nversion='0.1.0'\n", encoding="utf-8"
        )
        commands = (
            ("git", "init", "-q", "-b", "0.20.0-dev"),
            ("git", "add", "pyproject.toml"),
            (
                "git",
                "-c",
                "user.name=Flext Tests",
                "-c",
                "user.email=tests@flext.local",
                "commit",
                "-q",
                "-m",
                "Initialize workspace fixture",
            ),
        )
        for command in commands:
            success = cli.run_checked(command, cwd=workspace_root).unwrap()
            tm.that(success, eq=True)
        return workspace_root

    @staticmethod
    def _assert_contains_all(text: str, parts: t.StrSequence) -> None:
        """Assert that generated text contains every required fragment."""
        for part in parts:
            tm.that(text, has=part)

    def test_workspace_makefile_generator_sanitizes_orchestrator_env(
        self, tmp_path: Path
    ) -> None:
        """Sanitize inherited type-checker paths before orchestration."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        self._assert_contains_all(
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
        self, tmp_path: Path
    ) -> None:
        """Declare the canonical workspace command variables."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        self._assert_contains_all(
            makefile_text,
            [
                "PROJECT ?=",
                "PROJECTS ?=",
                "DEPS_REPORT ?= 1",
                "PR_BRANCH ?= 0.20.0-dev",
                "WORKSPACE_INFRA_DEPS := $(WORKSPACE_FLEXT_INFRA) deps",
                "WORKSPACE_INFRA_MAINTENANCE := $(WORKSPACE_FLEXT_INFRA) maintenance run",
                "WORKSPACE_INFRA_RELEASE := $(WORKSPACE_FLEXT_INFRA) release run",
                "WORKSPACE_INFRA_VALIDATE := $(WORKSPACE_FLEXT_INFRA) validate",
                "WORKSPACE_INFRA_GITHUB := $(WORKSPACE_FLEXT_INFRA) github",
            ],
        )

    def test_workspace_makefile_generator_reuses_mod_and_boot_feedback(
        self, tmp_path: Path
    ) -> None:
        """Reuse the canonical modernization and boot guidance."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile_text.count("$(MAKE) _mod"), eq=1)
        self._assert_contains_all(
            makefile_text,
            [
                "Run 'make boot'.",
                "Run 'make boot' first to create the environment.",
                "re-run: make boot",
            ],
        )

    def test_workspace_makefile_generator_separates_boot_from_validation(
        self, tmp_path: Path
    ) -> None:
        """Keep workspace validation explicit instead of running it during boot."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        self._assert_contains_all(
            makefile_text,
            [
                "FLEXT_PROJECTS :=",
                "WORKSPACE_PROJECTS :=",
                "tool.flext.workspace or tool.uv.workspace",
                'gitmodules = root / ".gitmodules"',
                "_val_workspace: ## Run workspace validation gates",
                "$(MAKE) --no-print-directory _val_body VALIDATE_SCOPE=workspace $(MAKE_SELECTION_ARGS)",
                "Running workspace validation (inventory + strict anti-drift gates)...",
            ],
        )

    def test_workspace_makefile_generator_does_not_persist_external_project_names(
        self, tmp_path: Path
    ) -> None:
        """Exclude external documentation roots from generated project state."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile_text, lacks="sample-external-alpha")
        tm.that(makefile_text, lacks="sample-external-beta")

    def test_workspace_makefile_generator_emits_parseable_discovery_commands(
        self, tmp_path: Path
    ) -> None:
        """Emit discovery commands accepted by GNU Make."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        outcome = cli.run_raw(["make", "-C", str(workspace_root), "--dry-run", "help"])

        output = outcome.unwrap()
        tm.that(output.exit_code, eq=0)

    def test_workspace_makefile_generator_ignores_projects_outside_workspace_scope(
        self, tmp_path: Path
    ) -> None:
        """Ignore projects excluded from the declared workspace scope."""
        workspace_root = self._write_workspace_root(tmp_path)
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
                "exclude_roots": ["sample-external-alpha", "sample-external-beta"]
            }
        }
        cli.json_write_file(docs_dir / "docs_config.json", docs_config).unwrap()
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
        tm.ok(result)
        outcome = cli.run_raw(["make", "-C", str(workspace_root), "-pn"])

        output = outcome.unwrap()
        tm.that(output.exit_code, eq=0)
        stdout = output.stdout
        tm.that(stdout, lacks="sample-external-alpha")
        tm.that(stdout, lacks="sample-external-beta")
        tm.that(stdout, lacks="INDEPENDENT_PROJECTS :=")
        tm.that(stdout, lacks="ATTACHABLE_PROJECTS :=")

    def test_workspace_makefile_generator_uses_check_only_for_maintenance_validation(
        self, tmp_path: Path
    ) -> None:
        """Use read-only maintenance validation in generated Makefiles."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        self._assert_contains_all(
            makefile_text, ["$(WORKSPACE_INFRA_MAINTENANCE) --check-only || exit 1"]
        )

    def test_workspace_sync_regenerates_each_test_facade_explicitly(
        self, tmp_path: Path
    ) -> None:
        """Keep generated test facades synchronized without indexing test classes."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile_text.count("--module tests --apply || exit 1"), eq=2)
        _assert_contains_all(
            makefile_text,
            [
                'if [ -d "$(CURDIR)/$$proj/tests" ]; then',
                'init --workspace "$(CURDIR)/$$proj" --module tests --apply',
                "for proj in $(ALL_PROJECTS); do",
            ],
        )

    def test_workspace_validation_is_read_only_and_venv_guard_is_fail_closed(
        self, tmp_path: Path
    ) -> None:
        """Detect generated drift and local environments without mutating either."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        self._assert_contains_all(
            makefile_text,
            [
                "define CHECK_SYNC_ALL_PROJECTS",
                'sync --workspace "$(CURDIR)" --dry-run || exit 1',
                "project-local .venv directories violate",
                "$(Q)$(CHECK_SYNC_ALL_PROJECTS)",
            ],
        )
        tm.that(makefile_text, lacks="for venv_path in $$local_venvs; do rm -rf")

    def test_workspace_makefile_generator_limits_absolute_path_scan_to_sources(
        self, tmp_path: Path
    ) -> None:
        """Limit absolute-path scans to declared source artifacts."""
        workspace_root = self._write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        self._assert_contains_all(
            makefile_text,
            [
                "git grep -nE '/home/.*/flext|file:///home/.*/flext' -- '*.py' '**/*.py' '*.toml' '**/*.toml' '*.yml' '**/*.yml' '*.yaml' '**/*.yaml' '*.json' '**/*.json' '.gitignore' 'base.mk' '**/base.mk' ':!.reports/**' ':!**/*.bak' ':!docs/**'"
            ],
        )
