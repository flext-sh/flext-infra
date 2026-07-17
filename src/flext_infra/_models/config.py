"""Pure Pydantic config and codegen contracts for flext-infra.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal

from annotated_types import Len
from pydantic import HttpUrl

from flext_cli import m
from flext_infra._constants.codegen_project import FlextInfraConstantsCodegenProject
from flext_infra._models.deps_tool_config import FlextInfraModelsDepsToolSettings

# Local non-empty string contract (external annotated_types only; no facade).
type NonEmptyStr = Annotated[str, Len(1)]


# NOTE (multi-agent, mro-wkii.17.26.2.26 / agent: codex): these fragments use
# the same semantics in Python ``re`` and ECMA-262 Unicode regular expressions.
_STRICT_END = r"(?![\s\S])"
_WINDOWS_DEVICE_STEM = (
    r"(?:[Cc][Oo][Nn]|[Pp][Rr][Nn]|[Aa][Uu][Xx]|[Nn][Uu][Ll]|"
    r"[Cc][Oo][Mm][1-9]|[Ll][Pp][Tt][1-9])"
)
_PORTABLE_PATH_COMPONENT = (
    rf"(?=[A-Za-z0-9._-]{{1,255}}(?:/|{_STRICT_END}))"
    rf"(?!{_WINDOWS_DEVICE_STEM}(?:[.]|/|{_STRICT_END}))"
    r"[A-Za-z0-9._-]*[A-Za-z0-9_-]"
)
_PORTABLE_RELATIVE_PATH_PATTERN = (
    rf"^{_PORTABLE_PATH_COMPONENT}(?:/{_PORTABLE_PATH_COMPONENT})*{_STRICT_END}"
)
_STRICT_TEXT_PATTERN = (
    rf"^[^\s\x00-\x1F\x7F]"
    rf"(?:[^\x00-\x1F\x7F]*[^\s\x00-\x1F\x7F])?{_STRICT_END}"
)
_ENVIRONMENT_VARIABLE_PATTERN = rf"^[A-Za-z_][A-Za-z0-9_]*{_STRICT_END}"
_TOOL_IDENTIFIER_PATTERN = rf"^[A-Za-z0-9][A-Za-z0-9._-]*{_STRICT_END}"

# NOTE (multi-agent, mro-wkii.17.26.2.21 / agent: codex): every configured
# repository-relative write root shares this single portable field grammar.
type _PortableRelativePath = Annotated[
    NonEmptyStr, m.Field(pattern=_PORTABLE_RELATIVE_PATH_PATTERN)
]
type _StrictText = Annotated[NonEmptyStr, m.Field(pattern=_STRICT_TEXT_PATTERN)]
type _EnvironmentVariableName = Annotated[
    NonEmptyStr, m.Field(max_length=255, pattern=_ENVIRONMENT_VARIABLE_PATTERN)
]
type _ToolIdentifier = Annotated[
    NonEmptyStr, m.Field(max_length=255, pattern=_TOOL_IDENTIFIER_PATTERN)
]
type _RepositoryRootFileName = Annotated[
    NonEmptyStr, m.Field(pattern=r"^\.?[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*$")
]


class _ConfigContract(m.ContractModel):
    """Private declarative base for schema-loaded codegen records."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): rendered file payloads are
    # byte contracts; Pydantic must never trim their final newline.
    model_config = m.ConfigDict(
        strict=False,
        frozen=True,
        extra="forbid",
        str_strip_whitespace=False,
        regex_engine="python-re",
    )


