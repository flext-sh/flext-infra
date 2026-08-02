"""Canonical developer environment and formatter contracts."""

from __future__ import annotations

from pathlib import Path

from packaging.requirements import Requirement

from flext_infra import FlextInfraWorkspaceEnvironment, config
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm


class TestsCodegenDeveloperEnvironment:
    """Prove conform owns every runtime used by generated Make surfaces."""

    def test_mise_toolchain_contains_every_native_make_runtime(self) -> None:
        """The typed toolchain owns exact versions for all native Make tools."""
        required_backends = {
            "python",
            "uv",
            "go",
            "rust",
            "node",
            "npm:prettier",
            "github:gastownhall/beads",
            "kubectl",
            "helm",
            "kind",
            "taplo",
            "ast-grep",
            "gitleaks",
            "tokei",
        }
        tools = {
            tool.backend: tool.version
            for tool in config.Infra.codegen.toolchain.mise_tools
        }

        tm.that(required_backends.issubset(tools), eq=True)
        for backend, version in tools.items():
            tm.that(version, empty=False, msg=backend)
            tm.that(version, lacks="latest", msg=backend)

    def test_python_make_tools_are_exact_workspace_dependencies(self) -> None:
        """Uv installs every Python Make tool at its config-owned exact version."""
        required_tools = {
            "actionlint-py",
            "mypy",
            "pyrefly",
            "pyright",
            "pytest",
            "ruff",
            "rumdl",
            "vulture",
            "yamlfix",
        }
        requirements = {
            requirement.name: requirement
            for raw in config.Infra.codegen.scaffold.project.dev
            if (requirement := Requirement(raw)).name in required_tools
        }

        tm.that(set(requirements), eq=required_tools)
        for name, requirement in requirements.items():
            specifiers = tuple(requirement.specifier)
            tm.that(specifiers, len=1, msg=name)
            tm.that(specifiers[0].operator, eq="==", msg=name)

    def test_base_make_delegates_format_inventory_to_one_typed_owner(self) -> None:
        """Generated Make never reimplements Git selection or formatter routing."""
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        tm.that(rendered, has="$(PROJECT_INFRA_WORKSPACE) format")
        tm.that(rendered, lacks='git -C "$$md_root" ls-files')
        tm.that(rendered, lacks='xargs -r "$(dir $(VENV_PYTHON))rumdl"')

    def test_generated_make_bootstraps_mise_then_uses_workspace_venv(self) -> None:
        """Setup provisions uv with mise and Python tools from the active venv."""
        bootstrap = tm.ok(FlextInfraBaseMkTemplateRenderer.render_bootstrap_include())
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer().render_all())

        tm.that(bootstrap, has='"$(SETUP_MISE)" install')
        tm.that(bootstrap, has="$(SETUP_MISE) exec -- uv")
        tm.that(rendered, has="ACTIVE_VENV := $(WORKSPACE_ROOT)/.venv")
        tm.that(rendered, has="VENV_BIN := $(ACTIVE_VENV)/bin")
        tm.that(rendered, has="$(VENV_BIN)/pyrefly")
        tm.that(rendered, has="$(VENV_BIN)/vulture")

    def test_standalone_projection_adopts_attached_workspace_venv(self) -> None:
        """The same generated Makefile adopts a live superproject automatically."""
        template = (
            Path(__file__).parents[3]
            / "src/flext_infra/templates/project/base/Makefile.j2"
        ).read_text(encoding="utf-8")

        tm.that(
            template, has="git rev-parse --show-superproject-working-tree 2>/dev/null"
        )
        tm.that(template, has="$(wildcard $(SUPERPROJECT_ROOT)/config/workspace.yaml)")
        tm.that(template, has="RUNTIME_ROOT := $(SUPERPROJECT_ROOT)")
        tm.that(
            template, has='$(SELF_MAKE) -C "$(RUNTIME_ROOT)" _builtin_setup_environment'
        )

    def test_direnv_resolves_the_governing_git_workspace(self, tmp_path: Path) -> None:
        """Activation derives one environment root for roots, members, and worktrees."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "fixture"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        tm.ok(FlextInfraWorkspaceEnvironment.sync_environment_files(tmp_path))
        rendered = (tmp_path / ".envrc").read_text(encoding="utf-8")

        tm.that(rendered, has="git rev-parse --show-superproject-working-tree")
        tm.that(rendered, has='VENV_DIR="${WORKSPACE_ROOT}/.venv"')
        tm.that(rendered, has='PATH_rm "${MISE_SHIMS}"')
        tm.that(rendered, has='eval "$(mise env -s bash)"')
        tm.that(rendered, lacks="mise activate bash --shims")

    def test_environment_sync_is_the_sole_generated_environment_writer(self) -> None:
        """Conform delegates environment files to their one canonical writer."""
        managed = next(
            item
            for item in config.Infra.codegen.managed_files
            if item.path == Path(".envrc")
        )
        template = next(
            item
            for item in config.Infra.codegen.templates.entries
            if item.destination == ".envrc"
        )

        tm.that(managed.owner, eq="environment")
        tm.that(managed.policy, eq="delegated")
        tm.that(template.source, eq="base/envrc.sh.j2")


__all__: list[str] = ["TestsCodegenDeveloperEnvironment"]
