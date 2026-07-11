"""Typed contracts for the unified project conformance pipeline.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import ConfigDict

from flext_cli import m
from flext_infra.constants import c
from flext_infra.typings import t


class _CodegenContract(m.ContractModel):
    """Private declarative base for schema-loaded codegen records."""

    model_config = ConfigDict(strict=False, frozen=True, extra="forbid")


class FlextInfraModelsCodegenConform:
    """Pydantic contracts shared by codegen planning and application."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these models replace the
    # former model-less workspace/make dictionaries. YAML is accepted only at
    # the flext-cli loading boundary and is immediately model-validated here.

    class ToolchainSpec(_CodegenContract):
        """Exact Python and uv versions shared by generated projects."""

        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact Python version"),
        ]
        python_minor_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python major.minor tool configuration value"),
        ]
        python_required_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="PEP 440 project Python requirement"),
        ]
        uv_version: Annotated[t.NonEmptyStr, m.Field(description="Exact uv version")]
        uv_required_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="PEP 440 uv required-version expression"),
        ]

    class ProviderSpec(_CodegenContract):
        """One GitHub organization and its mandatory branch policy."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Provider key")]
        organization: Annotated[
            t.NonEmptyStr,
            m.Field(description="GitHub organization"),
        ]
        base_url: Annotated[
            t.NonEmptyStr,
            m.Field(description="GitHub HTTPS base URL"),
        ]
        branch: Annotated[t.NonEmptyStr, m.Field(description="Provider branch")]

    class ProfileSpec(_CodegenContract):
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
            t.NonEmptyStr,
            m.Field(description="repository discovery policy"),
        ]

    class MakeVerbSpec(_CodegenContract):
        """One public Make verb and its single default selector."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Public Make verb")]
        default_what: Annotated[
            t.NonEmptyStr,
            m.Field(description="Default WHAT selector"),
        ]
        apply_guarded: Annotated[
            bool,
            m.Field(description="Whether mutation requires APPLY=Y"),
        ] = False

    class CustomHandlerPolicy(_CodegenContract):
        """Strict schema for the only handwritten Make extension file."""

        filename: Annotated[
            t.NonEmptyStr,
            m.Field(description="Versioned custom handler filename"),
        ]
        target_pattern: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required private target regular expression"),
        ]
        allow_public_targets: bool = m.Field(description="Permit public targets")
        allow_generated_target_redefinition: bool = m.Field(
            description="Permit generated target redefinition",
        )
        allow_toolchain_declarations: bool = m.Field(
            description="Permit toolchain declarations",
        )
        allow_setup_declarations: bool = m.Field(
            description="Permit setup declarations",
        )
        allow_help_declarations: bool = m.Field(
            description="Permit help declarations",
        )

    class MakeSpec(_CodegenContract):
        """Complete generated Makefile public and extension contract."""

        selector: Annotated[
            t.NonEmptyStr,
            m.Field(description="Single selector variable name"),
        ]
        apply_variable: Annotated[
            t.NonEmptyStr,
            m.Field(description="Write-enable variable name"),
        ]
        apply_value: Annotated[
            t.NonEmptyStr,
            m.Field(description="Only accepted write-enable value"),
        ]
        verbs: Annotated[
            tuple[FlextInfraModelsCodegenConform.MakeVerbSpec, ...],
            m.Field(description="Ordered canonical public verbs"),
        ]
        custom_handler_policy: Annotated[
            FlextInfraModelsCodegenConform.CustomHandlerPolicy,
            m.Field(description="Private custom target policy"),
        ]

    class ManagedFileSpec(_CodegenContract):
        """One versioned file owned by codegen."""

        path: Annotated[
            Path,
            m.Field(description="Repository-relative file path"),
        ]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical owner")]
        overwrite: Annotated[
            bool,
            m.Field(description="Whether clean committed content may be replaced"),
        ]

    class TemplateEntrySpec(_CodegenContract):
        """One template-to-destination mapping shared by new and conform."""

        source: Annotated[
            Path,
            m.Field(description="Template-root-relative source"),
        ]
        destination: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
        ]
        profiles: Annotated[
            tuple[c.Infra.MakeProfile, ...],
            m.Field(description="Profiles that consume the template"),
        ]
        delegate: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical rendering delegate"),
        ]
        overwrite: Annotated[
            bool,
            m.Field(description="Whether the template owns existing content"),
        ] = False

    class TemplatesSpec(_CodegenContract):
        """Universal template root and its complete ordered manifest."""

        root: Annotated[
            Path,
            m.Field(description="Package-relative template root"),
        ]
        entries: Annotated[
            tuple[FlextInfraModelsCodegenConform.TemplateEntrySpec, ...],
            m.Field(description="Complete ordered template manifest"),
        ]

    class RepositoryRef(_CodegenContract):
        """One declared repository and its immutable Git origin contract."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Catalog key")]
        distribution: Annotated[
            t.NonEmptyStr,
            m.Field(description="Python distribution or repository name"),
        ]
        url: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical GitHub clone URL ending in .git"),
        ]
        branch: Annotated[
            t.NonEmptyStr,
            m.Field(description="Required Git branch"),
        ]
        path: Annotated[
            Path,
            m.Field(description="POSIX path relative to its workspace root"),
        ]
        role: Annotated[
            c.Infra.RepositoryRole,
            m.Field(description="Repository role in the declared topology"),
        ]
        state: Annotated[
            c.Infra.RepositoryState,
            m.Field(description="Repository lifecycle state"),
        ] = c.Infra.RepositoryState.ACTIVE
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key from the codegen configuration"),
        ]
        profile: Annotated[
            c.Infra.MakeProfile | None,
            m.Field(description="Makefile generation profile"),
        ] = None

    # mro-wkii.17 (Codex): project creation metadata remains a typed manifest input.
    class ProjectSpec(_CodegenContract):
        """Deterministic project metadata required to materialize a new tree."""

        package_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Import package name"),
        ]
        class_stem: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical public facade class stem"),
        ]
        namespace: Annotated[
            t.NonEmptyStr,
            m.Field(description="Nested c/t/p/m/u namespace"),
        ]
        alias: Annotated[
            t.NonEmptyStr,
            m.Field(description="Canonical public instance alias"),
        ]
        description: Annotated[
            t.NonEmptyStr,
            m.Field(description="Project description"),
        ]
        version: Annotated[t.NonEmptyStr, m.Field(description="Project version")]
        license: Annotated[t.NonEmptyStr, m.Field(description="SPDX license id")]
        author_name: Annotated[
            t.NonEmptyStr,
            m.Field(description="Author display name"),
        ]
        author_email: Annotated[
            t.NonEmptyStr,
            m.Field(description="Author email"),
        ]
        upstream: Annotated[
            t.NonEmptyStr,
            m.Field(description="Upstream FLEXT facade module"),
        ]
        year: Annotated[int, m.Field(ge=2025, description="Copyright year")]

    class WorkspaceExclusionSpec(_CodegenContract):
        """One explicitly rejected workspace path and its reason."""

        path: Annotated[
            Path,
            m.Field(description="Workspace-relative path"),
        ]
        reason: Annotated[t.NonEmptyStr, m.Field(description="Exclusion rationale")]

    class WorkspaceSpec(_CodegenContract):
        """Declared topology for exactly one orchestrated workspace."""

        version: Annotated[int, m.Field(ge=1, description="Manifest version")]
        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            FlextInfraModelsCodegenConform.RepositoryRef,
            m.Field(description="Root repository Git contract"),
        ]
        project: Annotated[
            FlextInfraModelsCodegenConform.ProjectSpec | None,
            m.Field(description="Metadata required only when materializing a new tree"),
        ] = None
        members: Annotated[
            tuple[FlextInfraModelsCodegenConform.RepositoryRef, ...],
            m.Field(description="Ordered active member repository contracts"),
        ] = ()
        content_only: Annotated[
            tuple[FlextInfraModelsCodegenConform.RepositoryRef, ...],
            m.Field(description="Ordered content-only repository contracts"),
        ] = ()
        exclusions: Annotated[
            tuple[FlextInfraModelsCodegenConform.WorkspaceExclusionSpec, ...],
            m.Field(description="Ordered paths deliberately excluded from inventory"),
        ] = ()

    class WorkspaceCatalogRef(_CodegenContract):
        """Global pointer to a local workspace topology manifest."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Root repository catalog key"),
        ]
        manifest: Annotated[
            Path,
            m.Field(description="Repository-relative manifest path"),
        ]

    class CodegenConfigSpec(_CodegenContract):
        """Fully modeled content of ``config/codegen.yaml``."""

        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        toolchain: Annotated[
            FlextInfraModelsCodegenConform.ToolchainSpec,
            m.Field(description="Exact generated toolchain"),
        ]
        providers: Annotated[
            tuple[FlextInfraModelsCodegenConform.ProviderSpec, ...],
            m.Field(description="Ordered Git providers"),
        ]
        profiles: Annotated[
            tuple[FlextInfraModelsCodegenConform.ProfileSpec, ...],
            m.Field(description="Ordered Make profiles"),
        ]
        make: Annotated[
            FlextInfraModelsCodegenConform.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        managed_files: Annotated[
            tuple[FlextInfraModelsCodegenConform.ManagedFileSpec, ...],
            m.Field(description="Files owned by conform"),
        ]
        templates: Annotated[
            FlextInfraModelsCodegenConform.TemplatesSpec,
            m.Field(description="Universal template manifest"),
        ]
        repositories: Annotated[
            tuple[FlextInfraModelsCodegenConform.RepositoryRef, ...],
            m.Field(description="Ordered repository catalog"),
        ]
        workspaces: Annotated[
            tuple[FlextInfraModelsCodegenConform.WorkspaceCatalogRef, ...],
            m.Field(description="Pointers to local workspace topology manifests"),
        ]

    class UvEnvironmentPlan(_CodegenContract):
        """One deterministic uv environment operation plan."""

        project_root: Annotated[Path, m.Field(description="Selected project root")]
        runtime_root: Annotated[
            Path,
            m.Field(description="Project supplying the active .venv"),
        ]
        lock_path: Annotated[Path, m.Field(description="Required versioned uv.lock")]
        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact Mise/Python pin"),
        ]
        uv_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact required uv version"),
        ]
        groups: Annotated[
            t.StrSequence,
            m.Field(description="Ordered dependency groups synchronized by setup"),
        ]
        editable_paths: Annotated[
            t.SequenceOf[Path],
            m.Field(description="Local projects overlaid after locked sync"),
        ] = ()

    class CodegenConformRequest(_CodegenContract):
        """Validated public request for ``flext-infra codegen conform``."""

        root: Annotated[
            Path,
            m.Field(description="Repository or workspace root"),
        ]
        scope: Annotated[
            c.Infra.CodegenConformScope,
            m.Field(description="Repository selection scope"),
        ] = c.Infra.CodegenConformScope.SELF
        mode: Annotated[
            c.Infra.CodegenConformMode,
            m.Field(description="Read-only check or atomic apply"),
        ] = c.Infra.CodegenConformMode.CHECK

    class CodegenFilePlan(_CodegenContract):
        """Expected content and current state for one managed file."""

        path: Annotated[Path, m.Field(description="Absolute managed file path")]
        rendered: Annotated[str, m.Field(description="Fully rendered expected content")]
        expected_sha256: Annotated[
            t.NonEmptyStr,
            m.Field(description="SHA-256 of expected content"),
        ]
        current_sha256: Annotated[
            str,
            m.Field(description="SHA-256 of current content, empty when missing"),
        ] = ""
        changed: Annotated[bool, m.Field(description="Whether content differs")]
        blocked: Annotated[
            bool,
            m.Field(description="Whether unrecognized WIP blocks application"),
        ] = False
        reason: Annotated[str, m.Field(description="Blocking explanation")] = ""

    class CodegenPlan(_CodegenContract):
        """Fully validated plan produced before any managed-file write."""

        request: Annotated[
            FlextInfraModelsCodegenConform.CodegenConformRequest,
            m.Field(description="Validated public request"),
        ]
        repositories: Annotated[
            tuple[FlextInfraModelsCodegenConform.RepositoryRef, ...],
            m.Field(description="Selected repositories in deterministic order"),
        ]
        workspace: Annotated[
            FlextInfraModelsCodegenConform.WorkspaceSpec,
            m.Field(description="Workspace governing the selection"),
        ]
        make_spec: Annotated[
            FlextInfraModelsCodegenConform.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        uv_environments: Annotated[
            tuple[FlextInfraModelsCodegenConform.UvEnvironmentPlan, ...],
            m.Field(description="uv plans paired with selected repositories"),
        ]
        files: Annotated[
            tuple[FlextInfraModelsCodegenConform.CodegenFilePlan, ...],
            m.Field(description="All render results validated before application"),
        ]

    class CodegenResult(_CodegenContract):
        """Public conformance outcome for check and apply modes."""

        plan: Annotated[
            FlextInfraModelsCodegenConform.CodegenPlan,
            m.Field(description="Plan that governed the operation"),
        ]
        written_files: Annotated[
            t.SequenceOf[Path],
            m.Field(description="Files atomically replaced by apply"),
        ] = ()
        errors: Annotated[
            t.StrSequence,
            m.Field(description="Fail-closed validation or write errors"),
        ] = ()


__all__: list[str] = ["FlextInfraModelsCodegenConform"]
