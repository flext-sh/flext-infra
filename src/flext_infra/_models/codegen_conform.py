"""Typed contracts for the unified project conformance pipeline.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Self

from pydantic import model_validator

from flext_cli import m
from flext_infra.constants import c
from flext_infra.typings import t


class FlextInfraModelsCodegenConform:
    """Pydantic contracts shared by codegen planning and application."""

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): these models replace the
    # former model-less workspace/make dictionaries. YAML is accepted only at
    # the flext-cli loading boundary and is immediately model-validated here.

    class ToolchainSpec(m.ContractModel):
        """Exact Python and uv versions shared by generated projects."""

        python_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="Exact Python version"),
        ]
        uv_version: Annotated[t.NonEmptyStr, m.Field(description="Exact uv version")]
        uv_required_version: Annotated[
            t.NonEmptyStr,
            m.Field(description="PEP 440 uv required-version expression"),
        ]

    class ProviderSpec(m.ContractModel):
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

    class ProfileSpec(m.ContractModel):
        """Execution semantics for one generated Make profile."""

        name: Annotated[
            c.Infra.MakeProfile,
            m.BeforeValidator(lambda value: c.Infra.MakeProfile(value)),
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

    class MakeVerbSpec(m.ContractModel):
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

    class CustomHandlerPolicy(m.ContractModel):
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

    class MakeSpec(m.ContractModel):
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
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Ordered canonical public verbs"),
        ]
        custom_handler_policy: Annotated[
            FlextInfraModelsCodegenConform.CustomHandlerPolicy,
            m.Field(description="Private custom target policy"),
        ]

        @model_validator(mode="after")
        def _validate_make_contract(self) -> Self:
            """Enforce the one canonical public surface without aliases."""
            names = tuple(verb.name for verb in self.verbs)
            if names != c.Infra.PUBLIC_MAKE_VERBS:
                msg = "public Make verbs must match the canonical ordered surface"
                raise ValueError(msg)
            if self.selector != "WHAT":
                msg = "WHAT is the only public Make selector"
                raise ValueError(msg)
            if self.apply_variable != "APPLY" or self.apply_value != "Y":
                msg = "APPLY=Y is the only write opt-in"
                raise ValueError(msg)
            return self

        @property
        def public_verbs(self) -> t.StrSequence:
            """Return the validated ordered public verb names."""
            return tuple(verb.name for verb in self.verbs)

    class ManagedFileSpec(m.ContractModel):
        """One versioned file owned by codegen."""

        path: Annotated[
            Path,
            m.BeforeValidator(lambda value: Path(value)),
            m.Field(description="Repository-relative file path"),
        ]
        owner: Annotated[t.NonEmptyStr, m.Field(description="Canonical owner")]
        overwrite: Annotated[
            bool,
            m.Field(description="Whether clean committed content may be replaced"),
        ]

    class TemplateEntrySpec(m.ContractModel):
        """One template-to-destination mapping shared by new and conform."""

        source: Annotated[
            Path,
            m.BeforeValidator(lambda value: Path(value)),
            m.Field(description="Template-root-relative source"),
        ]
        destination: Annotated[
            t.NonEmptyStr,
            m.Field(description="Tokenized repository-relative destination"),
        ]
        profiles: Annotated[
            tuple[c.Infra.MakeProfile, ...],
            m.BeforeValidator(
                lambda value: tuple(c.Infra.MakeProfile(item) for item in value),
            ),
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

    class TemplatesSpec(m.ContractModel):
        """Universal template root and its complete ordered manifest."""

        root: Annotated[
            Path,
            m.BeforeValidator(lambda value: Path(value)),
            m.Field(description="Package-relative template root"),
        ]
        entries: Annotated[
            tuple[FlextInfraModelsCodegenConform.TemplateEntrySpec, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Complete ordered template manifest"),
        ]

    class RepositoryRef(m.ContractModel):
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
            m.BeforeValidator(lambda value: Path(value)),
            m.Field(description="POSIX path relative to its workspace root"),
        ]
        role: Annotated[
            c.Infra.RepositoryRole,
            m.BeforeValidator(lambda value: c.Infra.RepositoryRole(value)),
            m.Field(description="Repository role in the declared topology"),
        ]
        state: Annotated[
            c.Infra.RepositoryState,
            m.BeforeValidator(lambda value: c.Infra.RepositoryState(value)),
            m.Field(description="Repository lifecycle state"),
        ] = c.Infra.RepositoryState.ACTIVE
        provider: Annotated[
            t.NonEmptyStr,
            m.Field(description="Provider key from the codegen configuration"),
        ]
        profile: Annotated[
            c.Infra.MakeProfile | None,
            m.BeforeValidator(
                lambda value: (
                    None if value is None else c.Infra.MakeProfile(value)
                ),
            ),
            m.Field(description="Makefile generation profile"),
        ] = None

        @m.field_validator("url")
        @classmethod
        def _validate_url(cls, value: str) -> str:
            """Reject non-GitHub and non-clone URLs at model validation."""
            if not value.endswith(c.Infra.GIT_DIR):
                msg = "repository URL must end in .git"
                raise ValueError(msg)
            if c.Infra.GITHUB_REPO_URL_RE.fullmatch(value) is None:
                msg = "repository URL must be a canonical GitHub clone URL"
                raise ValueError(msg)
            return value

        @m.field_validator("branch")
        @classmethod
        def _validate_branch(cls, value: str) -> str:
            """Reject empty or unsafe Git ref syntax."""
            if c.Infra.GIT_REF_RE.fullmatch(value) is None:
                msg = "repository branch is not a valid Git ref"
                raise ValueError(msg)
            return value

        @m.field_validator("path")
        @classmethod
        def _validate_relative_path(cls, value: Path) -> Path:
            """Keep repository paths inside the declarative workspace root."""
            if value.is_absolute() or ".." in value.parts:
                msg = "repository path must be relative and may not escape its root"
                raise ValueError(msg)
            return value

    class WorkspaceExclusionSpec(m.ContractModel):
        """One explicitly rejected workspace path and its reason."""

        path: Annotated[
            Path,
            m.BeforeValidator(lambda value: Path(value)),
            m.Field(description="Workspace-relative path"),
        ]
        reason: Annotated[t.NonEmptyStr, m.Field(description="Exclusion rationale")]

    class WorkspaceSpec(m.ContractModel):
        """Declared topology for exactly one orchestrated workspace."""

        version: Annotated[int, m.Field(ge=1, description="Manifest version")]
        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Root repository catalog key"),
        ]
        profile: Annotated[
            c.Infra.MakeProfile,
            m.BeforeValidator(lambda value: c.Infra.MakeProfile(value)),
            m.Field(description="Generated root or independent profile"),
        ]
        members: Annotated[
            t.StrSequence,
            m.Field(description="Ordered active member catalog keys"),
        ] = ()
        content_only: Annotated[
            t.StrSequence,
            m.Field(description="Ordered content-only catalog keys"),
        ] = ()
        exclusions: Annotated[
            tuple[FlextInfraModelsCodegenConform.WorkspaceExclusionSpec, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Ordered paths deliberately excluded from inventory"),
        ] = ()

        @model_validator(mode="after")
        def _validate_topology(self) -> Self:
            """Reject duplicate or overlapping member and exclusion paths."""
            members = tuple(self.members)
            content_only = tuple(self.content_only)
            exclusions = tuple(item.path.as_posix() for item in self.exclusions)
            if len(set(members)) != len(members):
                msg = "workspace members must be unique"
                raise ValueError(msg)
            if len(set(content_only)) != len(content_only):
                msg = "workspace content-only entries must be unique"
                raise ValueError(msg)
            if len(set(exclusions)) != len(exclusions):
                msg = "workspace exclusions must be unique"
                raise ValueError(msg)
            overlap = sorted(set(members).intersection(content_only))
            if overlap:
                msg = f"workspace entries cannot be active and content-only: {overlap}"
                raise ValueError(msg)
            return self

    class WorkspaceCatalogRef(m.ContractModel):
        """Global pointer to a local workspace topology manifest."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Workspace name")]
        repository: Annotated[
            t.NonEmptyStr,
            m.Field(description="Root repository catalog key"),
        ]
        manifest: Annotated[
            Path,
            m.BeforeValidator(lambda value: Path(value)),
            m.Field(description="Repository-relative manifest path"),
        ]

    class CodegenConfigSpec(m.ContractModel):
        """Fully modeled content of ``config/codegen.yaml``."""

        version: Annotated[int, m.Field(ge=1, description="Config schema version")]
        toolchain: Annotated[
            FlextInfraModelsCodegenConform.ToolchainSpec,
            m.Field(description="Exact generated toolchain"),
        ]
        providers: Annotated[
            tuple[FlextInfraModelsCodegenConform.ProviderSpec, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Ordered Git providers"),
        ]
        profiles: Annotated[
            tuple[FlextInfraModelsCodegenConform.ProfileSpec, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Ordered Make profiles"),
        ]
        make: Annotated[
            FlextInfraModelsCodegenConform.MakeSpec,
            m.Field(description="Canonical Make contract"),
        ]
        managed_files: Annotated[
            tuple[FlextInfraModelsCodegenConform.ManagedFileSpec, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Files owned by conform"),
        ]
        templates: Annotated[
            FlextInfraModelsCodegenConform.TemplatesSpec,
            m.Field(description="Universal template manifest"),
        ]
        repositories: Annotated[
            tuple[FlextInfraModelsCodegenConform.RepositoryRef, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Ordered repository catalog"),
        ]
        workspaces: Annotated[
            tuple[FlextInfraModelsCodegenConform.WorkspaceCatalogRef, ...],
            m.BeforeValidator(lambda value: tuple(value)),
            m.Field(description="Pointers to local workspace topology manifests"),
        ]

    class UvEnvironmentPlan(m.ContractModel):
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

    class CodegenConformRequest(m.ContractModel):
        """Validated public request for ``flext-infra codegen conform``."""

        root: Annotated[
            Path,
            m.BeforeValidator(
                lambda value: (
                    value if isinstance(value, Path) else Path(value)
                ).expanduser().resolve(),
            ),
            m.Field(description="Repository or workspace root"),
        ]
        scope: Annotated[
            c.Infra.CodegenConformScope,
            m.BeforeValidator(lambda value: c.Infra.CodegenConformScope(value)),
            m.Field(description="Repository selection scope"),
        ] = c.Infra.CodegenConformScope.SELF
        mode: Annotated[
            c.Infra.CodegenConformMode,
            m.BeforeValidator(lambda value: c.Infra.CodegenConformMode(value)),
            m.Field(description="Read-only check or atomic apply"),
        ] = c.Infra.CodegenConformMode.CHECK

    class CodegenFilePlan(m.ContractModel):
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

    class CodegenPlan(m.ContractModel):
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

        @property
        def ready(self) -> bool:
            """Return whether the complete plan can be safely applied."""
            return not any(file.blocked for file in self.files)

    class CodegenResult(m.ContractModel):
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

        @property
        def changed(self) -> bool:
            """Return whether any selected file differs from expected content."""
            return any(file.changed for file in self.plan.files)

        @property
        def idempotent(self) -> bool:
            """Return whether the operation observed the canonical fixed point."""
            return (not self.changed) and (not self.errors)


__all__: list[str] = ["FlextInfraModelsCodegenConform"]
