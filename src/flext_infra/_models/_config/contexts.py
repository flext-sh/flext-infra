"""Render context and repository reference models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal, Self

from flext_cli import m

from flext_infra import c, p, t
from flext_infra._models import FlextInfraModelsDepsToolConfig
from flext_infra._models._config import (
    FlextInfraModelsConfigBeads,
    FlextInfraModelsConfigContract,
    FlextInfraModelsConfigMake,
    FlextInfraModelsConfigRepository,
    FlextInfraModelsConfigScaffold,
)


class FlextInfraModelsConfigContexts(FlextInfraModelsConfigRepository):
    """Render context models composed over the repository reference models."""

    class MakeCommandContext(FlextInfraModelsConfigContract.ConfigContract):
        """Shared command identity required by every generated Make surface."""

        release_verbs: Annotated[
            tuple[
                FlextInfraModelsConfigMake.MakeVerbSpec,
                ...,
            ],
            m.Field(
                description="Release phase commands elected by repository capability"
            ),
        ] = ()

        infra_cli: Annotated[
            t.NonEmptyStr,
            m.Field(description="Installed infrastructure CLI command"),
        ]
        examples_module: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Repository-declared public examples module"),
        ] = None
        workspace_repositories: Annotated[
            tuple[
                FlextInfraModelsConfigRepository.RepositoryRef,
                ...,
            ],
            m.Field(description="Ordered workspace subproject records"),
        ] = ()
        environment_imports: Annotated[
            tuple[tuple[t.NonEmptyStr, Path], ...],
            m.Field(
                description="Declared package names and source roots for diagnostics"
            ),
        ]
        pytest: Annotated[
            FlextInfraModelsDepsToolConfig.PytestConfig,
            m.Field(description="Typed pytest execution policy"),
        ]
        environment_directory: Annotated[
            t.NonEmptyStr,
            m.Field(description="Runtime-root-local development environment"),
        ] = c.Infra.ENVIRONMENT_DIRECTORY
        contract_env_values: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="OPTIONS or HELP values that display a verb contract"),
        ] = tuple(sorted(c.Infra.PROMOTED_ENV_ENABLED_VALUES))

    class BootstrapRequirementsRenderSpec(
        FlextInfraModelsConfigContract.ConfigContract
    ):
        """Native editable requirements derived from the executor's local closure."""

        requirements: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1, description="Quoted source paths in dependency order"
            ),
        ]
        inputs: Annotated[
            tuple[t.Port[p.Cli.AtomicFileState], ...],
            m.Field(exclude=True, description="Original declarations consumed here"),
        ]

    class MakefileProjectRenderSpec(MakeCommandContext):
        """Bootstrap evidence and repository topology rendered into the Makefile."""

        bootstrap_requirements: Annotated[
            Path,
            m.Field(description="Catalog-owned executor requirements under FLEXT"),
        ]
        bootstrap_report_shell_literal: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Shell-quoted elected operation report scalar transport"
            ),
        ]
        bootstrap_report_relative_path: Annotated[
            Path,
            m.Field(
                description="Repository-relative early bootstrap evidence destination"
            ),
        ]
        dist: Annotated[t.NonEmptyStr, m.Field(description="PEP 621 project name")]
        make_profile: Annotated[
            c.Infra.MakeProfile,
            m.Field(description="Selected repository Make profile"),
        ]
        package: Annotated[
            bool,
            m.Field(description="Repository publishes a Python package"),
        ]
        analyzer_roots: Annotated[
            t.StrTuple,
            m.Field(
                description=(
                    "Configured analyzer directories; the Makefile keeps "
                    "only those present in the checkout"
                ),
            ),
        ]
        repository_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Relative workspace root path"),
        ]
        workspace_subprojects: Annotated[
            tuple[str, ...],
            m.Field(description="Declared workspace subproject paths"),
        ] = ()

    class MakefileToolchainRenderSpec(MakefileProjectRenderSpec):
        """Toolchain, lock and environment declarations rendered into the Makefile."""

        uv_link_mode: Annotated[
            t.NonEmptyStr,
            m.Field(description="Configured uv installation link mode"),
        ]
        toolchain: Annotated[
            FlextInfraModelsConfigContract.ToolchainSpec,
            m.Field(description="Canonical toolchain consumed by native bootstrap"),
        ]
        mise_selector: Annotated[
            t.NonEmptyStr,
            m.Field(description="Mise backend selector the mise.lock pin is read from"),
        ]
        mise_version: Annotated[
            t.NonEmptyStr,
            m.Field(
                description="Declared mise release the running binary must match",
            ),
        ]
        mise_install_tools: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Explicit [tools] keys `mise install` provisions in setup "
                    "and upg, so the operator's global Mise registry is never "
                    "installed by a project verb"
                ),
            ),
        ]
        mise_lock_filename: Annotated[
            t.NonEmptyStr,
            m.Field(description="Committed Mise lock of every governed repository"),
        ] = c.Infra.MISE_LOCK_FILENAME
        mise_config_filename: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Only project Mise config the locked bootstrap loads; a "
                    "machine-local override never enters a locked install"
                ),
            ),
        ] = c.Infra.MISE_TOML_FILENAME
        uv_lock_filename: Annotated[
            t.NonEmptyStr,
            m.Field(description="Committed native uv lock of the runtime root"),
        ] = c.Infra.UV_LOCK_FILENAME
        executor_installs_project: Annotated[
            bool,
            m.Field(
                description=(
                    "The project belongs to the infrastructure distribution's "
                    "runtime closure, so the upgrade executor installs the "
                    "project's locked non-editable build instead of excluding it"
                ),
            ),
        ]
        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python minor line the environment syncs against"),
        ]

    class MakefileRenderSpec(MakefileToolchainRenderSpec):
        """Typed render input for an existing repository Makefile."""

        make: Annotated[
            FlextInfraModelsConfigMake.MakeSpec,
            m.Field(description="Generated Make command contract"),
        ]
        extra_verbs: Annotated[
            tuple[
                FlextInfraModelsConfigMake.MakeVerbSpec,
                ...,
            ],
            m.Field(description="Repository-specific public Make verbs"),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraModelsConfigContexts.ScriptDispatchSpec | None,
            m.Field(description="Optional script command dispatch contract"),
        ] = None
        verb_groups: Annotated[
            tuple[
                FlextInfraModelsConfigMake.MakeVerbGroupSpec,
                ...,
            ],
            m.Field(description="Ordered `make help` sections; empty is flat"),
        ] = ()

        @m.model_validator(mode="after")
        def _require_common_verb_group(self) -> Self:
            """Declare the canonical verbs' section whenever sections exist.

            Returns:
                The validated render context.

            Raises:
                ValueError: When sections omit ``make.common_verb_group``.

            """
            names = {group.name for group in self.verb_groups}
            if names and self.make.common_verb_group not in names:
                msg = (
                    "verb_groups must declare the canonical section "
                    f"{self.make.common_verb_group!r}: {sorted(names)}"
                )
                raise ValueError(msg)
            return self

        makefile_custom_include: Annotated[
            t.NonEmptyStr,
            m.Field(description="Generated custom Make policy include directive"),
        ]
        workspace_cli_group: Annotated[
            t.NonEmptyStr,
            m.Field(description="CLI group that owns the workspace propagate route"),
        ]
        mypy_timeout_exit_code: Annotated[
            int,
            m.Field(gt=0, description="Wall-time limiter timeout exit code"),
        ]
        timeout_command: Annotated[
            t.NonEmptyStr,
            m.Field(description="Wall-time limiter executable"),
        ]
        timeout_kill_after_seconds: Annotated[
            int,
            m.Field(gt=0, description="Forced-termination grace period"),
        ]
        check_timeout_seconds: Annotated[
            int,
            m.Field(
                gt=0,
                description=(
                    "Make check wall-time bound derived from the largest "
                    "declared budget of the gates it runs"
                ),
            ),
        ]

    class MakeRenderContext(MakeCommandContext):
        """Typed input consumed by the generated Make surface."""

        owns_workspace_manifest: Annotated[
            bool,
            m.Field(
                description="Whether this repository owns the workspace manifest",
            ),
        ] = False
        make: Annotated[
            FlextInfraModelsConfigMake.MakeSpec,
            m.Field(description="Generated Make command contract"),
        ]
        mypy_timeout_exit_code: Annotated[
            int,
            m.Field(gt=0, description="Wall-time limiter timeout exit code"),
        ]
        timeout_command: Annotated[
            t.NonEmptyStr,
            m.Field(description="Wall-time limiter executable"),
        ]
        timeout_kill_after_seconds: Annotated[
            int,
            m.Field(gt=0, description="Forced-termination grace period"),
        ]
        tooling_runtime: Annotated[
            FlextInfraModelsDepsToolConfig.ToolingRuntimeContext,
            m.Field(description="Resolved project/workspace tooling values"),
        ]

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]

        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python major.minor tool value"),
        ]
        uv_link_mode: Annotated[
            t.NonEmptyStr,
            m.Field(description="Configured uv installation link mode"),
        ]
        make_profile: Annotated[
            c.Infra.MakeProfile,
            m.Field(description="Generated Make execution profile"),
        ]
        ruff_delegated_rules: Annotated[
            t.StrTuple,
            m.Field(description="Native rules checked by elected canonical owners"),
        ]
        repository_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Relative path to the declared workspace root"),
        ]
        makefile_custom_include: Annotated[
            str,
            m.Field(
                min_length=1,
                description=("Make directive that includes the custom Make surface"),
            ),
        ]
        workspace_subprojects: Annotated[
            tuple[str, ...],
            m.Field(description="Ordered workspace subproject paths"),
        ] = ()
        extra_verbs: Annotated[
            tuple[
                FlextInfraModelsConfigMake.MakeVerbSpec,
                ...,
            ],
            m.Field(description="Repository-specific additional public Make verbs"),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraModelsConfigContexts.ScriptDispatchSpec | None,
            m.Field(description="Opt-in script command-framework routing contract"),
        ] = None
        workspace_cli_group: Annotated[
            str,
            m.Field(
                description=(
                    "CLI group name for the flext-infra workspace propagate route"
                ),
            ),
        ] = ""

    class ProjectRenderRuntimeContext(FlextInfraModelsConfigContract.ConfigContract):
        """Distribution, tooling runtime and integration of a rendered project."""

        dist: t.NonEmptyStr = m.Field(description="Project distribution identity")
        make_profile: c.Infra.MakeProfile = m.Field(
            description="Selected repository Make profile"
        )
        uv_link_mode: t.NonEmptyStr = m.Field(description="Declared UV link mode")
        tooling_runtime: FlextInfraModelsDepsToolConfig.ToolingRuntimeContext = m.Field(
            description="Resolved tooling document required by project metadata"
        )

        # This render field is the exact
        # projection of ProjectSpec; templates must not infer or default a hook.
        hatch_build_hook_path: Annotated[
            Path | None,
            m.Field(description="Project-relative Hatch custom build hook module"),
        ] = None
        uv_cache_key_files: Annotated[
            Sequence[str],
            m.Field(description="Derived uv editable-build cache-key files"),
        ] = ()
        docs_audit: Annotated[
            FlextInfraModelsConfigContract.DocsAuditOverridesSpec,
            m.Field(
                description="Repository-owned documentation audit declarations",
            ),
        ] = m.Field(
            default_factory=FlextInfraModelsConfigContract.DocsAuditOverridesSpec
        )
        namespace_scan_dirs: Annotated[
            Sequence[str],
            m.Field(
                description=(
                    "Production source roots rendered as the namespace "
                    "validator's declared scan scope; empty keeps every root "
                    "in scope"
                ),
            ),
        ] = ()
        workspace_integration: Annotated[
            FlextInfraModelsConfigRepository.WorkspaceIntegrationSpec | None,
            m.Field(
                description=(
                    "Declared integration provider and branch written into the "
                    "workspace manifest so later renders derive from the "
                    "declaration, never from the checkout"
                ),
            ),
        ] = None

    class ProjectRenderDependencyContext(ProjectRenderRuntimeContext):
        """Scaffold, dependency, tooling and ownership of a rendered project."""

        scaffold: Annotated[
            FlextInfraModelsConfigScaffold.ScaffoldSpec,
            m.Field(description="New-project scaffold policy"),
        ]
        gitignore_sections: Annotated[
            tuple[
                (FlextInfraModelsConfigScaffold.ScaffoldGitignoreSectionSpec),
                ...,
            ],
            m.Field(
                min_length=1,
                description=(
                    "Canonical .gitignore sections derived from the artifact SSOT"
                ),
            ),
        ]
        project_dependencies: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Target-owned runtime requirements"),
        ]
        development_dependencies: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Development policy composed for the target's kind"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolConfig.ToolConfigDocument,
            m.Field(description="Canonical validated tooling policy"),
        ]
        environment_path_prepends: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Configured read-only PATH additions for direnv"),
        ] = ()
        beads: Annotated[
            FlextInfraModelsConfigBeads.BeadsProjectSpec | None,
            m.Field(description="Repository-local Beads identity when enabled"),
        ] = None
        ownership_command_prefix: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Configured Beads ownership command"),
        ]

    class ProjectRenderPackageContext(ProjectRenderDependencyContext):
        """Package identity, namespace and entry points of a rendered project."""

        canonical_project_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical PEP 621 project name"),
        ]
        const_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Configured constant project name"),
        ]
        package: Annotated[
            bool,
            m.Field(description="Repository publishes a Python package"),
        ]
        package_name: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Python import package name; absent without a package"),
        ]
        packaged_data_paths: Annotated[
            Sequence[str],
            m.Field(
                description="Validated relative data paths shipped in distributions",
            ),
        ]
        project_declaration_resource: Annotated[
            tuple[t.NonEmptyStr, t.NonEmptyStr] | None,
            m.Field(
                description=(
                    "Producer declaration source and wheel extra-metadata destination"
                ),
            ),
        ]
        packaged_data_excludes: Annotated[
            Sequence[str],
            m.Field(description="Validated files excluded from packaged data roots"),
        ] = ()
        class_stem: Annotated[
            t.NonEmptyStr,
            m.Field(description="Public facade class stem"),
        ]
        ns: Annotated[t.NonEmptyStr, m.Field(description="Public model namespace")]
        ns_attr: Annotated[
            t.NonEmptyStr,
            m.Field(description="Private namespace module token"),
        ]
        alias: Annotated[t.NonEmptyStr, m.Field(description="Public instance alias")]
        env_prefix: Annotated[
            t.NonEmptyStr,
            m.Field(description="Settings environment prefix"),
        ]
        upstream: Annotated[
            t.NonEmptyStr,
            m.Field(description="Upstream FLEXT facade module"),
        ]
        inherited_facets: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Upstream facets re-exported by the project root; see the "
                    "RepositoryRef namesake for the lazy-init contract."
                ),
            ),
        ] = ()
        root_packages: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Additional shipped top-level packages; see the ProjectSpec "
                    "namesake for the declaration contract."
                ),
            ),
        ] = ()
        repository_namespace_packages: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                description=(
                    "Implicit namespace directories shipped from the repository root"
                ),
            ),
        ] = ()
        root_modules: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Additional shipped top-level modules; see the ProjectSpec "
                    "namesake for the declaration contract."
                ),
            ),
        ] = ()
        cli_module: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the package ships its cli entry module; see the "
                    "ProjectSpec namesake."
                ),
            ),
        ]
        console_scripts: Annotated[
            tuple[
                FlextInfraModelsConfigRepository.ConsoleScriptSpec,
                ...,
            ],
            m.Field(
                default=(),
                description=(
                    "Additional console scripts; see the ProjectSpec namesake."
                ),
            ),
        ] = ()
        runtime_dependency_overlay: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                default=(),
                description=(
                    "Repository-declared runtime requirements rendered ahead of "
                    "the dependency profile's runtime set; see the ProjectSpec "
                    "namesake."
                ),
            ),
        ] = ()

    class ProjectRenderContext(ProjectRenderPackageContext):
        """Complete typed input consumed by project scaffold templates."""

        @m.computed_field
        @property
        def repository_env_prefix(self) -> str:
            """Settings environment prefix derived from the distribution name.

            Returns:
                The resulting ``str``.

            """
            return f"{self.dist.upper().replace('-', '_')}_"

        @property
        def _config_base(self) -> p.Infra.ScaffoldConfigBaseSpec | None:
            """ENFORCE-042 config base selected from declared requirements.

            A repository without a package composes no ``_config.py`` and elects
            no base.

            The fleet-converged ``_config.py`` inherits only the project's frozen
            config capability base, independently of runtime settings. The base
            is a property of the target's own dependencies, never a per-project
            hand choice: the
            first entry of ``scaffold.project.config_bases`` whose distribution
            target depends on (its runtime requirements or its upstream).

            Raises:
                ValueError: If scaffold.project.config_bases declares no base for the
                    declared requirements of.

            """
            if not self.package:
                return None
            depended = {
                t.Infra.REQUIREMENT_NAME_ADAPTER.validate_python(requirement)
                for requirement in self.project_dependencies
            } | {t.Infra.DISTRIBUTION_NAME_ADAPTER.validate_python(self.upstream)}
            for base in self.scaffold.project.config_bases:
                if base.module == self.upstream:
                    return base
            for base in self.scaffold.project.config_bases:
                if base.distribution in depended:
                    return base
            msg = (
                "scaffold.project.config_bases declares no base for the "
                f"declared requirements of {self.dist}: {sorted(depended)}"
            )
            raise ValueError(msg)

        @m.computed_field
        @property
        def config_base_class(self) -> str | None:
            """Config base class composed by the generated ``_config.py``.

            Returns:
                The base class name, or None without a package.

            """
            base = self._config_base
            return None if base is None else base.class_name

        @m.computed_field
        @property
        def config_base_module(self) -> str | None:
            """Import module exposing ``config_base_class``.

            Returns:
                The base module, or None without a package.

            """
            base = self._config_base
            return None if base is None else base.module

        @m.computed_field
        @property
        def settings_base_class(self) -> str | None:
            """Settings base class composed by the generated ``_settings.py``.

            It lives in ``config_base_module``, so both projections follow the
            same declared dependency profile.

            Returns:
                The settings base class name, or None without a package.

            """
            base = self._config_base
            return None if base is None else base.settings_class_name

        description: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project description"),
        ]
        documentation_language: t.Infra.DocumentationLanguage = m.Field(
            default="en", description="Project-local generated documentation language"
        )
        version: Annotated[t.NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[t.NonEmptyStr, m.Field(description="SPDX license id")]
        python_required_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="PEP 440 project Python requirement"),
        ]
        dependency_cooldown_days: Annotated[
            int,
            m.Field(
                ge=1,
                description="Supply-chain cooldown rendered as mise release age",
            ),
        ]
        author_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Author display name"),
        ]
        author_email: Annotated[t.NonEmptyStr, m.Field(description="Author email")]
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project repository page URL"),
        ]
        homepage: Annotated[t.NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project documentation URL"),
        ]
        flext_git_base_url: Annotated[
            t.NonEmptyStr,
            m.Field(description="FLEXT Git provider base URL"),
        ]
        flext_git_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="FLEXT Git provider branch"),
        ]
        repository_provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key the repository declares for itself"),
        ]
        repository_git_url: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical repository Git clone URL"),
        ]
        repository_branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical repository Git branch"),
        ]
        year: Annotated[int, m.Field(description="Copyright year")]

        @m.field_validator("hatch_build_hook_path")
        @classmethod
        def _validate_hatch_build_hook_path(cls, value: Path | None) -> Path | None:
            return FlextInfraModelsConfigContexts.validated_hatch_build_hook_path(
                value,
            )

    class ProfileSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Execution semantics for one generated Make profile."""

        name: Annotated[
            c.Infra.MakeProfile,
            m.Field(description="Closed Make profile name"),
        ]
        environment_scope: Annotated[
            t.NonEmptyStr,
            m.Field(description="uv environment ownership"),
        ]
        setup_scope: Annotated[
            t.NonEmptyStr,
            m.Field(description="setup orchestration scope"),
        ]
        execution_scope: Annotated[
            t.NonEmptyStr,
            m.Field(description="check/test runtime scope"),
        ]
        discovery_scope: Annotated[
            Literal["gitmodules", "none"],
            m.Field(description="repository-local discovery authority"),
        ]


__all__: list[str] = ["FlextInfraModelsConfigContexts"]
