"""Pure Pydantic config and codegen contracts for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, ClassVar, Literal

from flext_cli import m
from flext_infra import t
from flext_infra._constants.codegen_project import FlextInfraConstantsCodegenProject
from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolSettings


class _ConfigContract(m.ContractModel):
    """Private declarative base for schema-loaded codegen records."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): rendered file payloads are
    # byte contracts; Pydantic must never trim their final newline.
    model_config = m.ConfigDict(
        strict=False, frozen=True, extra="forbid", str_strip_whitespace=False
    )


class FlextInfraConfigModels:
    """Field-only models for config loading and codegen plans."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these models replace the
    # former model-less workspace/make dictionaries. YAML is accepted only at
    # the flext-cli loading boundary and is immediately model-validated here.

    class ToolchainSpec(_ConfigContract):
        """Language-runtime versions shared by generated projects.

        Only the exact-patch ``python_version`` (e.g. ``3.13.11``) and
        ``uv_version`` are declared (single source, chosen by the package-version
        updater). Every PEP 440 expression and the major.minor selector are
        derived, so a version bump touches exactly one value. Linters/type-
        checkers are NOT here: their pins live in the pyproject dependency
        groups (dependency_profiles).
        """

        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact Python patch version, e.g. '3.13.11'"),
        ]
        uv_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact uv version, e.g. '0.11.29'")
        ]
        uv_link_mode: Annotated[
            t.NonEmptyStr, m.Field(description="Portable uv installation link mode")
        ]
        kubectl_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kubectl version, e.g. '1.32.0'")
        ]
        helm_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Helm version, e.g. '3.19.4'")
        ]
        kind_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kind version, e.g. '0.31.0'")
        ]

        @m.computed_field()
        @property
        def python_minor_version(self) -> str:
            """Python major.minor selector derived from the exact patch."""
            major, _, rest = self.python_version.partition(".")
            minor, _, _patch = rest.partition(".")
            return f"{major}.{minor}"

        @m.computed_field()
        @property
        def python_required_version(self) -> str:
            """PEP 440 requirement: exact patch floor, next-minor ceiling."""
            major, _, rest = self.python_version.partition(".")
            minor, _, _patch = rest.partition(".")
            next_minor = int(minor) + 1
            return f">={self.python_version},<{major}.{next_minor}"

        @m.computed_field()
        @property
        def uv_required_version(self) -> str:
            """Exact PEP 440 uv requirement derived from the declared version."""
            return f"=={self.uv_version}"

    class ProviderSpec(_ConfigContract):
        """One GitHub organization and its mandatory branch policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Provider key")]
        organization: Annotated[
            t.NonEmptyStr, m.Field(description="GitHub organization")
        ]
        base_url: Annotated[t.NonEmptyStr, m.Field(description="GitHub HTTPS base URL")]
        branch: Annotated[t.NonEmptyStr, m.Field(description="Provider branch")]

    class ProfileSpec(_ConfigContract):
        """Execution semantics for one generated Make profile."""

        name: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Closed Make profile name"),
        ]
        environment_scope: Annotated[
            t.NonEmptyStr, m.Field(description="uv environment ownership")
        ]
        setup_scope: Annotated[
            t.NonEmptyStr, m.Field(description="setup orchestration scope")
        ]
        execution_scope: Annotated[
            t.NonEmptyStr, m.Field(description="check/test runtime scope")
        ]
        discovery_scope: Annotated[
            t.NonEmptyStr, m.Field(description="repository discovery policy")
        ]

    class MakeVerbSpec(_ConfigContract):
        """One public Make verb and its single default selector."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Public Make verb")]
        default_what: Annotated[
            t.NonEmptyStr, m.Field(description="Default WHAT selector")
        ]
        apply_guarded: Annotated[
            bool, m.Field(description="Whether mutation requires APPLY=Y")
        ] = False

    class ScriptDispatchSpec(_ConfigContract):
        """Opt-in routing of non-builtin verbs to a script command framework."""

        dispatcher: Annotated[
            t.NonEmptyStr,
            m.Field(
                description=(
                    "Repository-relative dispatcher entrypoint that resolves "
                    "scripts/<verb>/<what>.{py,sh} commands"
                )
            ),
        ]
        roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(
                min_length=1,
                description=(
                    "Repository-relative script roots scanned for a matching "
                    "<verb>/<what> command before falling back to a builtin"
                ),
            ),
        ]

    class CustomHandlerPolicy(_ConfigContract):
        """Strict schema for the only handwritten Make extension file."""

        filename: Annotated[
            t.NonEmptyStr, m.Field(description="Versioned custom handler filename")
        ]
        target_pattern: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required private target regular expression"),
        ]
        allow_public_targets: bool = m.Field(description="Permit public targets")
        allow_generated_target_redefinition: bool = m.Field(
            description="Permit generated target redefinition"
        )
        allow_toolchain_declarations: bool = m.Field(
            description="Permit toolchain declarations"
        )
        allow_setup_declarations: bool = m.Field(
            description="Permit setup declarations"
        )
        allow_help_declarations: bool = m.Field(description="Permit help declarations")

    class MakeSpec(_ConfigContract):
        """Complete generated Makefile public and extension contract."""

        selector: Annotated[
            t.NonEmptyStr, m.Field(description="Single selector variable name")
        ]
        apply_variable: Annotated[
            t.NonEmptyStr, m.Field(description="Write-enable variable name")
        ]
        apply_value: Annotated[
            t.NonEmptyStr, m.Field(description="Only accepted write-enable value")
        ]
        verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Ordered canonical public verbs"),
        ]
        custom_handler_policy: Annotated[
            FlextInfraConfigModels.CustomHandlerPolicy,
            m.Field(description="Private custom target policy"),
        ]

    class ManagedFileSpec(_ConfigContract):
        """One versioned file owned by codegen."""

        path: Annotated[Path, m.Field(description="Repository-relative file path")]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical owner")]
        policy: Annotated[
            Literal["full", "merge", "create-only", "delegated", "manual"],
            m.Field(description="Conform ownership and mutation policy"),
        ]

    class TemplateEntrySpec(_ConfigContract):
        """One scaffold-only template mapping consumed by ``codegen new``."""

        source: Annotated[Path, m.Field(description="Template-root-relative source")]
        destination: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
        ]
        profiles: Annotated[
            tuple[FlextInfraConstantsCodegenProject.MakeProfile, ...],
            m.Field(description="Profiles that consume the template"),
        ]
        delegate: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical rendering delegate")
        ]
        overwrite: Annotated[
            bool, m.Field(description="Whether the template owns existing content")
        ] = False

    class TemplatesSpec(_ConfigContract):
        """New-project scaffold root and its complete ordered manifest."""

        root: Annotated[Path, m.Field(description="Package-relative template root")]
        entries: Annotated[
            tuple[FlextInfraConfigModels.TemplateEntrySpec, ...],
            m.Field(description="Complete ordered template manifest"),
        ]

    class ScaffoldBuildSpec(_ConfigContract):
        """Configured Python build backend for newly scaffolded projects."""

        backend: Annotated[t.NonEmptyStr, m.Field(description="PEP 517 backend")]
        requirements: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Build-system requirements"),
        ]

    class ScaffoldDependencyProfileSpec(_ConfigContract):
        """Dependencies selected by the declared upstream FLEXT facade."""

        upstream: Annotated[
            t.NonEmptyStr, m.Field(description="Supported upstream facade package")
        ]
        runtime: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Runtime requirements"),
        ]
        codegen: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Code-generation requirements"),
        ] = ()
        dev: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Development and validation requirements"),
        ] = ()

    class ScaffoldProjectSpec(_ConfigContract):
        """Project metadata policy for newly scaffolded distributions."""

        readme: Annotated[t.NonEmptyStr, m.Field(description="PEP 621 readme path")]
        supported_licenses: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Licenses with complete templates"),
        ]
        classifiers: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Default PyPI classifiers"),
        ]
        keywords: Annotated[
            tuple[t.NonEmptyStr, ...], m.Field(description="Default project keywords")
        ] = ()
        dependency_profiles: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldDependencyProfileSpec, ...],
            m.Field(min_length=1, description="Upstream dependency profiles"),
        ]

    class ScaffoldPingExampleSpec(_ConfigContract):
        """Values for the functional ping example created only by codegen new."""

        command_name: Annotated[
            t.NonEmptyStr, m.Field(description="Public CLI command")
        ]
        help_text: Annotated[
            t.NonEmptyStr, m.Field(description="Public CLI command help")
        ]
        success_message: Annotated[
            t.NonEmptyStr, m.Field(description="CLI success message")
        ]
        enabled_default: Annotated[
            bool, m.Field(description="Default runtime enablement")
        ]
        reply: Annotated[t.NonEmptyStr, m.Field(description="Enabled ping response")]
        disabled_reply: Annotated[
            t.NonEmptyStr, m.Field(description="Disabled ping response")
        ]

    class ScaffoldGitignoreSectionSpec(_ConfigContract):
        """One configured section of the generated Git ignore policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Section heading")]
        patterns: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(min_length=1, description="Ignored path patterns"),
        ]

    class ScaffoldSpec(_ConfigContract):
        """Complete typed policy consumed only by new-project templates."""

        build: Annotated[
            FlextInfraConfigModels.ScaffoldBuildSpec,
            m.Field(description="Build-system policy"),
        ]
        project: Annotated[
            FlextInfraConfigModels.ScaffoldProjectSpec,
            m.Field(description="Project metadata and dependency policy"),
        ]
        ping_example: Annotated[
            FlextInfraConfigModels.ScaffoldPingExampleSpec,
            m.Field(description="Functional scaffold example"),
        ]
        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(min_length=1, description="Generated Git ignore sections"),
        ]

    class RepositoryRef(_ConfigContract):
        """One declared repository and its immutable Git origin contract."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(use_enum_values=False)

        name: Annotated[t.NonEmptyStr, m.Field(description="Catalog key")]
        distribution: Annotated[
            t.NonEmptyStr, m.Field(description="Python distribution or repository name")
        ]
        url: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical GitHub clone URL ending in .git"),
        ]
        branch: Annotated[t.NonEmptyStr, m.Field(description="Required Git branch")]
        path: Annotated[
            Path, m.Field(description="POSIX path relative to its workspace root")
        ]
        role: Annotated[
            FlextInfraConstantsCodegenProject.RepositoryRole,
            m.Field(description="Repository role in the declared topology"),
        ]
        state: Annotated[
            FlextInfraConstantsCodegenProject.RepositoryState,
            m.Field(description="Repository lifecycle state"),
        ] = FlextInfraConstantsCodegenProject.RepositoryState.ACTIVE
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key from the codegen configuration"),
        ]
        profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile | None,
            m.Field(description="Makefile generation profile"),
        ] = None
        checkout: Annotated[
            FlextInfraConstantsCodegenProject.CheckoutKind,
            m.Field(description="Physical checkout topology"),
        ]
        codegen: Annotated[
            FlextInfraConstantsCodegenProject.CodegenKind,
            m.Field(description="Repository code-generation policy"),
        ]
        package: Annotated[
            bool, m.Field(description="Repository publishes a Python package")
        ]
        editable: Annotated[
            bool, m.Field(description="Overlay repository as an editable dependency")
        ]
        read_only: Annotated[
            bool, m.Field(description="Repository rejects generated mutations")
        ]
        extra_verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(
                description=(
                    "Additional public Make verbs this repository dispatches "
                    "beyond the canonical set (e.g. a script command framework)"
                )
            ),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraConfigModels.ScriptDispatchSpec | None,
            m.Field(
                description=(
                    "Opt-in script command-framework routing for non-builtin "
                    "verbs and WHAT selectors; None keeps builtin-only dispatch"
                )
            ),
        ] = None

    # mro-wkii.17 (Codex): project creation metadata remains a typed manifest input.
    class ProjectSpec(_ConfigContract):
        """Deterministic project metadata required to materialize a new tree."""

        package_name: Annotated[
            t.NonEmptyStr, m.Field(description="Import package name")
        ]
        class_stem: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical public facade class stem")
        ]
        namespace: Annotated[
            t.NonEmptyStr, m.Field(description="Nested c/t/p/m/u namespace")
        ]
        constant_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Configured project name exposed through constants"),
        ]
        namespace_attribute: Annotated[
            t.NonEmptyStr, m.Field(description="Private module namespace token")
        ]
        alias: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical public instance alias")
        ]
        environment_prefix: Annotated[
            t.NonEmptyStr, m.Field(description="Project settings environment prefix")
        ]
        description: Annotated[
            t.NonEmptyStr, m.Field(description="Project description")
        ]
        version: Annotated[t.NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[t.NonEmptyStr, m.Field(description="SPDX license id")]
        author_name: Annotated[
            t.NonEmptyStr, m.Field(description="Author display name")
        ]
        author_email: Annotated[t.NonEmptyStr, m.Field(description="Author email")]
        upstream: Annotated[
            t.NonEmptyStr, m.Field(description="Upstream FLEXT facade module")
        ]
        homepage: Annotated[t.NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            t.NonEmptyStr, m.Field(description="Project documentation URL")
        ]
        workspace_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Declared relative path to the workspace root"),
        ]
        year: Annotated[int, m.Field(ge=2025, description="Copyright year")]

    class ProjectRenderContext(_ConfigContract):
        """Complete typed input consumed by the universal project templates."""

        scaffold: Annotated[
            FlextInfraConfigModels.ScaffoldSpec,
            m.Field(description="New-project scaffold policy"),
        ]
        gitignore_sections: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...],
            m.Field(
                min_length=1,
                description=(
                    "Canonical .gitignore sections derived from the artifact SSOT"
                ),
            ),
        ]
        dependency_profile: Annotated[
            FlextInfraConfigModels.ScaffoldDependencyProfileSpec,
            m.Field(description="Resolved upstream dependency profile"),
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Generated Make command contract"),
        ]
        mypy_memory_limit_mb: Annotated[
            int, m.Field(gt=0, description="Generated Mypy address-space limit in MiB")
        ]
        mypy_timeout_seconds: Annotated[
            int, m.Field(gt=0, description="Generated Mypy wall-time limit in seconds")
        ]
        mypy_timeout_exit_code: Annotated[
            int, m.Field(gt=0, description="Wall-time limiter timeout exit code")
        ]
        mypy_signal_exit_offset: Annotated[
            int, m.Field(gt=0, description="Shell signal exit-code offset")
        ]
        prlimit_command: Annotated[
            t.NonEmptyStr, m.Field(description="Address-space limiter executable")
        ]
        prlimit_address_space_option: Annotated[
            t.NonEmptyStr, m.Field(description="Address-space limiter option")
        ]
        timeout_command: Annotated[
            t.NonEmptyStr, m.Field(description="Wall-time limiter executable")
        ]
        timeout_kill_after_seconds: Annotated[
            int, m.Field(gt=0, description="Forced-termination grace period")
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolSettings.ToolConfigDocument,
            m.Field(description="Canonical validated tooling policy"),
        ]
        tooling_runtime: Annotated[
            FlextInfraModelsDepsToolSettings.ToolingRuntimeContext,
            m.Field(description="Resolved project/workspace tooling values"),
        ]

        dist: Annotated[t.NonEmptyStr, m.Field(description="Distribution name")]
        const_name: Annotated[
            t.NonEmptyStr, m.Field(description="Configured constant project name")
        ]
        package_name: Annotated[
            t.NonEmptyStr, m.Field(description="Python import package name")
        ]
        packaged_data_dirs: Annotated[
            t.StrSequence,
            m.Field(description="Generated root data directories shipped in wheels"),
        ]
        class_stem: Annotated[
            t.NonEmptyStr, m.Field(description="Public facade class stem")
        ]
        ns: Annotated[t.NonEmptyStr, m.Field(description="Public model namespace")]
        ns_attr: Annotated[
            t.NonEmptyStr, m.Field(description="Private namespace module token")
        ]
        alias: Annotated[t.NonEmptyStr, m.Field(description="Public instance alias")]
        env_prefix: Annotated[
            t.NonEmptyStr, m.Field(description="Settings environment prefix")
        ]
        upstream: Annotated[
            t.NonEmptyStr, m.Field(description="Upstream FLEXT facade module")
        ]
        description: Annotated[
            t.NonEmptyStr, m.Field(description="Project description")
        ]
        version: Annotated[t.NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[t.NonEmptyStr, m.Field(description="SPDX license id")]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python major.minor tool value")
        ]
        python_toolchain_version: Annotated[
            t.NonEmptyStr, m.Field(description="Python toolchain version selector")
        ]
        python_required_version: Annotated[
            t.NonEmptyStr, m.Field(description="PEP 440 project Python requirement")
        ]
        kubectl_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kubectl toolchain version")
        ]
        helm_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact Helm toolchain version")
        ]
        kind_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact kind toolchain version")
        ]
        uv_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact uv toolchain version")
        ]
        uv_required_version: Annotated[
            t.NonEmptyStr, m.Field(description="PEP 440 uv requirement")
        ]
        uv_link_mode: Annotated[
            t.NonEmptyStr, m.Field(description="Configured uv installation link mode")
        ]
        author_name: Annotated[
            t.NonEmptyStr, m.Field(description="Author display name")
        ]
        author_email: Annotated[t.NonEmptyStr, m.Field(description="Author email")]
        repository: Annotated[
            t.NonEmptyStr, m.Field(description="Project repository page URL")
        ]
        homepage: Annotated[t.NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            t.NonEmptyStr, m.Field(description="Project documentation URL")
        ]
        flext_git_base_url: Annotated[
            t.NonEmptyStr, m.Field(description="FLEXT Git provider base URL")
        ]
        flext_git_branch: Annotated[
            t.NonEmptyStr, m.Field(description="FLEXT Git provider branch")
        ]
        make_profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Generated Make execution profile"),
        ]
        workspace_root_rel: Annotated[
            t.NonEmptyStr,
            m.Field(description="Relative path to the declared workspace root"),
        ]
        repository_provider: Annotated[
            t.NonEmptyStr, m.Field(description="Repository provider catalog key")
        ]
        repository_git_url: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical repository Git clone URL")
        ]
        repository_branch: Annotated[
            t.NonEmptyStr, m.Field(description="Canonical repository Git branch")
        ]
        workspace_manifest_version: Annotated[
            int,
            m.Field(
                ge=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                le=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                description="Workspace manifest schema version",
            ),
        ]
        workspace_repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Repository rendered into the workspace manifest"),
        ]
        year: Annotated[int, m.Field(description="Copyright year")]
        workspace_members: Annotated[
            tuple[str, ...], m.Field(description="Ordered workspace member paths")
        ] = ()
        workspace_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered workspace member records"),
        ] = ()
        workspace_content_only: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered content-only repository records"),
        ] = ()
        workspace_exclusions: Annotated[
            tuple[FlextInfraConfigModels.WorkspaceExclusionSpec, ...],
            m.Field(description="Ordered excluded workspace paths"),
        ] = ()
        extra_verbs: Annotated[
            tuple[FlextInfraConfigModels.MakeVerbSpec, ...],
            m.Field(description="Repository-specific additional public Make verbs"),
        ] = ()
        script_dispatch: Annotated[
            FlextInfraConfigModels.ScriptDispatchSpec | None,
            m.Field(description="Opt-in script command-framework routing contract"),
        ] = None

    class WorkspaceExclusionSpec(_ConfigContract):
        """One explicitly rejected workspace path and its reason."""

        path: Annotated[Path, m.Field(description="Workspace-relative path")]
        reason: Annotated[t.NonEmptyStr, m.Field(description="Exclusion rationale")]

    class WorkspaceSpec(_ConfigContract):
        """Declared topology for exactly one orchestrated workspace."""

        version: Annotated[
            int,
            m.Field(
                ge=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                le=FlextInfraConstantsCodegenProject.WORKSPACE_MANIFEST_VERSION,
                description="Manifest version",
            ),
        ]
        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            FlextInfraConfigModels.RepositoryRef,
            m.Field(description="Root repository Git contract"),
        ]
        project: Annotated[
            FlextInfraConfigModels.ProjectSpec | None,
            m.Field(description="Metadata required only when materializing a new tree"),
        ] = None
        members: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered active member repository contracts"),
        ] = ()
        content_only: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered content-only repository contracts"),
        ] = ()
        exclusions: Annotated[
            tuple[FlextInfraConfigModels.WorkspaceExclusionSpec, ...],
            m.Field(description="Ordered paths deliberately excluded from inventory"),
        ] = ()

    class WorkspaceCatalogRef(_ConfigContract):
        """Global pointer to a local workspace topology manifest."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            t.NonEmptyStr, m.Field(description="Root repository catalog key")
        ]
        manifest: Annotated[
            Path, m.Field(description="Repository-relative manifest path")
        ]

    # NOTE (mro-jnm1.1 / mro-jnm1.4): the artifact list is the SINGLE SSOT for
    # ephemeral/generated resources; VS Code excludes and source_scan ignores
    # are derived projections, never re-declared in YAML.
    class CodegenArtifactSpec(_ConfigContract):
        """One ephemeral/generated resource every ignore/exclude derives from."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Basename of the resource")]
        is_dir: Annotated[bool, m.Field(description="Directory (vs file) resource")] = (
            True
        )
        vscode_exclude: Annotated[
            bool, m.Field(description="Feed VS Code files.exclude + search.exclude")
        ] = True
        watch_exclude: Annotated[
            bool, m.Field(description="Feed VS Code files.watcherExclude")
        ] = True
        gitignore: Annotated[
            bool, m.Field(description="Feed the Python/tool section of .gitignore")
        ] = True
        source_scan_ignore: Annotated[
            bool, m.Field(description="Feed source_scan.ignored_resources")
        ] = False

    class CodegenVscodeSpec(_ConfigContract):
        """Fully modeled content of the ``vscode`` section of ``config/codegen.yaml``."""

        scalar_settings: Annotated[
            Mapping[str, str | bool],
            m.Field(description="VS Code scalar keys enforced on every project"),
        ]
        list_settings: Annotated[
            Mapping[str, tuple[str, ...]],
            m.Field(description="VS Code list keys enforced on every project"),
        ]
        map_union_settings: Annotated[
            Mapping[str, Mapping[str, str | bool]],
            m.Field(description="VS Code map keys union-merged over project settings"),
        ]

    class CodegenConfigSpec(_ConfigContract):
        """Fully modeled content of ``config/codegen.yaml``."""

        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        toolchain: Annotated[
            FlextInfraConfigModels.ToolchainSpec,
            m.Field(description="Exact generated toolchain"),
        ]
        providers: Annotated[
            tuple[FlextInfraConfigModels.ProviderSpec, ...],
            m.Field(description="Ordered Git providers"),
        ]
        profiles: Annotated[
            tuple[FlextInfraConfigModels.ProfileSpec, ...],
            m.Field(description="Ordered Make profiles"),
        ]
        make: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        vscode: Annotated[
            FlextInfraConfigModels.CodegenVscodeSpec,
            m.Field(description="Canonical VS Code settings merge contract"),
        ]
        artifacts: Annotated[
            tuple[FlextInfraConfigModels.CodegenArtifactSpec, ...],
            m.Field(
                min_length=1,
                description=(
                    "Ephemeral/generated artifact SSOT; every ignore/exclude "
                    "projection derives from this list"
                ),
            ),
        ]

        @m.computed_field()
        @property
        def vscode_files_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.exclude`` entries from the artifact SSOT."""
            return {
                f"**/{artifact.name}": True
                for artifact in self.artifacts
                if artifact.vscode_exclude
            }

        @m.computed_field()
        @property
        def vscode_watcher_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``files.watcherExclude`` entries from the SSOT."""
            return {
                f"**/{artifact.name}/**": True
                for artifact in self.artifacts
                if artifact.watch_exclude
            }

        @m.computed_field()
        @property
        def vscode_search_exclude_map(self) -> Mapping[str, bool]:
            """Derived VS Code ``search.exclude`` entries from the artifact SSOT."""
            return self.vscode_files_exclude_map

        @m.computed_field()
        @property
        def source_scan_ignored(self) -> tuple[str, ...]:
            """Derived ``source_scan.ignored_resources`` names from the SSOT."""
            return tuple(
                artifact.name
                for artifact in self.artifacts
                if artifact.source_scan_ignore
            )

        # NOTE (mro-jnm1.2): the canonical .gitignore body is ONE computed
        # projection — the artifact SSOT feeds the Python/build section and the
        # static scaffold sections carry only what the SSOT cannot express
        # (file globs, secrets, editor/OS noise). Per-project exception fields
        # (extra_ignored / allowed dirs) land in WorkspaceSpec with mro-jnm1.3;
        # this projection is the seam they will extend.
        @m.computed_field()
        @property
        def gitignore_sections(
            self,
        ) -> tuple[FlextInfraConfigModels.ScaffoldGitignoreSectionSpec, ...]:
            """Derived canonical ``.gitignore`` sections (SSOT first, deduplicated)."""
            scaffold_sections = self.scaffold.gitignore_sections
            first = scaffold_sections[0]
            merged: t.MutableSequenceOf[str] = list(self.gitignore_artifact_patterns)
            seen = set(merged)
            for pattern in first.patterns:
                if pattern not in seen:
                    seen.add(pattern)
                    merged.append(pattern)
            sections: t.MutableSequenceOf[
                FlextInfraConfigModels.ScaffoldGitignoreSectionSpec
            ] = [
                FlextInfraConfigModels.ScaffoldGitignoreSectionSpec(
                    name=first.name, patterns=tuple(merged)
                )
            ]
            for section in scaffold_sections[1:]:
                patterns = tuple(
                    pattern for pattern in section.patterns if pattern not in seen
                )
                seen.update(patterns)
                if patterns:
                    sections.append(
                        FlextInfraConfigModels.ScaffoldGitignoreSectionSpec(
                            name=section.name, patterns=patterns
                        )
                    )
            return tuple(sections)

        @m.computed_field()
        @property
        def gitignore_artifact_patterns(self) -> tuple[str, ...]:
            """Derived ``.gitignore`` artifact patterns from the SSOT (stable order)."""
            return tuple(
                f"{artifact.name}/" if artifact.is_dir else artifact.name
                for artifact in self.artifacts
                if artifact.gitignore
            )

        managed_files: Annotated[
            tuple[FlextInfraConfigModels.ManagedFileSpec, ...],
            m.Field(description="Files owned by conform"),
        ]
        scaffold: Annotated[
            FlextInfraConfigModels.ScaffoldSpec,
            m.Field(description="Typed new-project scaffold policy"),
        ]
        templates: Annotated[
            FlextInfraConfigModels.TemplatesSpec,
            m.Field(description="New-project-only scaffold template manifest"),
        ]
        repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Ordered repository catalog"),
        ]
        workspaces: Annotated[
            tuple[FlextInfraConfigModels.WorkspaceCatalogRef, ...],
            m.Field(description="Pointers to local workspace topology manifests"),
        ]

    # NOTE (multi-agent, mro-wkii.17.24 / agent: codex): production source
    # selection is modeled once so iteration, Rope, and census share one SSOT.
    class SourceScanSpec(_ConfigContract):
        """Canonical production roots and recursively ignored directories."""

        roots: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Ordered production source directory names"),
        ]

    class StaticRule(_ConfigContract):
        """Shared immutable metadata for one Rope static-analysis rule."""

        kind: t.NonEmptyStr = m.Field(description="Violation kind")
        detail: t.NonEmptyStr = m.Field(description="Root-cause explanation")

    class StaticImportModuleRule(StaticRule):
        """Reject one imported module outside its configured owning project."""

        operator: Literal["import_module"] = m.Field(description="Operator")
        module: t.NonEmptyStr = m.Field(description="Rejected module root")
        owner_project: t.NonEmptyStr | None = m.Field(
            default=None, description="Permitted owning project"
        )

    class StaticImportMemberRule(StaticRule):
        """Reject one member imported from a configured module."""

        operator: Literal["import_member"] = m.Field(description="Operator")
        module: t.NonEmptyStr = m.Field(description="Import source module")
        member: t.NonEmptyStr = m.Field(description="Rejected imported member")

    class StaticAttributeRule(StaticRule):
        """Reject one member accessed through a semantically imported module alias."""

        operator: Literal["attribute"] = m.Field(description="Operator")
        module: t.NonEmptyStr = m.Field(description="Imported module")
        member: t.NonEmptyStr = m.Field(description="Rejected attribute")

    class StaticCallRule(StaticRule):
        """Reject calls to one bare callable name."""

        operator: Literal["call"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Rejected callable")

    class StaticCallKeywordRule(StaticRule):
        """Require one keyword in calls to a configured callable."""

        operator: Literal["call_keyword"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Callable")
        keyword: t.NonEmptyStr = m.Field(description="Required keyword")

    class StaticAnnotationRule(StaticRule):
        """Reject one identifier anywhere in an annotation."""

        operator: Literal["annotation"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Rejected annotation identifier")

    class StaticBareExceptRule(StaticRule):
        """Reject an exception handler without an exception contract."""

        operator: Literal["bare_except"] = m.Field(description="Operator")

    class StaticAnnotatedStringRule(StaticRule):
        """Reject an annotated target assigned directly to a string literal."""

        operator: Literal["annotated_string"] = m.Field(description="Operator")
        name: t.NonEmptyStr = m.Field(description="Rejected assignment target")

    class StaticCommentRule(StaticRule):
        """Reject one marker only when Rope classifies its region as a comment."""

        operator: Literal["comment"] = m.Field(description="Operator")
        marker: t.NonEmptyStr = m.Field(description="Rejected comment marker")

    type StaticRuleSpec = Annotated[
        StaticImportModuleRule
        | StaticImportMemberRule
        | StaticAttributeRule
        | StaticCallRule
        | StaticCallKeywordRule
        | StaticAnnotationRule
        | StaticBareExceptRule
        | StaticAnnotatedStringRule
        | StaticCommentRule,
        m.Field(discriminator="operator"),
    ]

    class StaticEnforcementSpec(_ConfigContract):
        """Complete validated static policy evaluated only through Rope facts."""

        rules: Annotated[
            tuple[FlextInfraConfigModels.StaticRuleSpec, ...],
            m.Field(min_length=1, description="Ordered static-analysis rules"),
        ]

    # NOTE (multi-agent, mro-wkii.9 + mro-wkii.17 / agent: codex): this
    # field-only namespace is the sole validated owner exposed as config.Infra.
    class Infra(_ConfigContract):
        """Complete flext-infra configuration namespace."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Project distribution name")]
        version: Annotated[
            t.NonEmptyStr, m.Field(description="Project release version")
        ]
        codegen: Annotated[
            FlextInfraConfigModels.CodegenConfigSpec,
            m.Field(description="Unified project and workspace codegen contract"),
        ]
        tooling: Annotated[
            FlextInfraModelsDepsToolSettings.ToolConfigDocument,
            m.Field(description="Validated lint, typecheck, and scaffold policy"),
        ]
        source_scan: Annotated[
            FlextInfraConfigModels.SourceScanSpec,
            m.Field(description="Production-only source discovery contract"),
        ]
        # mro-j47u (codex): static policy is validated data, never detector code.
        enforcement: Annotated[
            FlextInfraConfigModels.StaticEnforcementSpec,
            m.Field(description="Rope-only static enforcement policy"),
        ]

    class Root(_ConfigContract):
        """Root payload deep-merged from flext-infra config files."""

        Infra: Annotated[
            FlextInfraConfigModels.Infra,
            m.Field(description="Validated flext-infra namespace"),
        ]

    class UvEnvironmentPlan(_ConfigContract):
        """One deterministic uv environment operation plan."""

        project_root: Annotated[Path, m.Field(description="Selected project root")]
        environment_root: Annotated[
            Path, m.Field(description="Project supplying the active .venv")
        ]
        lock_path: Annotated[Path, m.Field(description="Required versioned uv.lock")]
        python_version: Annotated[
            t.NonEmptyStr, m.Field(description="Mise/Python version selector")
        ]
        uv_version: Annotated[
            t.NonEmptyStr, m.Field(description="Exact required uv version")
        ]
        groups: Annotated[
            tuple[str, ...],
            m.Field(description="Ordered dependency groups synchronized by setup"),
        ]
        editable_repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Local repositories overlaid after locked sync"),
        ] = ()

    class CodegenConformRequest(_ConfigContract):
        """Validated public request for ``flext-infra codegen conform``."""

        root: Annotated[Path, m.Field(description="Repository or workspace root")]
        what: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformSurface,
            m.Field(description="Managed file selection"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformSurface.ALL
        scope: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformScope,
            m.Field(description="Repository selection scope"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformScope.SELF
        mode: Annotated[
            FlextInfraConstantsCodegenProject.CodegenConformMode,
            m.Field(description="Read-only check or atomic apply"),
        ] = FlextInfraConstantsCodegenProject.CodegenConformMode.CHECK

    class CodegenFilePlan(_ConfigContract):
        """Expected content and current state for one managed file."""

        path: Annotated[Path, m.Field(description="Absolute managed file path")]
        rendered: Annotated[str, m.Field(description="Fully rendered expected content")]
        expected_sha256: Annotated[
            t.NonEmptyStr, m.Field(description="SHA-256 of expected content")
        ]
        owner: Annotated[
            str,
            m.Field(description="Canonical artifact owner, empty for scaffold files"),
        ] = ""
        policy: Annotated[
            Literal["full", "merge", "create-only", "delegated", "manual"] | None,
            m.Field(description="Governed root artifact policy"),
        ] = None
        current_sha256: Annotated[
            str, m.Field(description="SHA-256 of current content, empty when missing")
        ] = ""
        changed: Annotated[bool, m.Field(description="Whether content differs")]
        blocked: Annotated[
            bool, m.Field(description="Whether unrecognized WIP blocks application")
        ] = False
        reason: Annotated[str, m.Field(description="Blocking explanation")] = ""

    class CodegenPlan(_ConfigContract):
        """Fully validated plan produced before any managed-file write."""

        request: Annotated[
            FlextInfraConfigModels.CodegenConformRequest,
            m.Field(description="Validated public request"),
        ]
        repositories: Annotated[
            tuple[FlextInfraConfigModels.RepositoryRef, ...],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            FlextInfraConfigModels.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        make_spec: Annotated[
            FlextInfraConfigModels.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        uv_environments: Annotated[
            tuple[FlextInfraConfigModels.UvEnvironmentPlan, ...],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        files: Annotated[
            tuple[FlextInfraConfigModels.CodegenFilePlan, ...],
            m.Field(description="All render results validated before application"),
        ]

    class CodegenResult(_ConfigContract):
        """Public conformance outcome for check and apply modes."""

        plan: Annotated[
            FlextInfraConfigModels.CodegenPlan,
            m.Field(description="Plan that governed the operation"),
        ]
        written_files: Annotated[
            tuple[Path, ...], m.Field(description="Files atomically replaced by apply")
        ] = ()
        errors: Annotated[
            tuple[str, ...],
            m.Field(description="Fail-closed validation or write errors"),
        ] = ()


__all__: list[str] = ["FlextInfraConfigModels"]