class FlextInfraConfigModels:
    """Field-only models for config loading and codegen plans."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these models replace the
    # former model-less workspace/make dictionaries. YAML is accepted only at
    # the flext-cli loading boundary and is immediately model-validated here.

    class ToolchainSpec(_ConfigContract):
        """Python selector and exact uv version shared by generated projects."""

        python_version: Annotated[
            NonEmptyStr, m.Field(description="Python toolchain version selector")
        ]
        python_minor_version: Annotated[
            NonEmptyStr,
            m.Field(description="Python major.minor tool configuration value"),
        ]
        python_required_version: Annotated[
            NonEmptyStr, m.Field(description="PEP 440 project Python requirement")
        ]
        # mro-wkii.17.26 (codex): model every generated mise tool pin.
        ruff_version: Annotated[
            NonEmptyStr, m.Field(description="Exact Ruff version for mise")
        ]
        uv_version: Annotated[NonEmptyStr, m.Field(description="Exact uv version")]
        uv_required_version: Annotated[
            NonEmptyStr, m.Field(description="PEP 440 uv required-version expression")
        ]
        uv_link_mode: Annotated[
            NonEmptyStr, m.Field(description="Portable uv installation link mode")
        ]

    class ProviderSpec(_ConfigContract):
        """One GitHub organization and its mandatory branch policy."""

        name: Annotated[NonEmptyStr, m.Field(description="Provider key")]
        organization: Annotated[NonEmptyStr, m.Field(description="GitHub organization")]
        base_url: Annotated[NonEmptyStr, m.Field(description="GitHub HTTPS base URL")]
        branch: Annotated[NonEmptyStr, m.Field(description="Provider branch")]

    class ProfileSpec(_ConfigContract):
        """Execution semantics for one generated Make profile."""

        name: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Closed Make profile name"),
        ]
        environment_scope: Annotated[
            NonEmptyStr, m.Field(description="uv environment ownership")
        ]
        setup_scope: Annotated[
            NonEmptyStr, m.Field(description="setup orchestration scope")
        ]
        execution_scope: Annotated[
            NonEmptyStr, m.Field(description="check/test runtime scope")
        ]
        discovery_scope: Annotated[
            NonEmptyStr, m.Field(description="repository discovery policy")
        ]

    class MakeVerbSpec(_ConfigContract):
        """One public Make verb and its single default selector."""

        name: Annotated[NonEmptyStr, m.Field(description="Public Make verb")]
        default_what: Annotated[
            NonEmptyStr, m.Field(description="Default WHAT selector")
        ]
        apply_guarded: Annotated[
            bool, m.Field(description="Whether mutation requires APPLY=Y")
        ] = False

    class CustomHandlerPolicy(_ConfigContract):
        """Strict schema for the only handwritten Make extension file."""

        filename: Annotated[
            NonEmptyStr, m.Field(description="Versioned custom handler filename")
        ]
        target_pattern: Annotated[
            NonEmptyStr,
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
            NonEmptyStr, m.Field(description="Single selector variable name")
        ]
        apply_variable: Annotated[
            NonEmptyStr, m.Field(description="Write-enable variable name")
        ]
        apply_value: Annotated[
            NonEmptyStr, m.Field(description="Only accepted write-enable value")
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
        owner: Annotated[NonEmptyStr, m.Field(description="Canonical owner")]
        overwrite: Annotated[
            bool, m.Field(description="Whether clean committed content may be replaced")
        ]

    class TemplateEntrySpec(_ConfigContract):
        """One scaffold-only template mapping consumed by ``codegen new``."""

        source: Annotated[Path, m.Field(description="Template-root-relative source")]
        destination: Annotated[
            NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
        ]
        profiles: Annotated[
            tuple[FlextInfraConstantsCodegenProject.MakeProfile, ...],
            m.Field(description="Profiles that consume the template"),
        ]
        delegate: Annotated[
            NonEmptyStr, m.Field(description="Canonical rendering delegate")
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

        backend: Annotated[NonEmptyStr, m.Field(description="PEP 517 backend")]
        requirements: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(min_length=1, description="Build-system requirements"),
        ]

    class ResourceSpec(_ConfigContract):
        """One PEP-compliant repository resource root and wheel mapping."""

        source: Annotated[
            Path, m.Field(description="Repository-root-relative resource directory")
        ]
        required: Annotated[
            bool, m.Field(description="Whether every Python project requires the root")
        ] = False
        wheel_destination: Annotated[
            NonEmptyStr | None,
            m.Field(
                description=(
                    "Package-relative wheel destination with {package_name} support"
                )
            ),
        ] = None

    class ScaffoldDependencyProfileSpec(_ConfigContract):
        """Dependencies selected by the declared upstream FLEXT facade."""

        upstream: Annotated[
            NonEmptyStr, m.Field(description="Supported upstream facade package")
        ]
        runtime: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(min_length=1, description="Runtime requirements"),
        ]
        codegen: Annotated[
            tuple[NonEmptyStr, ...], m.Field(description="Code-generation requirements")
        ] = ()
        dev: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(description="Development and validation requirements"),
        ] = ()

    class ScaffoldProjectSpec(_ConfigContract):
        """Project metadata policy for newly scaffolded distributions."""

        readme: Annotated[NonEmptyStr, m.Field(description="PEP 621 readme path")]
        supported_licenses: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(min_length=1, description="Licenses with complete templates"),
        ]
        classifiers: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(min_length=1, description="Default PyPI classifiers"),
        ]
        keywords: Annotated[
            tuple[NonEmptyStr, ...], m.Field(description="Default project keywords")
        ] = ()
        dependency_profiles: Annotated[
            tuple[FlextInfraConfigModels.ScaffoldDependencyProfileSpec, ...],
            m.Field(min_length=1, description="Upstream dependency profiles"),
        ]

    class ScaffoldPingExampleSpec(_ConfigContract):
        """Values for the functional ping example created only by codegen new."""

        command_name: Annotated[NonEmptyStr, m.Field(description="Public CLI command")]
        help_text: Annotated[
            NonEmptyStr, m.Field(description="Public CLI command help")
        ]
        success_message: Annotated[
            NonEmptyStr, m.Field(description="CLI success message")
        ]
        enabled_default: Annotated[
            bool, m.Field(description="Default runtime enablement")
        ]
        reply: Annotated[NonEmptyStr, m.Field(description="Enabled ping response")]
        disabled_reply: Annotated[
            NonEmptyStr, m.Field(description="Disabled ping response")
        ]

    class ScaffoldGitignoreSectionSpec(_ConfigContract):
        """One configured section of the generated Git ignore policy."""

        name: Annotated[NonEmptyStr, m.Field(description="Section heading")]
        patterns: Annotated[
            tuple[NonEmptyStr, ...],
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
        resources: Annotated[
            tuple[FlextInfraConfigModels.ResourceSpec, ...],
            m.Field(min_length=1, description="Canonical repository resource roots"),
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

        name: Annotated[NonEmptyStr, m.Field(description="Catalog key")]
        distribution: Annotated[
            NonEmptyStr, m.Field(description="Python distribution or repository name")
        ]
        url: Annotated[
            NonEmptyStr,
            m.Field(description="Canonical GitHub clone URL ending in .git"),
        ]
        branch: Annotated[NonEmptyStr, m.Field(description="Required Git branch")]
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
            NonEmptyStr,
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

    # mro-wkii.17 (Codex): project creation metadata remains a typed manifest input.
    class ProjectSpec(_ConfigContract):
        """Deterministic project metadata required to materialize a new tree."""

        package_name: Annotated[NonEmptyStr, m.Field(description="Import package name")]
        class_stem: Annotated[
            NonEmptyStr, m.Field(description="Canonical public facade class stem")
        ]
        namespace: Annotated[
            NonEmptyStr, m.Field(description="Nested c/t/p/m/u namespace")
        ]
        constant_name: Annotated[
            NonEmptyStr,
            m.Field(description="Configured project name exposed through constants"),
        ]
        namespace_attribute: Annotated[
            NonEmptyStr, m.Field(description="Private module namespace token")
        ]
        alias: Annotated[
            NonEmptyStr, m.Field(description="Canonical public instance alias")
        ]
        environment_prefix: Annotated[
            NonEmptyStr, m.Field(description="Project settings environment prefix")
        ]
        description: Annotated[NonEmptyStr, m.Field(description="Project description")]
        version: Annotated[NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[NonEmptyStr, m.Field(description="SPDX license id")]
        author_name: Annotated[NonEmptyStr, m.Field(description="Author display name")]
        author_email: Annotated[NonEmptyStr, m.Field(description="Author email")]
        upstream: Annotated[
            NonEmptyStr, m.Field(description="Upstream FLEXT facade module")
        ]
        homepage: Annotated[NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            NonEmptyStr, m.Field(description="Project documentation URL")
        ]
        workspace_root_rel: Annotated[
            NonEmptyStr,
            m.Field(description="Declared relative path to the workspace root"),
        ]
        year: Annotated[int, m.Field(ge=2025, description="Copyright year")]
        resources: Annotated[
            tuple[FlextInfraConfigModels.ResourceSpec, ...],
            m.Field(description="Additional project-specific resource roots"),
        ] = ()

    class ProjectRenderContext(_ConfigContract):
        """Complete typed input consumed by the universal project templates."""

        scaffold: Annotated[
            FlextInfraConfigModels.ScaffoldSpec,
            m.Field(description="New-project scaffold policy"),
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
        mypy_signal_exit_offset: Annotated[
            int, m.Field(gt=0, description="Shell signal exit-code offset")
        ]
        prlimit_command: Annotated[
            NonEmptyStr, m.Field(description="Address-space limiter executable")
        ]
        prlimit_address_space_option: Annotated[
            NonEmptyStr, m.Field(description="Address-space limiter option")
        ]
        timeout_command: Annotated[
            NonEmptyStr, m.Field(description="Wall-time limiter executable")
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

        dist: Annotated[NonEmptyStr, m.Field(description="Distribution name")]
        const_name: Annotated[
            NonEmptyStr, m.Field(description="Configured constant project name")
        ]
        package_name: Annotated[
            NonEmptyStr, m.Field(description="Python import package name")
        ]
        packaged_data_dirs: Annotated[
            Sequence[str],
            m.Field(description="Generated root data directories shipped in wheels"),
        ]
        class_stem: Annotated[
            NonEmptyStr, m.Field(description="Public facade class stem")
        ]
        ns: Annotated[NonEmptyStr, m.Field(description="Public model namespace")]
        ns_attr: Annotated[
            NonEmptyStr, m.Field(description="Private namespace module token")
        ]
        alias: Annotated[NonEmptyStr, m.Field(description="Public instance alias")]
        env_prefix: Annotated[
            NonEmptyStr, m.Field(description="Settings environment prefix")
        ]
        upstream: Annotated[
            NonEmptyStr, m.Field(description="Upstream FLEXT facade module")
        ]
        description: Annotated[NonEmptyStr, m.Field(description="Project description")]
        version: Annotated[NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[NonEmptyStr, m.Field(description="SPDX license id")]
        python_version: Annotated[
            NonEmptyStr, m.Field(description="Python major.minor tool value")
        ]
        python_toolchain_version: Annotated[
            NonEmptyStr, m.Field(description="Python toolchain version selector")
        ]
        python_required_version: Annotated[
            NonEmptyStr, m.Field(description="PEP 440 project Python requirement")
        ]
        uv_version: Annotated[
            NonEmptyStr, m.Field(description="Exact uv toolchain version")
        ]
        uv_required_version: Annotated[
            NonEmptyStr, m.Field(description="PEP 440 uv requirement")
        ]
        uv_link_mode: Annotated[
            NonEmptyStr, m.Field(description="Configured uv installation link mode")
        ]
        author_name: Annotated[NonEmptyStr, m.Field(description="Author display name")]
        author_email: Annotated[NonEmptyStr, m.Field(description="Author email")]
        repository: Annotated[
            NonEmptyStr, m.Field(description="Project repository page URL")
        ]
        homepage: Annotated[NonEmptyStr, m.Field(description="Project homepage")]
        documentation: Annotated[
            NonEmptyStr, m.Field(description="Project documentation URL")
        ]
        flext_git_base_url: Annotated[
            NonEmptyStr, m.Field(description="FLEXT Git provider base URL")
        ]
        flext_git_branch: Annotated[
            NonEmptyStr, m.Field(description="FLEXT Git provider branch")
        ]
        make_profile: Annotated[
            FlextInfraConstantsCodegenProject.MakeProfile,
            m.Field(description="Generated Make execution profile"),
        ]
        workspace_root_rel: Annotated[
            NonEmptyStr,
            m.Field(description="Relative path to the declared workspace root"),
        ]
        repository_provider: Annotated[
            NonEmptyStr, m.Field(description="Repository provider catalog key")
        ]
        repository_git_url: Annotated[
            NonEmptyStr, m.Field(description="Canonical repository Git clone URL")
        ]
        repository_branch: Annotated[
            NonEmptyStr, m.Field(description="Canonical repository Git branch")
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
        project_resources: Annotated[
            tuple[FlextInfraConfigModels.ResourceSpec, ...],
            m.Field(description="Additional resources declared by this project"),
        ] = ()
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

    class WorkspaceExclusionSpec(_ConfigContract):
        """One explicitly rejected workspace path and its reason."""

        path: Annotated[Path, m.Field(description="Workspace-relative path")]
        reason: Annotated[NonEmptyStr, m.Field(description="Exclusion rationale")]

    class WorkspaceSpec(_ConfigContract):
        """Declared topology for exactly one orchestrated workspace."""

        version: Annotated[int, m.Field(ge=1, description="Manifest version")]
        name: Annotated[NonEmptyStr, m.Field(description="Workspace name")]
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

        name: Annotated[NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            NonEmptyStr, m.Field(description="Root repository catalog key")
        ]
        manifest: Annotated[
            Path, m.Field(description="Repository-relative manifest path")
        ]

    # mro-wkii.17.26 (codex): official compiler normalization is validated data.
    class GrpcCodegenSpec(_ConfigContract):
        """Canonical normalization policy for official compiler modules."""

        ruff_safe_fixes: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(min_length=1, description="Ordered safe Ruff fix selectors"),
        ]

    class CodegenConfigSpec(_ConfigContract):
        """Fully modeled content of ``config/codegen.yaml``."""

        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        grpc: Annotated[
            FlextInfraConfigModels.GrpcCodegenSpec,
            m.Field(description="gRPC generated-source normalization policy"),
        ]
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

    # NOTE (multi-agent, mro-wkii.17.26.2.7 / agent: codex): model the exact
    # external YAML envelope so its JSON Schema is generated, never hand-mirrored.
    class CodegenConfigNamespaceSpec(_ConfigContract):
        """Typed ``Infra`` namespace stored in ``config/codegen.yaml``."""

        codegen: Annotated[
            FlextInfraConfigModels.CodegenConfigSpec,
            m.Field(description="Canonical code-generation configuration"),
        ]

    # NOTE (multi-agent, mro-wkii.17.26.2.21 / agent: codex): config owns the
    # generated schema identity and destination; the model owns only its fields.
    class CodegenSchemaSpec(_ConfigContract):
        """Repository destination and JSON Schema identity for codegen config."""

        path: Annotated[
            _PortableRelativePath,
            m.Field(description="Owner-repository-relative schema path"),
        ]
        dialect: Annotated[
            HttpUrl, m.Field(description="JSON Schema dialect identifier")
        ]
        identifier: Annotated[
            HttpUrl, m.Field(description="Published schema identifier")
        ]
        title: Annotated[_StrictText, m.Field(description="Published schema title")]

    class CodegenConfigDocumentSpec(_ConfigContract):
        """Complete schema-generating contract for ``config/codegen.yaml``."""

        Infra: Annotated[
            FlextInfraConfigModels.CodegenConfigNamespaceSpec,
            m.Field(description="FLEXT Infra configuration namespace"),
        ]

    class WorktreeTransactionLintCommandSpec(_ConfigContract):
        """One lint command captured around an isolated transaction."""

        tool: Annotated[_ToolIdentifier, m.Field(description="Lint tool identifier")]
        command: Annotated[
            tuple[_StrictText, ...],
            m.Field(min_length=1, description="Complete lint command arguments"),
        ]

    # NOTE (multi-agent, mro-wkii.17.26.2.21 / agent: codex): the field grammar
    # rejects non-portable paths before transaction code can construct a Path.
    class WorktreeTransactionSpec(_ConfigContract):
        """Operator policy for complete isolated worktree transactions."""

        environment_variable: Annotated[
            _EnvironmentVariableName,
            m.Field(description="Child-process recursion guard variable"),
        ]
        active_value: Annotated[
            _StrictText, m.Field(description="Value activating the recursion guard")
        ]
        root: Annotated[
            _PortableRelativePath,
            m.Field(description="Portable repository-relative transaction directory"),
        ]
        preserved_ignored_paths: Annotated[
            tuple[_RepositoryRootFileName, ...],
            m.Field(
                min_length=1,
                description=(
                    "Generated ignored files reproduced in the isolated checkpoint"
                ),
            ),
        ]
        timeout_seconds: Annotated[
            int,
            m.Field(gt=0, description="Maximum duration of each transaction command"),
        ]
        lint_commands: Annotated[
            tuple[FlextInfraConfigModels.WorktreeTransactionLintCommandSpec, ...],
            m.Field(min_length=1, description="Ordered transaction lint commands"),
        ]

    # NOTE (multi-agent, mro-wkii.17.24 / agent: codex): production source
    # selection is modeled once for iteration and census.
    class SourceScanSpec(_ConfigContract):
        """Canonical production roots and recursively ignored directories."""

        roots: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(description="Ordered production source directory names"),
        ]
        ignored_resources: Annotated[
            frozenset[NonEmptyStr],
            m.Field(
                min_length=1,
                description="File or directory names excluded from every source scan",
            ),
        ]

    # mro-wkii.17.26 (codex): Rope indexes all workspace consumer surfaces;
    # production-only analysis remains independently governed above.
    class RopeIndexSpec(SourceScanSpec):
        """Canonical roots and exclusions for the full Rope semantic universe."""

    class StaticRule(_ConfigContract):
        """Shared immutable metadata for one Rope static-analysis rule."""

        kind: NonEmptyStr = m.Field(description="Violation kind")
        detail: NonEmptyStr = m.Field(description="Root-cause explanation")

    class StaticImportModuleRule(StaticRule):
        """Reject one imported module outside its configured owning project."""

        operator: Literal["import_module"] = m.Field(description="Operator")
        module: NonEmptyStr = m.Field(description="Rejected module root")
        owner_project: NonEmptyStr | None = m.Field(
            default=None, description="Permitted owning project"
        )

    class StaticImportMemberRule(StaticRule):
        """Reject one member imported from a configured module."""

        operator: Literal["import_member"] = m.Field(description="Operator")
        module: NonEmptyStr = m.Field(description="Import source module")
        member: NonEmptyStr = m.Field(description="Rejected imported member")

    class StaticAttributeRule(StaticRule):
        """Reject one member accessed through a semantically imported module alias."""

        operator: Literal["attribute"] = m.Field(description="Operator")
        module: NonEmptyStr = m.Field(description="Imported module")
        member: NonEmptyStr = m.Field(description="Rejected attribute")

    class StaticCallRule(StaticRule):
        """Reject calls to one bare callable name."""

        operator: Literal["call"] = m.Field(description="Operator")
        name: NonEmptyStr = m.Field(description="Rejected callable")

    class StaticCallKeywordRule(StaticRule):
        """Require one keyword in calls to a configured callable."""

        operator: Literal["call_keyword"] = m.Field(description="Operator")
        name: NonEmptyStr = m.Field(description="Callable")
        keyword: NonEmptyStr = m.Field(description="Required keyword")

    class StaticAnnotationRule(StaticRule):
        """Reject one identifier anywhere in an annotation."""

        operator: Literal["annotation"] = m.Field(description="Operator")
        name: NonEmptyStr = m.Field(description="Rejected annotation identifier")

    class StaticBareExceptRule(StaticRule):
        """Reject an exception handler without an exception contract."""

        operator: Literal["bare_except"] = m.Field(description="Operator")

    class StaticAnnotatedStringRule(StaticRule):
        """Reject an annotated target assigned directly to a string literal."""

        operator: Literal["annotated_string"] = m.Field(description="Operator")
        name: NonEmptyStr = m.Field(description="Rejected assignment target")

    class StaticCommentRule(StaticRule):
        """Reject one marker only when Rope classifies its region as a comment."""

        operator: Literal["comment"] = m.Field(description="Operator")
        marker: NonEmptyStr = m.Field(description="Rejected comment marker")

    class StaticPrivateRootImportRule(StaticRule):
        """Reject a private package-root config or settings singleton import."""

        operator: Literal["private_root_import"] = m.Field(description="Operator")
        module: NonEmptyStr = m.Field(
            pattern=r"^_[a-z][a-z0-9_]*$",
            description="Private package-root module basename",
        )
        singleton: NonEmptyStr = m.Field(
            description="Canonical public singleton exported by the package root"
        )
        type_checking_families: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(
                alias="type-checking-families",
                min_length=1,
                description="Private facade families allowed for proven type-only edges",
            ),
        ]
        allow_generated_root_init: bool = m.Field(
            alias="allow-generated-root-init",
            description="Allow the generated package root to assemble this singleton",
        )

    # mro-wkii.17.26 (codex): lint remediation is validated rule data; Rope
    # verifies the configured semantic scope before the closed operator writes.
    class StaticRuffIssueRule(StaticRule):
        """Remediate one Ruff diagnostic through a Rope-verified operator."""

        operator: Literal["ruff_issue"] = m.Field(description="Operator")
        code: NonEmptyStr = m.Field(description="Exact Ruff diagnostic code")
        fix_operator: Literal["insert_test_docstring"] = m.Field(
            alias="fix-operator", description="Closed remediation operator"
        )
        roots: Annotated[
            tuple[NonEmptyStr, ...],
            m.Field(min_length=1, description="Allowed project-relative roots"),
        ]
        scope_kinds: Annotated[
            tuple[Literal["function", "method"], ...],
            m.Field(
                alias="scope-kinds",
                min_length=1,
                description="Allowed Rope semantic object kinds",
            ),
        ]
        name_prefix: NonEmptyStr = m.Field(
            alias="name-prefix", description="Required semantic object-name prefix"
        )
        docstring_template: NonEmptyStr = m.Field(
            alias="docstring-template",
            description="Template rendered from the semantic object summary",
        )

    type StaticRuleSpec = Annotated[
        StaticImportModuleRule
        | StaticImportMemberRule
        | StaticAttributeRule
        | StaticCallRule
        | StaticCallKeywordRule
        | StaticAnnotationRule
        | StaticBareExceptRule
        | StaticAnnotatedStringRule
        | StaticCommentRule
        | StaticPrivateRootImportRule
        | StaticRuffIssueRule,
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

        name: Annotated[NonEmptyStr, m.Field(description="Project distribution name")]
        version: Annotated[NonEmptyStr, m.Field(description="Project release version")]
        codegen_schema: Annotated[
            FlextInfraConfigModels.CodegenSchemaSpec,
            m.Field(description="Generated codegen configuration schema policy"),
        ]
        worktree_transaction: Annotated[
            FlextInfraConfigModels.WorktreeTransactionSpec,
            m.Field(description="Isolated mutation transaction policy"),
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
        rope_index: Annotated[
            FlextInfraConfigModels.RopeIndexSpec,
            m.Field(description="Workspace-wide Rope semantic index contract"),
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
            NonEmptyStr, m.Field(description="Mise/Python version selector")
        ]
        uv_version: Annotated[
            NonEmptyStr, m.Field(description="Exact required uv version")
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
        operation: Annotated[
            Literal["write", "move"],
            m.Field(description="Atomic filesystem operation selected by conformance"),
        ] = "write"
        source_path: Annotated[
            Path | None, m.Field(description="Existing source for a move operation")
        ] = None
        rendered: Annotated[
            str, m.Field(description="Fully rendered expected content for writes")
        ] = ""
        expected_sha256: Annotated[
            NonEmptyStr, m.Field(description="SHA-256 of expected content")
        ]
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
