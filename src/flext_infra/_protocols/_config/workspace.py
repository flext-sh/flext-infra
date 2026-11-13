from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal

    from flext_cli import p

    from flext_infra import t
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigBeads,
        FlextInfraProtocolsConfigMake,
        FlextInfraProtocolsConfigRepository,
    )


from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._constants.config import FlextInfraConstantsConfig
from flext_infra._protocols._config.contract import FlextInfraProtocolsConfigContract

# Copyright (c) 2026 FLEXT Team. All rights reserved.
# SPDX-License-Identifier: MIT
"""Structural contracts mirrored from ``_models._config.workspace``.

This bootstrap contract lets the protocol projector construct the workspace
before it can publish the remaining model-module projections.
"""


class FlextInfraProtocolsConfigWorkspace:
    """Runtime-checkable contracts declared by the workspace model module."""

    @runtime_checkable
    class GitSubmoduleDeclaration(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Submodule path relative to the superproject root."""
            ...

        @property
        def url(self) -> str:
            """Declared URL; empty when undeclared."""
            ...

        @property
        def branch(self) -> str:
            """Declared branch; empty when undeclared."""
            ...

        @property
        def managed(self) -> bool | None:
            """Structural member projected from the owning model.

            Native Git boolean: absent inherits participation; true participates and
            false does not.
            """
            ...

        @property
        def layer(self) -> FlextInfraConstantsConfig.MemberArchitectureLayer | None:
            """Structural member projected from the owning model.

            Declared architecture layer (domain or platform); absent leaves the
            member outside the layered sets.
            """
            ...

    @runtime_checkable
    class DependencyGroupInclude(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def include_group(self) -> t.NonEmptyStr:
            """Referenced dependency group."""
            ...

    @runtime_checkable
    class DependencyGroupDeclarations(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependency_groups(
            self,
        ) -> Mapping[
            str,
            tuple[str | FlextInfraProtocolsConfigWorkspace.DependencyGroupInclude, ...],
        ]:
            """Ordered native group entries."""
            ...

    @runtime_checkable
    class DependencyManifestSpec(DependencyGroupDeclarations, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """PEP 621 distribution name."""
            ...

        @property
        def dependencies(self) -> Sequence[str]:
            """PEP 621 runtime requirements."""
            ...

    @runtime_checkable
    class DependencyEdgeSpec(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dependent(self) -> t.NonEmptyStr:
            """Member distribution declaring the requirement."""
            ...

        @property
        def dependency(self) -> t.NonEmptyStr:
            """Member distribution it requires."""
            ...

    @runtime_checkable
    class RefactorConfigSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def project_scan_dirs(self) -> tuple[t.NonEmptyStr, ...]:
            """Relative directories scanned for candidate files."""
            ...

        @property
        def file_extensions(self) -> tuple[t.NonEmptyStr, ...]:
            """Allowed file extensions (empty = all by pattern)."""
            ...

    @runtime_checkable
    class DependencyCommitSourceSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def distribution(self) -> t.NonEmptyStr:
            """Exact dependency distribution name."""
            ...

        @property
        def url(self) -> t.NonEmptyStr:
            """Canonical HTTPS Git repository URL."""
            ...

        @property
        def commit(self) -> t.NonEmptyStr:
            """Full immutable Git commit OID."""
            ...

    @runtime_checkable
    class CandidateDependenciesSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def candidate_dependencies(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.DependencyCommitSourceSpec, ...]:
            """Candidate-only exact dependency Git sources."""
            ...

    @runtime_checkable
    class RepositoryDeltaAnalysisSpec(CandidateDependenciesSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def docs_audit(
            self,
        ) -> FlextInfraProtocolsConfigContract.DocsAuditOverridesSpec:
            """Universal documentation-audit declarations."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsConfigRepository.ProjectSpec | None:
            """Explicit metadata for a new project scaffold."""
            ...

        @property
        def integration(
            self,
        ) -> FlextInfraProtocolsConfigRepository.WorkspaceIntegrationSpec | None:
            """Explicit repository integration contract."""
            ...

        @property
        def namespace_scan_dirs(self) -> Sequence[str]:
            """Own namespace analysis roots."""
            ...

        @property
        def candidate_bootstrap_targets(
            self,
        ) -> tuple[
            FlextInfraProtocolsConfigWorkspace.CandidateBootstrapTargetSpec, ...
        ]:
            """Declared candidate worktrees and recovery surfaces."""
            ...

        @property
        def workspace_inventory_command(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Own public host inventory argv; empty leaves host discovery unselected,
            with no external participant catalogue.
            """
            ...

        @property
        def refactor(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.RefactorConfigSpec | None:
            """Own refactor file-selection declaration."""
            ...

    @runtime_checkable
    class RepositoryDeltaSpec(RepositoryDeltaAnalysisSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def beads_enabled(self) -> bool:
            """Repository participates in the Beads contract."""
            ...

        @property
        def gascity_enabled(self) -> bool:
            """Repository consumes the Gas City runtime contract."""
            ...

        @property
        def ci_enabled(self) -> bool:
            """Repository projects its canonical CI surface."""
            ...

        @property
        def ci_matrix_auto_run(self) -> bool:
            """Repository enables automatic CI matrix execution."""
            ...

        @property
        def codegen(self) -> FlextInfraConstantsConfig.CodegenKind:
            """Own canonical generation policy."""
            ...

        @property
        def state(self) -> FlextInfraConstantsConfig.RepositoryState:
            """Own lifecycle participation policy."""
            ...

        @property
        def read_only(self) -> bool:
            """Repository rejects generated mutations."""
            ...

        @property
        def publishes_release(self) -> bool:
            """Repository declares the generated release protocol."""
            ...

        @property
        def uv_link_mode(
            self,
        ) -> Literal["clone", "copy", "hardlink", "symlink"] | None:
            """Own uv installation link-mode declaration."""
            ...

        @property
        def duplication_trees(self) -> tuple[t.NonEmptyStr, ...]:
            """Own additional duplication-analysis trees."""
            ...

        @property
        def deferred_distributions(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Own costly third-party distributions: a lazy export whose module imports
            one at module scope loads on first member use.
            """
            ...

        @property
        def examples_module(self) -> t.NonEmptyStr | None:
            """Own explicit examples module."""
            ...

        @property
        def extra_verbs(self) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbSpec, ...]:
            """Own additional public Make commands."""
            ...

        @property
        def domain_capabilities(self) -> tuple[t.NonEmptyStr, ...]:
            """Structural member projected from the owning model.

            Technology names this repository's domain owns as capabilities, exempt
            from the library-named facade member ban.
            """
            ...

        @property
        def script_dispatch(
            self,
        ) -> FlextInfraProtocolsConfigRepository.ScriptDispatchSpec | None:
            """Own script command routing contract."""
            ...

        @property
        def verb_groups(
            self,
        ) -> tuple[FlextInfraProtocolsConfigMake.MakeVerbGroupSpec, ...]:
            """Own ordered `make help` sections."""
            ...

    @runtime_checkable
    class CandidateBootstrapTargetSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Relative candidate worktree path."""
            ...

        @property
        def what(self) -> FlextInfraConstantsConfig.CodegenConformSurface:
            """Canonical generator surface for this target."""
            ...

    @runtime_checkable
    class DependencyGroupEntries(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(
            self,
        ) -> tuple[
            str | FlextInfraProtocolsConfigWorkspace.DependencyGroupInclude, ...
        ]:
            """Structural member projected from the owning model."""
            ...

    @runtime_checkable
    class WorkspaceBeadsServerSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def backend(self) -> Literal["dolt"]:
            """Workspace ledger storage engine."""
            ...

        @property
        def mode(self) -> Literal["server"]:
            """Workspace ledger connection mode."""
            ...

        @property
        def shared_server(self) -> Literal[False]:
            """Workspace ledger uses an external Dolt endpoint."""
            ...

        @property
        def host(self) -> t.NonEmptyStr:
            """Dolt server host."""
            ...

        @property
        def port(self) -> int:
            """Dolt server TCP port."""
            ...

        @property
        def user(self) -> t.NonEmptyStr:
            """Dolt server user."""
            ...

        @property
        def auto_commit(self) -> Literal["off", "on", "batch"]:
            """Dolt auto-commit policy."""
            ...

    @runtime_checkable
    class RepositoryPolicyOverlaySpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.NonEmptyStr:
            """Canonical project distribution."""
            ...

        @property
        def beads_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Whether the repository participates in Beads; an overlay that omits it
            means the same as no overlay (enabled).
            """
            ...

        @property
        def ci_enabled(self) -> bool:
            """Whether conform owns the CI surface."""
            ...

        @property
        def ci_matrix_auto_run(self) -> bool:
            """Whether the CI matrix runs automatically."""
            ...

        @property
        def gascity_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Whether the repository consumes the Gas City runtime contract (city-
            owned Dolt server, gc tool projection, inherited endpoint keys). False
            renders the standalone shape: repository-local Dolt server owned by
            Beads.
            """
            ...

    @runtime_checkable
    class WorkspaceExclusionSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Workspace-relative path."""
            ...

        @property
        def reason(self) -> t.NonEmptyStr:
            """Exclusion rationale."""
            ...

    @runtime_checkable
    class WorkspaceManifestSpec(CandidateDependenciesSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def version(self) -> int:
            """Workspace manifest schema version."""
            ...

        @property
        def name(self) -> t.NonEmptyStr:
            """Workspace name."""
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

            Repository-level production roots the namespace validator enforces; an
            empty declaration keeps every root in scope, and an explicit project-
            level declaration wins.
            """
            ...

        @property
        def ledger_id(self) -> t.NonEmptyStr | None:
            """Optional workspace ledger database identity."""
            ...

        @property
        def ledger_prefix(self) -> t.NonEmptyStr | None:
            """Optional workspace issue-prefix identity."""
            ...

        @property
        def beads_server(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.WorkspaceBeadsServerSpec | None:
            """Optional workspace-local Dolt connection."""
            ...

        @property
        def repository(self) -> FlextInfraProtocolsConfigRepository.RepositoryRef:
            """Root repository declaration."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsConfigRepository.ProjectSpec | None:
            """Optional project creation metadata."""
            ...

        @property
        def members(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.RepositoryRef, ...]:
            """Declared member repository contracts."""
            ...

        @property
        def external_dependency_paths(self) -> tuple[Path, ...]:
            """Declared external dependency paths."""
            ...

        @property
        def content_only(self) -> tuple[Path, ...]:
            """Content-only Gitlink paths."""
            ...

        @property
        def exclusions(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.WorkspaceExclusionSpec, ...]:
            """Explicit workspace exclusions."""
            ...

        @property
        def integration(
            self,
        ) -> FlextInfraProtocolsConfigRepository.WorkspaceIntegrationSpec | None:
            """Optional integration provider overlay."""
            ...

        @property
        def candidate_bootstrap_targets(
            self,
        ) -> tuple[
            FlextInfraProtocolsConfigWorkspace.CandidateBootstrapTargetSpec, ...
        ]:
            """Declared candidate worktrees conformed by Infra."""
            ...

        @property
        def repository_policy_overlays(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.RepositoryPolicyOverlaySpec, ...]:
            """Repository-local policy overlays."""
            ...

        @property
        def external_consumers(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.ExternalConsumerSpec, ...]:
            """Structural member projected from the owning model.

            Out-of-workspace repositories propagation adjusts as guests through
            their own make verbs.
            """
            ...

        @property
        def refactor(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.RefactorConfigSpec | None:
            """Refactor file-selection configuration."""
            ...

    @runtime_checkable
    class CodegenBootstrapSource(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def url(self) -> t.NonEmptyStr:
            """Infrastructure Git URL."""
            ...

        @property
        def ref(self) -> t.NonEmptyStr:
            """Infrastructure Git ref."""
            ...

    @runtime_checkable
    class HostWorkspaceInventoryEntry(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def project_id(self) -> t.NonEmptyStr:
            """Forge project identity."""
            ...

        @property
        def owner(self) -> t.NonEmptyStr:
            """Resolved forge owner."""
            ...

        @property
        def path(self) -> Path:
            """Physical checkout root."""
            ...

        @property
        def checkout_id(self) -> t.NonEmptyStr:
            """Checkout identity."""
            ...

        @property
        def governing_checkout_id(self) -> t.NonEmptyStr:
            """Project's governing checkout identity."""
            ...

        @property
        def project_profile(
            self,
        ) -> FlextInfraConstantsConfig.ProjectKind | Literal["unclassified"]:
            """Host's declared governance and architecture profile."""
            ...

        @property
        def upstream_project_id(self) -> str | None:
            """Declared fork upstream identity."""
            ...

        @property
        def effective_ref(self) -> str | None:
            """Host's resolved checkout reference."""
            ...

    @runtime_checkable
    class HostWorkspaceInventory(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def entries(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.HostWorkspaceInventoryEntry, ...]:
            """Canonical discovered checkout identities."""
            ...

    @runtime_checkable
    class ExternalConsumerSpec(
        FlextInfraProtocolsConfigContract.ConfigContract, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Consumer display name."""
            ...

        @property
        def root(self) -> Path:
            """Structural member projected from the owning model.

            Absolute checkout root of the consumer repository outside this
            workspace.
            """
            ...

        @property
        def integration_branch(self) -> t.NonEmptyStr | None:
            """Structural member projected from the owning model.

            Consumer integration branch; absent defers to the resolver's provider
            fallback.
            """
            ...

        @property
        def fix_namespace(self) -> bool:
            """Run the consumer's make fix-namespace verb."""
            ...

        @property
        def fix_accessors(self) -> bool:
            """Run the consumer's make fix-accessors verb."""
            ...

    @runtime_checkable
    class WorkspaceSpec(CandidateDependenciesSpec, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Original topology and declaration observations."""
            ...

        @property
        def name(self) -> t.NonEmptyStr:
            """Workspace name."""
            ...

        @property
        def docs_audit(
            self,
        ) -> FlextInfraProtocolsConfigContract.DocsAuditOverridesSpec:
            """Validated local documentation audit declarations."""
            ...

        @property
        def beads(self) -> FlextInfraProtocolsConfigBeads.BeadsProjectSpec | None:
            """Repository-local Beads identity when enabled."""
            ...

        @property
        def gascity_enabled(self) -> bool:
            """Structural member projected from the owning model.

            Gas City runtime-contract participation resolved from the matched
            repository policy overlay; True when the checkout declares no manifest
            or no overlay.
            """
            ...

        @property
        def repository(self) -> FlextInfraProtocolsConfigRepository.RepositoryRef:
            """Local repository Git contract."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsConfigRepository.ProjectSpec | None:
            """Metadata required only when materializing a new tree."""
            ...

        @property
        def flext_source(
            self,
        ) -> FlextInfraProtocolsConfigWorkspace.CodegenBootstrapSource | None:
            """Structural member projected from the owning model.

            FLEXT dependency source required before the first pyproject exists;
            generated dependencies own provenance afterwards.
            """
            ...

        @property
        def namespace_scan_dirs(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Repository-level production roots the namespace validator enforces; an
            empty declaration keeps every root in scope, and an explicit project-
            level declaration wins.
            """
            ...

        @property
        def integration(
            self,
        ) -> FlextInfraProtocolsConfigRepository.WorkspaceIntegrationSpec | None:
            """Structural member projected from the owning model.

            Declared integration provider and branch from the workspace manifest;
            the resolver consults it before any Git fact.
            """
            ...

        @property
        def candidate_bootstrap_targets(
            self,
        ) -> tuple[
            FlextInfraProtocolsConfigWorkspace.CandidateBootstrapTargetSpec, ...
        ]:
            """Declared candidate worktrees for bootstrap."""
            ...

        @property
        def subprojects(
            self,
        ) -> tuple[FlextInfraProtocolsConfigRepository.RepositoryRef, ...]:
            """Direct governed repositories from local .gitmodules."""
            ...

        @property
        def pending_subprojects(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.GitSubmoduleDeclaration, ...]:
            """Managed Git declarations awaiting checkout provisioning."""
            ...

        @property
        def external_dependency_paths(self) -> tuple[Path, ...]:
            """Observed external or fork Git submodule paths."""
            ...

        @property
        def external_consumers(
            self,
        ) -> tuple[FlextInfraProtocolsConfigWorkspace.ExternalConsumerSpec, ...]:
            """Structural member projected from the owning model.

            Out-of-workspace repositories propagation adjusts as guests through
            their own make verbs.
            """
            ...


__all__: tuple[str, ...] = ("FlextInfraProtocolsConfigWorkspace",)
