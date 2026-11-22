# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/workspace
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsBase

if TYPE_CHECKING:
    from flext_cli import p

    from flext_infra import c, t
    from flext_infra._protocols import FlextInfraProtocolsCheck, FlextInfraProtocolsRope
    from flext_infra._protocols._config import (
        FlextInfraProtocolsConfigBeads,
        FlextInfraProtocolsConfigRepository,
        FlextInfraProtocolsConfigWorkspace,
    )
    from flext_infra._protocols._git import FlextInfraProtocolsGitIdentity


class FlextInfraProtocolsWorkspace:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenSourceAuthority(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def runtime(self) -> Path:
            """Authenticated native interpreter."""
            ...

        @property
        def repository_root(self) -> Path:
            """Structural member projected from the owning model.

            Repository being generated: only its sources are authenticated; other
            repositories' sources are read-only inputs.
            """
            ...

        @property
        def optimize(self) -> int:
            """Native compiler optimization."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileReceipt, ...]:
            """Pinned source/resource/distribution/runtime byte identities."""
            ...

        @property
        def bootstrap_sources(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Structural member projected from the owning model.

            Original buffered source candidates for atomic-reader bootstrap; only
            consumed candidates enter the sealed native reference.
            """
            ...

        @property
        def generator_trees(self) -> tuple[p.Cli.AtomicPhysicalTreeManifest, ...]:
            """Authenticated physical producer membership."""
            ...

        @property
        def generator_modules(self) -> tuple[tuple[str, Path], ...]:
            """Cold-elected physical producer namespaces."""
            ...

        @property
        def selections(
            self,
        ) -> tuple[FlextInfraProtocolsRope.SourceClassReference, ...]:
            """Portable entrypoint, receiver and explicitly wired port roots."""
            ...

        @property
        def generator_reference(
            self,
        ) -> FlextInfraProtocolsWorkspace.NativeImportReference | None:
            """Shared native epoch; cold authority carries none."""
            ...

    @runtime_checkable
    class NativeCodeEvidence(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def filename(self) -> str:
            """Actual relocated compiler filename."""
            ...

        @property
        def name(self) -> str:
            """Native code-unit name."""
            ...

        @property
        def firstlineno(self) -> int:
            """Actual compiler starting line."""
            ...

        @property
        def witness(self) -> bytes | None:
            """Complete native compiler witness, never deserialized."""
            ...

        @property
        def locations(self) -> tuple[t.JsonValue, ...] | None:
            """Flat root and nested compiler locations."""
            ...

        @property
        def nonportable_constants(self) -> tuple[tuple[tuple[int, ...], str], ...]:
            """Structural member projected from the owning model.

            Constant paths and native types requiring identity or containing NaN.
            """
            ...

    @runtime_checkable
    class NativeBindingEvidence(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def binding(self) -> str:
            """Root anchors, identity nodes and labeled native edges."""
            ...

        @property
        def kind(self) -> str:
            """Observed native descriptor category."""
            ...

        @property
        def supplier(self) -> str:
            """Actual defining module."""
            ...

        @property
        def name(self) -> str:
            """Advertised native name."""
            ...

        @property
        def qualname(self) -> str:
            """Advertised qualified name."""
            ...

        @property
        def code(self) -> str | None:
            """Structural member projected from the owning model.

            Validated JSON compiler witness or explicit nonportable-constant
            refusal.
            """
            ...

        @property
        def operands(self) -> tuple[tuple[str, str], ...]:
            """Static executable links and native declaration inputs."""
            ...

        @property
        def operational(self) -> tuple[tuple[str, str], ...]:
            """Observable native cache state kept separate from executable links."""
            ...

    @runtime_checkable
    class NativeObservationContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        paths: tuple[tuple[Path, Path], ...]
        origins: MutableMapping[str, Path]
        module_anchors: MutableMapping[str, t.Infra.NativeOperand]
        sources: t.Infra.MutableSetOf[tuple[str, str, str]]
        evidence: MutableSequence[FlextInfraProtocolsWorkspace.NativeBindingEvidence]
        evidence_index: MutableMapping[
            str, FlextInfraProtocolsWorkspace.NativeBindingEvidence
        ]
        generated_owners: MutableMapping[int, tuple[str, str, p.AttributeProbe | None]]
        references: MutableSequence[tuple[str, t.Infra.NativeOperand]]
        pending: MutableSequence[
            tuple[
                str,
                t.Infra.NativeOperand,
                str,
                str,
                Literal["execution", "storage_type"],
            ]
        ]
        expanded_classes: t.Infra.MutableSetOf[int]
        role: Literal["execution", "storage_type"]
        compiled: MutableMapping[Path, t.Infra.NativeClassDeclarations]
        lexical: bool
        binding_context: str
        incoming: str
        binding: str
        supplier: str
        owner_source: str
        visited: MutableMapping[int, tuple[t.Infra.NativeOperand, str]]
        edges: MutableMapping[str, str]
        absent_edges: t.Infra.MutableSetOf[str]

    @runtime_checkable
    class NativeFunctionObservationContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        value: tuple[t.Infra.NativeFunction]
        code: t.Infra.NativeCode
        supplier: str
        origin: Path
        generated: bool
        generated_operands: tuple[tuple[str, str], ...]
        nonlocals: MutableMapping[str, t.Infra.NativeOperand]
        global_bindings: MutableMapping[str, t.Infra.NativeOperand]
        operational_globals: frozenset[str]

    @runtime_checkable
    class NativeImportObservation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def runtime(self) -> Path:
            """Exact observed native interpreter."""
            ...

        @property
        def runtime_prefix(self) -> Path:
            """Physical interpreter environment."""
            ...

        @property
        def modules(self) -> tuple[FlextInfraProtocolsRope.SourceClassReference, ...]:
            """Selected modules and native lexical binding paths."""
            ...

        @property
        def sources(self) -> tuple[tuple[str, str, str], ...]:
            """Physical supplier and generated declaration origins."""
            ...

        @property
        def bindings(
            self,
        ) -> tuple[FlextInfraProtocolsWorkspace.NativeBindingEvidence, ...]:
            """Complete static native binding observations."""
            ...

        @property
        def executed_sources(self) -> tuple[p.Cli.AtomicFileReceipt, ...]:
            """Sources authenticated before compilation in the cold import."""
            ...

    @runtime_checkable
    class NativeImportReference(NativeImportObservation, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_authority(
            self,
        ) -> FlextInfraProtocolsWorkspace.CodegenSourceAuthority:
            """Cold authority pinned by the capture call."""
            ...

    @runtime_checkable
    class NativeImportRequest(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Declared workspace whose unchanged source view is consumed."""
            ...

        @property
        def runtime_root(self) -> Path:
            """Declared resolution owner of the elected physical runtime."""
            ...

        @property
        def modules(self) -> tuple[FlextInfraProtocolsRope.SourceClassReference, ...]:
            """Source-owned module/binding selections for this epoch."""
            ...

        @property
        def import_roots(self) -> tuple[Path, ...]:
            """Physical import roots carrying the elected producer sources."""
            ...

        @property
        def source_authority(
            self,
        ) -> FlextInfraProtocolsWorkspace.CodegenSourceAuthority:
            """Cold authority for reference consumption, not publication."""
            ...

        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Pinned source inputs checked before and after authentication."""
            ...

    @runtime_checkable
    class WorkspaceRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Repository root path."""
            ...

    @runtime_checkable
    class NativeGateRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def argv(self) -> tuple[str, ...]:
            """Native executable and arguments."""
            ...

        @property
        def budget_seconds(self) -> t.PositiveInt:
            """Native wall budget including termination grace."""
            ...

    @runtime_checkable
    class NativeSetupQualificationRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pending_report(self) -> Path:
            """Invocation-owned pending setup report."""
            ...

    @runtime_checkable
    class NativeSetupInputs(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def launcher(self) -> p.Cli.AtomicFileReceipt:
            """Locked static launcher receipt."""
            ...

        @property
        def extractor(self) -> p.Cli.AtomicFileReceipt:
            """Locked static SDK extractor receipt."""
            ...

        @property
        def extractor_arguments(self) -> tuple[str, ...]:
            """Original native SDK extraction arguments."""
            ...

        @property
        def compiler_archive(self) -> p.Cli.AtomicFileReceipt:
            """Original authenticated SDK archive."""
            ...

        @property
        def compiler_member(self) -> Path:
            """Compiler path inside the authenticated SDK archive."""
            ...

        @property
        def compiler_arguments(self) -> tuple[str, ...]:
            """Original arguments selecting the driver."""
            ...

        @property
        def archive(self) -> Path:
            """Static libseccomp archive."""
            ...

        @property
        def headers(self) -> tuple[Path, Path]:
            """Exact public libseccomp headers."""
            ...

        @property
        def sources(self) -> tuple[p.Cli.AtomicFileReceipt, p.Cli.AtomicFileReceipt]:
            """Installed policy and probe source receipts."""
            ...

        @property
        def declaration(self) -> tuple[p.Cli.AtomicFileReceipt, ...]:
            """Original toolchain declaration."""
            ...

        @property
        def installation(self) -> tuple[p.Cli.AtomicFileReceipt, ...]:
            """Exact locked installation inputs."""
            ...

        @property
        def abi_reference(self) -> p.Cli.AtomicFileReceipt:
            """Installed runtime interpreter receipt."""
            ...

        @property
        def profiles(self) -> tuple[Literal["read-only", "fixture"], ...]:
            """Original elected process profiles."""
            ...

    @runtime_checkable
    class WorkspaceTestsRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file(self) -> Path | None:
            """Repository-relative test file in this repository."""
            ...

        @property
        def scope(
            self,
        ) -> Literal[c.Infra.CodegenConformScope.ALL, c.Infra.CodegenConformScope.SELF]:
            """Test all governed repositories or only this repository."""
            ...

        @property
        def marker(self) -> str | None:
            """One declared harness gate marker narrowing the harness tests."""
            ...

    @runtime_checkable
    class FlextEditableRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def flext_root(self) -> Path | None:
            """Structural member projected from the owning model.

            Local FLEXT workspace whose provided distributions setup reinstalls
            editable; absent restores the locked installs.
            """
            ...

        @property
        def candidate_environment(self) -> Path | None:
            """Explicit prepared environment; absent selects the owned runtime."""
            ...

    @runtime_checkable
    class FlextEditableSelection(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def flext_root(self) -> Path:
            """Resolved FLEXT workspace root."""
            ...

        @property
        def distributions(self) -> Mapping[str, Path]:
            """Structural member projected from the owning model.

            Distribution name to the absolute source directory setup installed it
            editable from.
            """
            ...

    @runtime_checkable
    class WorkspaceRuntimeContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path:
            """Submitted Git worktree root."""
            ...

        @property
        def runtime_root(self) -> Path:
            """Physical runtime owner."""
            ...

        @property
        def resolution_root(self) -> Path:
            """Selected native UV project."""
            ...

        @property
        def pyproject_path(self) -> Path:
            """Selected resolution document."""
            ...

        @property
        def lock_path(self) -> Path:
            """Selected immutable UV lock."""
            ...

        @property
        def environment_path(self) -> Path:
            """Physical shared environment."""
            ...

        @property
        def standalone(self) -> bool:
            """Installed native resolution view; independent of later CI flags."""
            ...

        @property
        def installation_inputs(self) -> tuple[p.Cli.AtomicFileState, ...]:
            """Structural member projected from the owning model.

            Native lock and physical environment states captured after installation.
            """
            ...

        @property
        def native_install_exit_code(self) -> int | None:
            """Original frozen sync status; absent before installation."""
            ...

    @runtime_checkable
    class WorkspaceOperationReceipt(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_tool_qualifications(
            self,
        ) -> tuple[p.Cli.ProcessNativeToolEvidence, ...]:
            """Shared native qualification evidence."""
            ...

        @property
        def runtime_context(
            self,
        ) -> FlextInfraProtocolsWorkspace.WorkspaceRuntimeContext | None:
            """Authenticated installed runtime association."""
            ...

        @property
        def root(self) -> Path:
            """Repository actually attempted."""
            ...

        @property
        def executed(self) -> bool:
            """Original operation was invoked."""
            ...

        @property
        def outcome(self) -> c.Infra.ToolOutcome | None:
            """Native outcome, independent of report transport."""
            ...

        @property
        def native_exit_code(self) -> int | None:
            """Observed original shell exit status."""
            ...

        @property
        def stage(self) -> t.NonEmptyStr | None:
            """Original bootstrap stage reached."""
            ...

        @property
        def completed(self) -> bool | None:
            """Whether bootstrap reached its final stage."""
            ...

        @property
        def applicability(self) -> str:
            """Declared reason preventing execution."""
            ...

        @property
        def files(self) -> tuple[Path, ...]:
            """Paths returned by the original operation owner."""
            ...

        @property
        def issues(self) -> tuple[FlextInfraProtocolsCheck.Issue, ...]:
            """Native findings at their actual repository."""
            ...

    @runtime_checkable
    class WorkspaceOperationTarget(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Actual declared repository root."""
            ...

        @property
        def managed(self) -> bool | None:
            """Explicit Git management policy; absent when undeclared."""
            ...

    @runtime_checkable
    class WorkspaceOperationApplicability(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def applicable(self) -> bool:
            """Original owner may execute."""
            ...

        @property
        def reason(self) -> str:
            """Declared reason when inapplicable."""
            ...

    @runtime_checkable
    class WorkspaceOperationReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Invoking repository root."""
            ...

        @property
        def operation(self) -> t.NonEmptyStr:
            """Public operation name."""
            ...

        @property
        def scope(self) -> tuple[Path, ...]:
            """Roots discovered before the batch."""
            ...

        @property
        def receipts(
            self,
        ) -> tuple[FlextInfraProtocolsWorkspace.WorkspaceOperationReceipt, ...]:
            """Original receipts in discovered order."""
            ...

        @property
        def candidate_read_exit_code(self) -> int | None:
            """Original Git metadata read status."""
            ...

        @property
        def candidate_sha(self) -> str | None:
            """Observed Git candidate; absent when no candidate could be read."""
            ...

    @runtime_checkable
    class SubprojectLoadContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def integration_branch(self) -> str:
            """Successfully resolved workspace integration line."""
            ...

        @property
        def workspace_beads(
            self,
        ) -> FlextInfraProtocolsConfigBeads.BeadsProjectSpec | None:
            """Workspace Beads ledger spec; absent disables routing."""
            ...

        @property
        def allow_unprovisioned_members(self) -> bool:
            """Structural member projected from the owning model.

            Whether declared Python members may stay unprovisioned checkouts while
            CI omits them deliberately.
            """
            ...

        @property
        def superproject_gitlinks(self) -> t.StrTuple:
            """Structural member projected from the owning model.

            Paths the superproject index records as gitlinks; a member checkout at
            one of them is an attached submodule.
            """
            ...

        @property
        def declared_member(
            self,
        ) -> FlextInfraProtocolsConfigRepository.RepositoryRef | None:
            """Catalog-declared member reference for this entry."""
            ...

    @runtime_checkable
    class EnvironmentContractViolation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt:
            """Line number."""
            ...

        @property
        def message(self) -> str:
            """Violation description without the line prefix."""
            ...

        @property
        def token(self) -> str:
            """Offending token when the contract is token-based."""
            ...

    @runtime_checkable
    class WorkspaceProjectContext(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def cwd(self) -> Path:
            """Resolved submitted directory."""
            ...

        @property
        def identity(self) -> FlextInfraProtocolsGitIdentity.GitIdentityReport:
            """Observed Git identity of the containing checkout."""
            ...

        @property
        def workspace(self) -> FlextInfraProtocolsConfigWorkspace.WorkspaceSpec | None:
            """Governed workspace contract when declared."""
            ...

        @property
        def target(self) -> FlextInfraProtocolsConfigRepository.RepositoryConformTarget:
            """Effective governed project properties."""
            ...

        @property
        def governed(self) -> bool:
            """Whether repository-local FLEXT governance exists."""
            ...

        @property
        def runtime(self) -> FlextInfraProtocolsWorkspace.WorkspaceRuntimeContext:
            """Physical environment and native resolver ownership."""
            ...

    @runtime_checkable
    class DirectUrlDirectoryInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def editable(self) -> bool:
            """Distribution is installed as editable."""
            ...

    @runtime_checkable
    class DirectUrlVcsInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def vcs(self) -> str:
            """Native VCS kind."""
            ...

        @property
        def commit_id(self) -> str:
            """Installed full commit identity."""
            ...

    @runtime_checkable
    class PythonEnvironmentObservation(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def prefix(self) -> Path:
            """Observed native sys.prefix."""
            ...

        @property
        def metadata_paths(self) -> tuple[Path, ...]:
            """Native physical purelib and platlib install directories."""
            ...

        @property
        def import_paths(self) -> tuple[Path, ...]:
            """Native sys.path used for package resolution."""
            ...

        @property
        def package_directories(self) -> Mapping[str, tuple[Path, ...]]:
            """Native package search locations by declared package."""
            ...

        @property
        def package_distributions(self) -> Mapping[str, tuple[str, ...]]:
            """Native installed distribution owners by import package."""
            ...

    @runtime_checkable
    class DirectUrlReceipt(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dir_info(
            self,
        ) -> FlextInfraProtocolsWorkspace.DirectUrlDirectoryInfo | None:
            """Directory metadata of a local install."""
            ...

        @property
        def url(self) -> t.NonEmptyStr:
            """Required PEP 610 origin URL."""
            ...

        @property
        def vcs_info(self) -> FlextInfraProtocolsWorkspace.DirectUrlVcsInfo | None:
            """Installed immutable VCS identity."""
            ...

    @runtime_checkable
    class LockedPackageSource(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def git(self) -> str | None:
            """Locked VCS URL and SHA."""
            ...

        @property
        def registry(self) -> str | None:
            """Locked registry artifact."""
            ...

        @property
        def editable(self) -> str | None:
            """Local root source."""
            ...

        @property
        def directory(self) -> str | None:
            """Noneditable directory."""
            ...

        @property
        def virtual(self) -> str | None:
            """Virtual local project."""
            ...

        @property
        def url(self) -> str | None:
            """Locked archive URL."""
            ...

    @runtime_checkable
    class LockedDependency(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Required distribution."""
            ...

        @property
        def version(self) -> str | None:
            """Locked edge version when needed to disambiguate."""
            ...

        @property
        def source(self) -> FlextInfraProtocolsWorkspace.LockedPackageSource | None:
            """Locked edge source when needed to disambiguate."""
            ...

        @property
        def marker(self) -> str | None:
            """Environment condition for this edge."""
            ...

        @property
        def extra(self) -> tuple[str, ...]:
            """Requested extras; absent means none."""
            ...

    @runtime_checkable
    class LockedPackage(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Locked distribution name."""
            ...

        @property
        def version(self) -> t.NonEmptyStr:
            """Locked distribution version."""
            ...

        @property
        def source(self) -> FlextInfraProtocolsWorkspace.LockedPackageSource:
            """Locked source identity."""
            ...

        @property
        def dependencies(
            self,
        ) -> tuple[FlextInfraProtocolsWorkspace.LockedDependency, ...]:
            """Resolved package edges; absent for a leaf package."""
            ...

        @property
        def optional_dependencies(
            self,
        ) -> Mapping[str, tuple[FlextInfraProtocolsWorkspace.LockedDependency, ...]]:
            """Resolved edges by extra; absent when no extras exist."""
            ...

        @property
        def dev_dependencies(
            self,
        ) -> Mapping[str, tuple[FlextInfraProtocolsWorkspace.LockedDependency, ...]]:
            """Resolved edges by development group; absent means none."""
            ...

        @property
        def resolution_markers(self) -> tuple[str, ...]:
            """Package fork conditions; absent means no fork restriction."""
            ...

    @runtime_checkable
    class LockedEnvironment(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package(self) -> tuple[FlextInfraProtocolsWorkspace.LockedPackage, ...]:
            """Nonempty lock-owned package inventory."""
            ...

        @property
        def members(self) -> tuple[str, ...]:
            """Native workspace members; absent outside a workspace."""
            ...

    @runtime_checkable
    class EditableDirectUrl(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def url(self) -> t.NonEmptyStr:
            """Editable source URL."""
            ...

        @property
        def dir_info(self) -> FlextInfraProtocolsWorkspace.DirectUrlDirectoryInfo:
            """Editable directory metadata."""
            ...

    @runtime_checkable
    class FleetPullRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def number(self) -> int:
            """Provider pull-request number."""
            ...

        @property
        def head(self) -> str:
            """Branch the pull request proposes."""
            ...

        @property
        def title(self) -> str:
            """Pull-request title."""
            ...

        @property
        def url(self) -> str:
            """Pull-request web address."""
            ...

    @runtime_checkable
    class FleetRepoGaps(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Repository name."""
            ...

        @property
        def root(self) -> Path:
            """Repository checkout root."""
            ...

        @property
        def present(self) -> bool:
            """Whether the declared checkout exists on disk."""
            ...

        @property
        def dirty_paths(self) -> Sequence[str]:
            """Porcelain status paths of the checkout."""
            ...

        @property
        def open_pull_requests(
            self,
        ) -> tuple[FlextInfraProtocolsWorkspace.FleetPullRequest, ...]:
            """Open pull requests; empty when the query fails."""
            ...

        @property
        def unmerged_branches(self) -> int:
            """Local branches not merged into the integration line."""
            ...

        @property
        def lint_findings(self) -> t.NonNegativeInt | None:
            """Executed eligible lint findings; null is unknown/not executed."""
            ...

        @property
        def pyrefly_findings(self) -> t.NonNegativeInt | None:
            """Executed eligible Pyrefly findings; null is unknown/not executed."""
            ...

        @property
        def codemod_findings(self) -> int:
            """Mod scan findings from the checkout's receipt; 0 absent."""
            ...

        @property
        def agents_doc_present(self) -> bool:
            """Whether the checkout declares its AGENTS.md."""
            ...

        @property
        def skills_stamp_present(self) -> bool:
            """Whether the skills provisioning stamp exists."""
            ...

        @property
        def skills_stamp_distribution_version(self) -> str:
            """Stamp's distribution_version; empty when the stamp is absent."""
            ...

        @property
        def beads_config_present(self) -> bool:
            """Whether the Beads runtime identity exists."""
            ...

    @runtime_checkable
    class FleetGapsReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def schema_version(self) -> int:
            """Report schema version."""
            ...

        @property
        def workspace_root(self) -> Path:
            """Invoking workspace root."""
            ...

        @property
        def workspace_name(self) -> str:
            """Workspace identity name."""
            ...

        @property
        def repos(self) -> tuple[FlextInfraProtocolsWorkspace.FleetRepoGaps, ...]:
            """One row per declared member and external consumer."""
            ...

    @runtime_checkable
    class WorkspaceSyncRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dry_run(self) -> bool:
            """Preview only; do not execute sync operations."""
            ...

    @runtime_checkable
    class WorkspaceSyncRepoResult(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Repository name."""
            ...

        @property
        def root(self) -> Path:
            """Repository checkout root."""
            ...

        @property
        def present(self) -> bool:
            """Whether the checkout exists."""
            ...

        @property
        def fetched(self) -> bool:
            """Whether fetch was executed."""
            ...

        @property
        def pruned(self) -> bool:
            """Whether stale refs were pruned."""
            ...

        @property
        def submodule_synced(self) -> bool:
            """Whether submodules were synced."""
            ...

        @property
        def integration_branch(self) -> str | None:
            """Resolved integration branch."""
            ...

        @property
        def at_integration_tip(self) -> bool:
            """Whether at integration tip."""
            ...

        @property
        def ahead_by(self) -> int:
            """Commits ahead of integration."""
            ...

        @property
        def behind_by(self) -> int:
            """Commits behind integration."""
            ...

        @property
        def error(self) -> str | None:
            """Error message if any."""
            ...

    @runtime_checkable
    class WorkspaceSyncReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_root(self) -> Path:
            """Invoking workspace root."""
            ...

        @property
        def workspace_name(self) -> str:
            """Workspace identity name."""
            ...

        @property
        def integration_branch(self) -> str:
            """Resolved integration branch."""
            ...

        @property
        def repos(
            self,
        ) -> tuple[FlextInfraProtocolsWorkspace.WorkspaceSyncRepoResult, ...]:
            """One row per declared repository."""
            ...

        @property
        def all_at_tip(self) -> bool:
            """Whether all repos at integration tip."""
            ...

        @property
        def dry_run(self) -> bool:
            """Whether this was a dry run."""
            ...

    @runtime_checkable
    class WorkspaceCleanRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dry_run(self) -> bool:
            """Preview only; do not execute cleanup operations."""
            ...

        @property
        def confirm(self) -> bool:
            """Confirm execution (required when not dry-run)."""
            ...

    @runtime_checkable
    class WorkspaceCleanRepoResult(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str:
            """Repository name."""
            ...

        @property
        def root(self) -> Path:
            """Repository checkout root."""
            ...

        @property
        def present(self) -> bool:
            """Whether the checkout exists."""
            ...

        @property
        def worktrees_removed(self) -> int:
            """Obsolete worktrees removed."""
            ...

        @property
        def preserve_branches_removed(self) -> int:
            """Stale preserve branches removed."""
            ...

        @property
        def submodule_drift_fixed(self) -> bool:
            """Submodule SHA drift corrected."""
            ...

        @property
        def generated_projections_cleaned(self) -> int:
            """Stale generated files removed."""
            ...

        @property
        def testmon_db_cleaned(self) -> bool:
            """Stale testmon DB removed."""
            ...

        @property
        def venv_recreated(self) -> bool:
            """Stale .venv recreated."""
            ...

        @property
        def error(self) -> str | None:
            """Error message if any."""
            ...

    @runtime_checkable
    class WorkspaceCleanReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_root(self) -> Path:
            """Invoking workspace root."""
            ...

        @property
        def workspace_name(self) -> str:
            """Workspace identity name."""
            ...

        @property
        def repos(
            self,
        ) -> tuple[FlextInfraProtocolsWorkspace.WorkspaceCleanRepoResult, ...]:
            """One row per declared repository."""
            ...

        @property
        def dry_run(self) -> bool:
            """Whether this was a dry run."""
            ...

        @property
        def confirm(self) -> bool:
            """Whether execution was confirmed."""
            ...

    @runtime_checkable
    class WorkspacePrValidateRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tracking_id(self) -> str | None:
            """Bead ID to validate against."""
            ...

    @runtime_checkable
    class WorkspacePrValidateReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_root(self) -> Path:
            """Invoking workspace root."""
            ...

        @property
        def workspace_name(self) -> str:
            """Workspace identity name."""
            ...

        @property
        def tracking_id(self) -> str | None:
            """Bead ID validated."""
            ...

        @property
        def workspace_sync(self) -> bool:
            """Workspace sync passed."""
            ...

        @property
        def gate_evidence(self) -> bool:
            """All gate evidence recorded."""
            ...

        @property
        def rca_complete(self) -> bool:
            """RCA evidence complete."""
            ...

        @property
        def runtime_qa(self) -> bool:
            """Runtime QA passed."""
            ...

        @property
        def integration_path(self) -> bool:
            """Integration path verified."""
            ...

        @property
        def all_passed(self) -> bool:
            """All checks passed."""
            ...

        @property
        def errors(self) -> tuple[str, ...]:
            """Error messages if any."""
            ...

    @runtime_checkable
    class WorkspaceRcaCaptureRequest(WorkspaceRequest, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def tracking_id(self) -> str | None:
            """Bead ID to record RCA for."""
            ...

    @runtime_checkable
    class WorkspaceRcaCaptureReport(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def workspace_root(self) -> Path:
            """Invoking workspace root."""
            ...

        @property
        def workspace_name(self) -> str:
            """Workspace identity name."""
            ...

        @property
        def tracking_id(self) -> str | None:
            """Bead ID recorded."""
            ...

        @property
        def reproduction_recorded(self) -> bool:
            """Reproduction command recorded."""
            ...

        @property
        def root_cause_recorded(self) -> bool:
            """Root cause recorded."""
            ...

        @property
        def fix_verified(self) -> bool:
            """Fix verification recorded."""
            ...

        @property
        def gate_reexercised(self) -> bool:
            """Gate re-exercise recorded."""
            ...

        @property
        def all_recorded(self) -> bool:
            """All RCA evidence recorded."""
            ...

        @property
        def errors(self) -> tuple[str, ...]:
            """Error messages if any."""
            ...

    @runtime_checkable
    class ProjectInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Project name."""
            ...

        @property
        def path(self) -> Path:
            """Absolute or relative project path."""
            ...

        @property
        def stack(self) -> t.NonEmptyStr:
            """Primary technology stack."""
            ...

        @property
        def has_tests(self) -> bool:
            """Project has test suite."""
            ...

        @property
        def has_src(self) -> bool:
            """Project has source directory."""
            ...

        @property
        def project_class(self) -> t.NonEmptyStr:
            """Docs/governance project classification."""
            ...

        @property
        def package_name(self) -> str:
            """Primary Python package name."""
            ...

        @property
        def make_profile(self) -> c.Infra.MakeProfile:
            """Topology proven by this checkout's .gitmodules."""
            ...

        @property
        def declared_subproject(self) -> bool:
            """Whether the aggregate workspace declares this path."""
            ...

    @runtime_checkable
    class ProjectPyprojectState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path:
            """Project root path."""
            ...

        @property
        def pyproject_path(self) -> Path:
            """Resolved pyproject path."""
            ...

        @property
        def payload(self) -> t.JsonMapping:
            """Parsed pyproject payload."""
            ...

        @property
        def docs_meta(self) -> t.JsonMapping:
            """Parsed tool.flext.docs payload."""
            ...

        @property
        def project_name(self) -> str:
            """Declared project name."""
            ...

        @property
        def package_name(self) -> str:
            """Primary package name."""
            ...

        @property
        def dependency_names(self) -> Sequence[str]:
            """Declared dependency names."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsWorkspace",
]
