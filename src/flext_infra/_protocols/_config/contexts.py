# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_config/contexts
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_infra._protocols._config import FlextInfraProtocolsConfigContract

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import (
        FlextInfraProtocolsDepsToolConfig,
        FlextInfraProtocolsMiseToolchain,
    )
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigBeads,
        FlextInfraProtocolsConfigMake,
        FlextInfraProtocolsConfigRepository,
        FlextInfraProtocolsConfigScaffold,
    )


class FlextInfraProtocolsConfigContexts:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class MakeCommandContext(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def release_verbs(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Release phase commands elected by repository capability."""
            ...

        @property
        def infra_cli(self) -> t.NonEmptyStr:
            """Installed infrastructure CLI command."""
            ...

        @property
        def examples_module(self) -> t.NonEmptyStr | None:
            """Repository-declared public examples module."""
            ...

        @property
        def workspace_repositories(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.RepositoryRef, ...]:
            """Ordered workspace subproject records."""
            ...

        @property
        def environment_imports(self) -> tuple[tuple[t.NonEmptyStr, Path], ...]:
            """Declared package names and source roots for diagnostics."""
            ...

        @property
        def pytest(self) -> FlextInfraProtocolsDepsToolConfig.PytestConfig:
            """Typed pytest execution policy."""
            ...

        @property
        def environment_directory(self) -> t.NonEmptyStr:
            """Runtime-root-local development environment."""
            ...

        @property
        def contract_env_values(self) -> tuple[t.NonEmptyStr, ...]:
            """OPTIONS or HELP values that display a verb contract."""
            ...

    @runtime_checkable
    class BootstrapRequirementsRenderSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def requirements(self) -> tuple[t.NonEmptyStr, ...]:
            """Quoted source paths in dependency order."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Original declarations consumed here."""
            ...

    @runtime_checkable
    class MakefileProjectRenderSpec(MakeCommandContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def bootstrap_requirements(self) -> Path:
            """Catalog-owned executor requirements under FLEXT."""
            ...

        @property
        def bootstrap_report_shell_literal(self) -> t.NonEmptyStr:
            """Shell-quoted elected operation report scalar transport."""
            ...

        @property
        def bootstrap_report_relative_path(self) -> Path:
            """Repository-relative early bootstrap evidence destination."""
            ...

        @property
        def dist(self) -> t.NonEmptyStr:
            """PEP 621 project name."""
            ...

        @property
        def make_profile(self) -> c.Infra.MakeProfile:
            """Selected repository Make profile."""
            ...

        @property
        def package(self) -> bool:
            """Repository publishes a Python package."""
            ...

        @property
        def analyzer_roots(self) -> t.StrTuple:
            """Structural member projected from the owning model.

            Configured analyzer directories; the Makefile keeps only those present
            in the checkout.
            """
            ...

        @property
        def repository_root_rel(self) -> t.NonEmptyStr:
            """Relative workspace root path."""
            ...

        @property
        def workspace_subprojects(self) -> tuple[str, ...]:
            """Declared workspace subproject paths."""
            ...

    @runtime_checkable
    class MakefileToolchainRenderSpec(MakefileProjectRenderSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def uv_link_mode(self) -> t.NonEmptyStr:
            """Configured uv installation link mode."""
            ...

        @property
        def toolchain(self) -> FlextInfraProtocolsMiseToolchain.ToolchainSpec:
            """Canonical toolchain consumed by native bootstrap."""
            ...

        @property
        def mise_selector(self) -> t.NonEmptyStr:
            """Mise backend selector the mise.lock pin is read from."""
            ...

        @property
        def mise_version(self) -> t.NonEmptyStr:
            """Declared mise release the running binary must match."""
            ...

        @property
        def mise_install_tools(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Explicit [tools] keys `mise install` provisions in setup and upg, so the
            operator's global Mise registry is never installed by a project verb.
            """
            ...

        @property
        def mise_lock_filename(self) -> t.NonEmptyStr:
            """Committed Mise lock of every governed repository."""
            ...

        @property
        def mise_config_filename(self) -> t.NonEmptyStr:
            """Structural member projected from the owning model.

            Only project Mise config the locked bootstrap loads; a machine-local
            override never enters a locked install.
            """
            ...

        @property
        def uv_lock_filename(self) -> t.NonEmptyStr:
            """Committed native uv lock of the runtime root."""
            ...

        @property
        def executor_installs_project(self) -> bool:
            """Structural member projected from the owning model.

            The project belongs to the infrastructure distribution's runtime
            closure, so the upgrade executor installs the project's locked non-
            editable build instead of excluding it.
            """
            ...

        @property
        def python_version(self) -> t.NonEmptyStr:
            """Python minor line the environment syncs against."""
            ...

    @runtime_checkable
    class MakefileRenderSpec(MakefileToolchainRenderSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def make(self) -> FlextInfraProtocolsConfigMake.MakeSpec:
            """Generated Make command contract."""
            ...

        @property
        def extra_verbs(self) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Repository-specific public Make verbs."""
            ...

        @property
        def script_dispatch(
            self,
        ) -> FlextInfraProtocolsConfigRepository.ScriptDispatchSpec | None:
            """Optional script command dispatch contract."""
            ...

        @property
        def verb_groups(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbGroupSpec, ...]:
            """Ordered `make help` sections; empty is flat."""
            ...

        @property
        def makefile_custom_include(self) -> t.NonEmptyStr:
            """Generated custom Make policy include directive."""
            ...

        @property
        def workspace_cli_group(self) -> t.NonEmptyStr:
            """CLI group that owns the workspace propagate route."""
            ...

        @property
        def mypy_timeout_exit_code(self) -> int:
            """Wall-time limiter timeout exit code."""
            ...

        @property
        def timeout_command(self) -> t.NonEmptyStr:
            """Wall-time limiter executable."""
            ...

        @property
        def timeout_kill_after_seconds(self) -> int:
            """Forced-termination grace period."""
            ...

    @runtime_checkable
    class MakeRenderContext(MakeCommandContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def owns_workspace_manifest(self) -> bool:
            """Whether this repository owns the workspace manifest."""
            ...

        @property
        def make(self) -> FlextInfraProtocolsConfigMake.MakeSpec:
            """Generated Make command contract."""
            ...

        @property
        def mypy_timeout_exit_code(self) -> int:
            """Wall-time limiter timeout exit code."""
            ...

        @property
        def timeout_command(self) -> t.NonEmptyStr:
            """Wall-time limiter executable."""
            ...

        @property
        def timeout_kill_after_seconds(self) -> int:
            """Forced-termination grace period."""
            ...

        @property
        def tooling_runtime(
            self,
        ) -> FlextInfraProtocolsDepsToolConfig.ToolingRuntimeContext:
            """Resolved project/workspace tooling values."""
            ...

        @property
        def dist(self) -> t.NonEmptyStr:
            """Distribution name."""
            ...

        @property
        def python_version(self) -> t.NonEmptyStr:
            """Python major.minor tool value."""
            ...

        @property
        def uv_link_mode(self) -> t.NonEmptyStr:
            """Configured uv installation link mode."""
            ...

        @property
        def make_profile(self) -> c.Infra.MakeProfile:
            """Generated Make execution profile."""
            ...

        @property
        def ruff_delegated_rules(self) -> t.StrTuple:
            """Native rules checked by elected canonical owners."""
            ...

        @property
        def repository_root_rel(self) -> t.NonEmptyStr:
            """Relative path to the declared workspace root."""
            ...

        @property
        def makefile_custom_include(self) -> str:
            """Make directive that includes the custom Make surface."""
            ...

        @property
        def workspace_subprojects(self) -> tuple[str, ...]:
            """Ordered workspace subproject paths."""
            ...

        @property
        def extra_verbs(self) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Repository-specific additional public Make verbs."""
            ...

        @property
        def script_dispatch(
            self,
        ) -> FlextInfraProtocolsConfigRepository.ScriptDispatchSpec | None:
            """Opt-in script command-framework routing contract."""
            ...

        @property
        def workspace_cli_group(self) -> str:
            """CLI group name for the flext-infra workspace propagate route."""
            ...

    @runtime_checkable
    class ProjectRenderRuntimeContext(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def dist(self) -> t.NonEmptyStr:
            """Project distribution identity."""
            ...

        @property
        def make_profile(self) -> c.Infra.MakeProfile:
            """Selected repository Make profile."""
            ...

        @property
        def uv_link_mode(self) -> t.NonEmptyStr:
            """Declared UV link mode."""
            ...

        @property
        def tooling_runtime(
            self,
        ) -> FlextInfraProtocolsDepsToolConfig.ToolingRuntimeContext:
            """Resolved tooling document required by project metadata."""
            ...

        @property
        def hatch_build_hook_path(self) -> Path | None:
            """Project-relative Hatch custom build hook module."""
            ...

        @property
        def uv_cache_key_files(self) -> Sequence[str]:
            """Derived uv editable-build cache-key files."""
            ...

        @property
        def docs_audit(
            self,
        ) -> FlextInfraProtocolsConfigContract.DocsAuditOverridesSpec:
            """Repository-owned documentation audit declarations."""
            ...

        @property
        def namespace_scan_dirs(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Production source roots rendered as the namespace validator's declared
            scan scope; empty keeps every root in scope.
            """
            ...

        @property
        def workspace_integration(
            self,
        ) -> FlextInfraProtocolsConfigRepository.WorkspaceIntegrationSpec | None:
            """Structural member projected from the owning model.

            Declared integration provider and branch written into the workspace
            manifest so later renders derive from the declaration, never from the
            checkout.
            """
            ...

    @runtime_checkable
    class ProjectRenderDependencyContext(ProjectRenderRuntimeContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def scaffold(self) -> FlextInfraProtocolsConfigScaffold.ScaffoldSpec:
            """New-project scaffold policy."""
            ...

        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraProtocolsConfigScaffold.ScaffoldGitignoreSectionSpec, ...]:
            """Canonical .gitignore sections derived from the artifact SSOT."""
            ...

        @property
        def project_dependencies(self) -> tuple[t.NonEmptyStr, ...]:
            """Target-owned runtime requirements."""
            ...

        @property
        def development_dependencies(self) -> tuple[t.NonEmptyStr, ...]:
            """Development policy composed for the target's kind."""
            ...

        @property
        def tooling(self) -> FlextInfraProtocolsDepsToolConfig.ToolConfigDocument:
            """Canonical validated tooling policy."""
            ...

        @property
        def environment_path_prepends(self) -> tuple[t.NonEmptyStr, ...]:
            """Configured read-only PATH additions for direnv."""
            ...

        @property
        def beads(self) -> FlextInfraProtocolsConfigBeads.BeadsProjectSpec | None:
            """Repository-local Beads identity when enabled."""
            ...

        @property
        def ownership_command_prefix(self) -> tuple[t.NonEmptyStr, ...]:
            """Configured Beads ownership command."""
            ...

    @runtime_checkable
    class ProjectRenderPackageContext(ProjectRenderDependencyContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def canonical_project_name(self) -> t.NonEmptyStr:
            """Canonical PEP 621 project name."""
            ...

        @property
        def const_name(self) -> t.NonEmptyStr:
            """Configured constant project name."""
            ...

        @property
        def package(self) -> bool:
            """Repository publishes a Python package."""
            ...

        @property
        def package_name(self) -> t.NonEmptyStr | None:
            """Python import package name; absent without a package."""
            ...

        @property
        def packaged_data_paths(self) -> Sequence[str]:
            """Validated relative data paths shipped in distributions."""
            ...

        @property
        def project_declaration_resource(
            self,
        ) -> tuple[t.NonEmptyStr, t.NonEmptyStr] | None:
            """Producer declaration source and wheel extra-metadata destination."""
            ...

        @property
        def packaged_data_excludes(self) -> Sequence[str]:
            """Validated files excluded from packaged data roots."""
            ...

        @property
        def class_stem(self) -> t.NonEmptyStr:
            """Public facade class stem."""
            ...

        @property
        def ns(self) -> t.NonEmptyStr:
            """Public model namespace."""
            ...

        @property
        def ns_attr(self) -> t.NonEmptyStr:
            """Private namespace module token."""
            ...

        @property
        def alias(self) -> t.NonEmptyStr:
            """Public instance alias."""
            ...

        @property
        def env_prefix(self) -> t.NonEmptyStr:
            """Settings environment prefix."""
            ...

        @property
        def upstream(self) -> t.NonEmptyStr:
            """Upstream FLEXT facade module."""
            ...

        @property
        def inherited_facets(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Upstream facets re-exported by the project root; see the RepositoryRef
            namesake for the lazy-init contract.
            """
            ...

        @property
        def root_packages(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Additional shipped top-level packages; see the ProjectSpec namesake for
            the declaration contract.
            """
            ...

        @property
        def repository_namespace_packages(self) -> tuple[t.NonEmptyStr, ...]:
            """Implicit namespace directories shipped from the repository root."""
            ...

        @property
        def root_modules(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Additional shipped top-level modules; see the ProjectSpec namesake for
            the declaration contract.
            """
            ...

        @property
        def cli_module(self) -> bool:
            """Structural member projected from the owning model.

            Whether the package ships its cli entry module; see the ProjectSpec
            namesake.
            """
            ...

        @property
        def console_scripts(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.ConsoleScriptSpec, ...]:
            """Additional console scripts; see the ProjectSpec namesake."""
            ...

        @property
        def runtime_dependency_overlay(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Repository-declared runtime requirements rendered ahead of the
            dependency profile's runtime set; see the ProjectSpec namesake.
            """
            ...

    @runtime_checkable
    class ProjectRenderContext(ProjectRenderPackageContext, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_env_prefix(self) -> str:
            """Settings environment prefix derived from the distribution name."""
            ...

        @property
        def config_base_class(self) -> str | None:
            """Config base class composed by the generated ``_config.py``."""
            ...

        @property
        def config_base_module(self) -> str | None:
            """Import module exposing ``config_base_class``."""
            ...

        @property
        def settings_base_class(self) -> str | None:
            """Settings base class composed by the generated ``_settings.py``."""
            ...

        @property
        def description(self) -> t.NonEmptyStr:
            """Project description."""
            ...

        @property
        def documentation_language(self) -> t.Infra.DocumentationLanguage:
            """Project-local generated documentation language."""
            ...

        @property
        def version(self) -> t.NonEmptyStr:
            """Project version."""
            ...

        @property
        def license(self) -> t.NonEmptyStr:
            """SPDX license id."""
            ...

        @property
        def python_required_version(self) -> t.NonEmptyStr:
            """PEP 440 project Python requirement."""
            ...

        @property
        def dependency_cooldown_days(self) -> int:
            """Supply-chain cooldown rendered as mise release age."""
            ...

        @property
        def author_name(self) -> t.NonEmptyStr:
            """Author display name."""
            ...

        @property
        def author_email(self) -> t.NonEmptyStr:
            """Author email."""
            ...

        @property
        def repository(self) -> t.NonEmptyStr:
            """Project repository page URL."""
            ...

        @property
        def homepage(self) -> t.NonEmptyStr:
            """Project homepage."""
            ...

        @property
        def documentation(self) -> t.NonEmptyStr:
            """Project documentation URL."""
            ...

        @property
        def flext_git_base_url(self) -> t.NonEmptyStr:
            """FLEXT Git provider base URL."""
            ...

        @property
        def flext_git_branch(self) -> t.NonEmptyStr:
            """FLEXT Git provider branch."""
            ...

        @property
        def repository_provider(self) -> t.NonEmptyStr:
            """Provider key the repository declares for itself."""
            ...

        @property
        def repository_git_url(self) -> t.NonEmptyStr:
            """Canonical repository Git clone URL."""
            ...

        @property
        def repository_branch(self) -> t.NonEmptyStr:
            """Canonical repository Git branch."""
            ...

        @property
        def year(self) -> int:
            """Copyright year."""
            ...

    @runtime_checkable
    class ProfileSpec(FlextInfraProtocolsConfigContract.ConfigContract, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> c.Infra.MakeProfile:
            """Closed Make profile name."""
            ...

        @property
        def environment_scope(self) -> t.NonEmptyStr:
            """Uv environment ownership."""
            ...

        @property
        def setup_scope(self) -> t.NonEmptyStr:
            """Setup orchestration scope."""
            ...

        @property
        def execution_scope(self) -> t.NonEmptyStr:
            """check/test runtime scope."""
            ...

        @property
        def discovery_scope(self) -> Literal["gitmodules", "none"]:
            """repository-local discovery authority."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsConfigContexts",
]
