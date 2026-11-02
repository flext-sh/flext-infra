from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal

    from flext_infra import p, t


from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_infra._constants.config import FlextInfraConstantsConfig

# Copyright (c) 2026 FLEXT Team. All rights reserved.
# SPDX-License-Identifier: MIT
"""Structural contracts mirrored from ``_models._config.workspace``.

This bootstrap contract lets the protocol projector construct the workspace
before it can publish the remaining model-module projections.
"""


class FlextInfraProtocolsConfigWorkspace:
    """Runtime-checkable contracts declared by the workspace model module."""

    @runtime_checkable
    class GitSubmoduleDeclaration(Protocol):
        """One declared Git submodule section."""

        @property
        def path(self) -> Path:
            """Path relative to the superproject root."""
            ...

        @property
        def url(self) -> str:
            """Declared upstream URL."""
            ...

        @property
        def branch(self) -> str:
            """Declared branch, when present."""
            ...

        @property
        def managed(self) -> bool | None:
            """Native participation flag."""
            ...

        @property
        def layer(self) -> FlextInfraConstantsConfig.MemberArchitectureLayer | None:
            """Optional architecture layer."""
            ...

    @runtime_checkable
    class DependencyGroupInclude(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def include_group(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class DependencyGroupDeclarations(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependency_groups(
            self,
        ) -> Mapping[str, tuple[str | p.Infra.DependencyGroupInclude, ...]]: ...

    @runtime_checkable
    class DependencyManifestSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependency_groups(
            self,
        ) -> Mapping[str, tuple[str | p.Infra.DependencyGroupInclude, ...]]: ...
        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def dependencies(self) -> Sequence[str]: ...

    @runtime_checkable
    class DependencyEdgeSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependent(self) -> t.NonEmptyStr: ...
        @property
        def dependency(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class RefactorConfigSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_scan_dirs(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def file_extensions(self) -> tuple[t.NonEmptyStr, ...]: ...

    @runtime_checkable
    class DependencyCommitSourceSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr: ...
        @property
        def url(self) -> t.NonEmptyStr: ...
        @property
        def commit(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class CandidateDependenciesSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def candidate_dependencies(
            self,
        ) -> tuple[p.Infra.DependencyCommitSourceSpec, ...]: ...

    @runtime_checkable
    class RepositoryDeltaSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def candidate_dependencies(
            self,
        ) -> tuple[p.Infra.DependencyCommitSourceSpec, ...]: ...
        @property
        def docs_audit(self) -> p.Infra.DocsAuditOverridesSpec: ...
        @property
        def project(self) -> p.Infra.ProjectSpec | None: ...
        @property
        def integration(self) -> p.Infra.WorkspaceIntegrationSpec | None: ...
        @property
        def namespace_scan_dirs(self) -> Sequence[str]: ...
        @property
        def candidate_bootstrap_targets(
            self,
        ) -> tuple[p.Infra.CandidateBootstrapTargetSpec, ...]: ...
        @property
        def workspace_inventory_command(self) -> Sequence[str]: ...
        @property
        def refactor(self) -> p.Infra.RefactorConfigSpec | None: ...
        @property
        def beads_enabled(self) -> bool: ...
        @property
        def gascity_enabled(self) -> bool: ...
        @property
        def ci_enabled(self) -> bool: ...
        @property
        def ci_matrix_auto_run(self) -> bool: ...
        @property
        def codegen(self) -> FlextInfraConstantsConfig.CodegenKind: ...
        @property
        def kind(self) -> FlextInfraConstantsConfig.ProjectKind | None: ...
        @property
        def state(self) -> FlextInfraConstantsConfig.RepositoryState: ...
        @property
        def read_only(self) -> bool: ...
        @property
        def publishes_release(self) -> bool: ...
        @property
        def uv_link_mode(
            self,
        ) -> Literal["clone", "copy", "hardlink", "symlink"] | None: ...
        @property
        def duplication_trees(self) -> tuple[t.NonEmptyStr, ...]: ...
        @property
        def examples_module(self) -> t.NonEmptyStr | None: ...
        @property
        def extra_verbs(self) -> tuple[p.Infra.MakeVerbSpec, ...]: ...
        @property
        def script_dispatch(self) -> p.Infra.ScriptDispatchSpec | None: ...

    @runtime_checkable
    class CandidateBootstrapTargetSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def what(self) -> FlextInfraConstantsConfig.CodegenConformSurface: ...

    @runtime_checkable
    class DependencyGroupEntries(Protocol):
        """Structural data contract projected from the owning model."""

        root: tuple[str | DependencyGroupInclude, ...]

    @runtime_checkable
    class WorkspaceBeadsServerSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def backend(self) -> Literal["dolt"]: ...
        @property
        def mode(self) -> Literal["server"]: ...
        @property
        def shared_server(self) -> Literal[False]: ...
        @property
        def host(self) -> t.NonEmptyStr: ...
        @property
        def port(self) -> int: ...
        @property
        def user(self) -> t.NonEmptyStr: ...
        @property
        def auto_commit(self) -> Literal["off", "on", "batch"]: ...

    @runtime_checkable
    class RepositoryPolicyOverlaySpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr: ...
        @property
        def beads_enabled(self) -> bool: ...
        @property
        def ci_enabled(self) -> bool: ...
        @property
        def ci_matrix_auto_run(self) -> bool: ...
        @property
        def gascity_enabled(self) -> bool: ...

    @runtime_checkable
    class WorkspaceExclusionSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def reason(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class WorkspaceManifestSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def candidate_dependencies(
            self,
        ) -> tuple[p.Infra.DependencyCommitSourceSpec, ...]: ...
        @property
        def version(self) -> int: ...
        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def docs_audit(self) -> p.Infra.DocsAuditOverridesSpec: ...
        @property
        def namespace_scan_dirs(self) -> Sequence[str]: ...
        @property
        def ledger_id(self) -> t.NonEmptyStr | None: ...
        @property
        def ledger_prefix(self) -> t.NonEmptyStr | None: ...
        @property
        def beads_server(self) -> p.Infra.WorkspaceBeadsServerSpec | None: ...
        @property
        def repository(self) -> p.Infra.RepositoryRef: ...
        @property
        def project(self) -> p.Infra.ProjectSpec | None: ...
        @property
        def members(self) -> tuple[p.Infra.RepositoryRef, ...]: ...
        @property
        def external_dependency_paths(self) -> tuple[Path, ...]: ...
        @property
        def content_only(self) -> tuple[Path, ...]: ...
        @property
        def exclusions(self) -> tuple[p.Infra.WorkspaceExclusionSpec, ...]: ...
        @property
        def integration(self) -> p.Infra.WorkspaceIntegrationSpec | None: ...
        @property
        def candidate_bootstrap_targets(
            self,
        ) -> tuple[p.Infra.CandidateBootstrapTargetSpec, ...]: ...
        @property
        def repository_policy_overlays(
            self,
        ) -> tuple[p.Infra.RepositoryPolicyOverlaySpec, ...]: ...
        @property
        def external_consumers(self) -> tuple[p.Infra.ExternalConsumerSpec, ...]: ...
        @property
        def refactor(self) -> p.Infra.RefactorConfigSpec | None: ...

    @runtime_checkable
    class CodegenBootstrapSource(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def url(self) -> t.NonEmptyStr: ...
        @property
        def ref(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class HostWorkspaceInventoryEntry(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_id(self) -> t.NonEmptyStr: ...
        @property
        def owner(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> Path: ...
        @property
        def checkout_id(self) -> t.NonEmptyStr: ...
        @property
        def governing_checkout_id(self) -> t.NonEmptyStr: ...
        @property
        def project_profile(
            self,
        ) -> FlextInfraConstantsConfig.ProjectKind | Literal["unclassified"]: ...
        @property
        def upstream_project_id(self) -> str | None: ...
        @property
        def effective_ref(self) -> str | None: ...

    @runtime_checkable
    class HostWorkspaceInventory(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def entries(self) -> tuple[p.Infra.HostWorkspaceInventoryEntry, ...]: ...

    @runtime_checkable
    class ExternalConsumerSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def root(self) -> Path: ...
        @property
        def integration_branch(self) -> t.NonEmptyStr | None: ...
        @property
        def fix_namespace(self) -> bool: ...
        @property
        def fix_accessors(self) -> bool: ...

    @runtime_checkable
    class WorkspaceSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def candidate_dependencies(
            self,
        ) -> tuple[p.Infra.DependencyCommitSourceSpec, ...]: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def docs_audit(self) -> p.Infra.DocsAuditOverridesSpec: ...
        @property
        def beads(self) -> p.Infra.BeadsProjectSpec | None: ...
        @property
        def gascity_enabled(self) -> bool: ...
        @property
        def repository(self) -> p.Infra.RepositoryRef: ...
        @property
        def project(self) -> p.Infra.ProjectSpec | None: ...
        @property
        def flext_source(self) -> p.Infra.CodegenBootstrapSource | None: ...
        @property
        def namespace_scan_dirs(self) -> Sequence[str]: ...
        @property
        def integration(self) -> p.Infra.WorkspaceIntegrationSpec | None: ...
        @property
        def candidate_bootstrap_targets(
            self,
        ) -> tuple[p.Infra.CandidateBootstrapTargetSpec, ...]: ...
        @property
        def subprojects(self) -> tuple[p.Infra.RepositoryRef, ...]: ...
        @property
        def pending_subprojects(
            self,
        ) -> tuple[p.Infra.GitSubmoduleDeclaration, ...]: ...
        @property
        def external_dependency_paths(self) -> tuple[Path, ...]: ...
        @property
        def external_consumers(self) -> tuple[p.Infra.ExternalConsumerSpec, ...]: ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsConfigWorkspace",)
