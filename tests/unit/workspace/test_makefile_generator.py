"""Workspace Makefile generator tests through the public generator API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

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
        "[project]\nname='workspace-root'\nversion='0.1.0'\n", encoding="utf-8"
    )
    _write_workspace_manifest(workspace_root)
    return workspace_root


def _write_workspace_manifest(workspace_root: Path, members: str = "") -> None:
    config_dir = workspace_root / "config"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "workspace.yaml").write_text(
        (
            "version: 2\n"
            "name: workspace-root\n"
            "repository:\n"
            "  name: workspace-root\n"
            "  distribution: workspace-root\n"
            "  provider: flext-sh\n"
            "  url: https://github.com/flext-sh/workspace-root.git\n"
            "  branch: main\n"
            "  path: .\n"
            "  role: workspace-root\n"
            "  state: active\n"
            "  profile: workspace-root\n"
            "  checkout: root\n"
            "  codegen: conform\n"
            "  package: false\n"
            "  editable: false\n"
            "  read_only: false\n"
            f"members:{members or ' []'}\n"
            "content_only: []\n"
            "exclusions: []\n"
        ),
        encoding="utf-8",
    )


def _assert_contains_all(text: str, parts: list[str]) -> None:
    for part in parts:
        tm.that(text, has=part)


class TestsFlextInfraWorkspaceMakefileGenerator:
    """Behavior contract for test_makefile_generator."""

    def test_workspace_makefile_generator_sanitizes_orchestrator_env(
        self, tmp_path: Path
    ) -> None:
        """Sanitize inherited type-checker paths before orchestration."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
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
        self, tmp_path: Path
    ) -> None:
        """Declare the canonical workspace command variables."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
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
        self, tmp_path: Path
    ) -> None:
        """Reuse the canonical modernization and boot guidance."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile_text.count("$(MAKE) _mod"), eq=1)
        _assert_contains_all(
            makefile_text,
            [
                "Run 'make boot'.",
                "Run 'make boot' first to create the environment.",
                "re-run: make boot",
            ],
        )

    def test_workspace_makefile_generator_declares_workspace_boot_separation(
        self, tmp_path: Path
    ) -> None:
        """Separate declared Git projects from workspace boot selection."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
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
                "$(MAKE) --no-print-directory _boot_submodules",
                "$(MAKE) --no-print-directory _boot_venv",
                "_boot_venv:",
                "_boot_submodules:",
            ],
        )

    def test_workspace_makefile_generator_does_not_persist_external_project_names(
        self, tmp_path: Path
    ) -> None:
        """Exclude external documentation roots from generated project state."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        tm.that(makefile_text, lacks="sample-external-alpha")
        tm.that(makefile_text, lacks="sample-external-beta")

    def test_workspace_makefile_generator_emits_parseable_discovery_commands(
        self, tmp_path: Path
    ) -> None:
        """Emit discovery commands accepted by GNU Make."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        outcome = cli.run_raw(["make", "-C", str(workspace_root), "--dry-run", "help"])

        output = tm.ok(outcome)
        tm.that(output.exit_code, eq=0)

    def test_workspace_makefile_runs_custom_verb_hooks(self, tmp_path: Path) -> None:
        """A root verb runs workspace_custom.mk pre-<verb> before its dispatch body."""
        workspace_root = _write_workspace_root(tmp_path)
        tm.ok(FlextInfraWorkspaceMakefileGenerator().generate(workspace_root))
        (workspace_root / "workspace_custom.mk").write_text(
            ".PHONY: pre-check post-check\n"
            "pre-check:\n\t@echo WS_HOOK_PRE_CHECK\n"
            "post-check:\n\t@echo WS_HOOK_POST_CHECK\n",
            encoding="utf-8",
        )
        # The dispatch body needs a workspace venv it does not have here, so it
        # stops after the pre-hook. That is enough to prove the pre-hook fires
        # at the start of the verb, ahead of the dispatch body.
        outcome = cli.run_raw(["make", "-C", str(workspace_root), "check", "WHAT=lint"])
        combined = outcome.value.stdout + outcome.value.stderr
        tm.that(combined, has="WS_HOOK_PRE_CHECK")

    def test_workspace_makefile_generator_ignores_projects_outside_workspace_scope(
        self, tmp_path: Path
    ) -> None:
        """Ignore projects excluded from the declared workspace scope."""
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
                "exclude_roots": ["sample-external-alpha", "sample-external-beta"]
            }
        }
        cli.write_json_file(docs_dir / "docs_config.json", docs_config).unwrap()
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

        output = tm.ok(outcome)
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
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
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
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                "define CHECK_SYNC_ALL_PROJECTS",
                'sync --workspace "$(CURDIR)" --dry-run || exit 1',
                "project-local .venv directories violate",
                "override UV_PROJECT_ENVIRONMENT := $(WORKSPACE_VENV)",
                'WORKSPACE_VERIFY_ENVIRONMENT := $(WORKSPACE_INFRA_WORKSPACE) verify-environment --workspace "$(CURDIR)"',
                "$(WORKSPACE_VERIFY_ENVIRONMENT) || exit 1",
                "$(Q)$(CHECK_SYNC_ALL_PROJECTS)",
            ],
        )
        tm.that(makefile_text.count("$(WORKSPACE_VERIFY_ENVIRONMENT)"), eq=2)
        tm.that(makefile_text, lacks="for venv_path in $$local_venvs; do rm -rf")

    def test_workspace_runtime_reinstalls_exact_manifest_editables(
        self, tmp_path: Path
    ) -> None:
        """Render targeted reinstall flags from distributions, not member paths."""
        workspace_root = _write_workspace_root(tmp_path)
        _write_workspace_manifest(
            workspace_root,
            members=(
                "\n"
                "  - name: member-path\n"
                "    distribution: canonical-distribution\n"
                "    provider: flext-sh\n"
                "    url: https://github.com/flext-sh/member-path.git\n"
                "    branch: main\n"
                "    path: member-path\n"
                "    role: workspace-member\n"
                "    state: active\n"
                "    profile: workspace-member\n"
                "    checkout: submodule\n"
                "    codegen: conform\n"
                "    package: true\n"
                "    editable: true\n"
                "    read_only: false"
            ),
        )

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                'WORKSPACE_EDITABLE_REINSTALL_FLAGS := --reinstall-package "canonical-distribution"',
                "uv sync --all-packages --all-groups --all-extras $(WORKSPACE_EDITABLE_REINSTALL_FLAGS)",
            ],
        )
        tm.that(makefile_text.count("$(WORKSPACE_EDITABLE_REINSTALL_FLAGS)"), eq=1)
        tm.that(makefile_text, lacks='--reinstall-package "member-path"')

    def test_workspace_makefile_generator_limits_absolute_path_scan_to_sources(
        self, tmp_path: Path
    ) -> None:
        """Limit absolute-path scans to declared source artifacts."""
        workspace_root = _write_workspace_root(tmp_path)

        result = FlextInfraWorkspaceMakefileGenerator().generate(workspace_root)
        tm.ok(result)
        makefile_text = (workspace_root / "Makefile").read_text(encoding="utf-8")

        _assert_contains_all(
            makefile_text,
            [
                "git grep -nE '/home/.*/flext|file:///home/.*/flext' -- '*.py' '**/*.py' '*.toml' '**/*.toml' '*.yml' '**/*.yml' '*.yaml' '**/*.yaml' '*.json' '**/*.json' '.gitignore' 'base.mk' '**/base.mk' ':!.reports/**' ':!**/*.bak' ':!docs/**'"
            ],
        )
