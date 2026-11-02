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

from flext_infra import c, t

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraProtocolsWorkspace:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class CodegenSourceAuthority(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def runtime(self) -> Path: ...
        @property
        def repository_root(self) -> Path: ...
        @property
        def optimize(self) -> int: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileReceipt, ...]: ...
        @property
        def bootstrap_sources(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def generator_trees(self) -> tuple[p.Cli.AtomicPhysicalTreeManifest, ...]: ...
        @property
        def generator_modules(self) -> tuple[tuple[str, Path], ...]: ...
        @property
        def selections(self) -> tuple[p.Infra.SourceClassReference, ...]: ...
        @property
        def generator_reference(self) -> p.Infra.NativeImportReference | None: ...

    @runtime_checkable
    class NativeCodeEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def filename(self) -> str: ...
        @property
        def name(self) -> str: ...
        @property
        def firstlineno(self) -> int: ...
        @property
        def witness(self) -> bytes | None: ...
        @property
        def locations(self) -> tuple[t.JsonValue, ...] | None: ...
        @property
        def nonportable_constants(self) -> tuple[tuple[tuple[int, ...], str], ...]: ...

    @runtime_checkable
    class NativeBindingEvidence(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def binding(self) -> str: ...
        @property
        def kind(self) -> str: ...
        @property
        def supplier(self) -> str: ...
        @property
        def name(self) -> str: ...
        @property
        def qualname(self) -> str: ...
        @property
        def code(self) -> str | None: ...
        @property
        def operands(self) -> tuple[tuple[str, str], ...]: ...
        @property
        def operational(self) -> tuple[tuple[str, str], ...]: ...

    @runtime_checkable
    class NativeObservationContext(Protocol):
        """Structural data contract projected from the owning model."""

        paths: tuple[tuple[Path, Path], ...]
        origins: MutableMapping[str, Path]
        module_anchors: MutableMapping[str, t.Infra.NativeOperand]
        sources: t.Infra.MutableSetOf[tuple[str, str, str]]
        evidence: MutableSequence[p.Infra.NativeBindingEvidence]
        evidence_index: MutableMapping[str, p.Infra.NativeBindingEvidence]
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
    class NativeFunctionObservationContext(Protocol):
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
    class NativeImportObservation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def runtime(self) -> Path: ...
        @property
        def runtime_prefix(self) -> Path: ...
        @property
        def modules(self) -> tuple[p.Infra.SourceClassReference, ...]: ...
        @property
        def sources(self) -> tuple[tuple[str, str, str], ...]: ...
        @property
        def bindings(self) -> tuple[p.Infra.NativeBindingEvidence, ...]: ...
        @property
        def executed_sources(self) -> tuple[p.Cli.AtomicFileReceipt, ...]: ...

    @runtime_checkable
    class NativeImportReference(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def runtime(self) -> Path: ...
        @property
        def runtime_prefix(self) -> Path: ...
        @property
        def modules(self) -> tuple[p.Infra.SourceClassReference, ...]: ...
        @property
        def sources(self) -> tuple[tuple[str, str, str], ...]: ...
        @property
        def bindings(self) -> tuple[p.Infra.NativeBindingEvidence, ...]: ...
        @property
        def executed_sources(self) -> tuple[p.Cli.AtomicFileReceipt, ...]: ...
        @property
        def source_authority(self) -> p.Infra.CodegenSourceAuthority: ...

    @runtime_checkable
    class NativeImportRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def runtime_root(self) -> Path: ...
        @property
        def modules(self) -> tuple[p.Infra.SourceClassReference, ...]: ...
        @property
        def import_roots(self) -> tuple[Path, ...]: ...
        @property
        def source_authority(self) -> p.Infra.CodegenSourceAuthority: ...
        @property
        def inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...

    @runtime_checkable
    class WorkspaceRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...

    @runtime_checkable
    class WorkspaceTestsRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def scope(
            self,
        ) -> Literal[
            c.Infra.CodegenConformScope.ALL, c.Infra.CodegenConformScope.SELF
        ]: ...

    @runtime_checkable
    class FlextEditableRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def flext_root(self) -> Path | None: ...
        @property
        def candidate_environment(self) -> Path | None: ...

    @runtime_checkable
    class FlextEditableSelection(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def flext_root(self) -> Path: ...
        @property
        def distributions(self) -> Mapping[str, Path]: ...

    @runtime_checkable
    class WorkspaceRuntimeContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path: ...
        @property
        def runtime_root(self) -> Path: ...
        @property
        def resolution_root(self) -> Path: ...
        @property
        def pyproject_path(self) -> Path: ...
        @property
        def lock_path(self) -> Path: ...
        @property
        def environment_path(self) -> Path: ...
        @property
        def standalone(self) -> bool: ...
        @property
        def installation_inputs(self) -> tuple[p.Cli.AtomicFileState, ...]: ...
        @property
        def native_install_exit_code(self) -> int | None: ...

    @runtime_checkable
    class WorkspaceOperationReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def native_tool_qualifications(
            self,
        ) -> tuple[p.Cli.ProcessNativeToolEvidence, ...]: ...
        @property
        def runtime_context(self) -> p.Infra.WorkspaceRuntimeContext | None: ...
        @property
        def root(self) -> Path: ...
        @property
        def executed(self) -> bool: ...
        @property
        def outcome(self) -> c.Infra.ToolOutcome | None: ...
        @property
        def native_exit_code(self) -> int | None: ...
        @property
        def stage(self) -> t.NonEmptyStr | None: ...
        @property
        def completed(self) -> bool | None: ...
        @property
        def applicability(self) -> str: ...
        @property
        def files(self) -> tuple[Path, ...]: ...
        @property
        def issues(self) -> tuple[p.Infra.Issue, ...]: ...

    @runtime_checkable
    class WorkspaceOperationTarget(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path: ...
        @property
        def managed(self) -> bool | None: ...

    @runtime_checkable
    class WorkspaceOperationApplicability(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def applicable(self) -> bool: ...
        @property
        def reason(self) -> str: ...

    @runtime_checkable
    class WorkspaceOperationReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path: ...
        @property
        def operation(self) -> t.NonEmptyStr: ...
        @property
        def scope(self) -> tuple[Path, ...]: ...
        @property
        def receipts(self) -> tuple[p.Infra.WorkspaceOperationReceipt, ...]: ...
        @property
        def candidate_read_exit_code(self) -> int | None: ...
        @property
        def candidate_sha(self) -> str | None: ...

    @runtime_checkable
    class SubprojectLoadContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def integration_branch(self) -> str: ...
        @property
        def workspace_beads(self) -> p.Infra.BeadsProjectSpec | None: ...
        @property
        def allow_unprovisioned_members(self) -> bool: ...
        @property
        def declared_member(self) -> p.Infra.RepositoryRef | None: ...

    @runtime_checkable
    class EnvironmentContractViolation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt: ...
        @property
        def message(self) -> str: ...
        @property
        def token(self) -> str: ...

    @runtime_checkable
    class WorkspaceProjectContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def cwd(self) -> Path: ...
        @property
        def identity(self) -> p.Infra.GitIdentityReport | None: ...
        @property
        def workspace(self) -> p.Infra.WorkspaceSpec | None: ...
        @property
        def target(self) -> p.Infra.RepositoryConformTarget | None: ...
        @property
        def governed(self) -> bool: ...
        @property
        def runtime(self) -> p.Infra.WorkspaceRuntimeContext | None: ...

    @runtime_checkable
    class DirectUrlDirectoryInfo(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def editable(self) -> bool: ...

    @runtime_checkable
    class DirectUrlVcsInfo(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def vcs(self) -> str: ...
        @property
        def commit_id(self) -> str: ...

    @runtime_checkable
    class PythonEnvironmentObservation(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def prefix(self) -> Path: ...
        @property
        def metadata_paths(self) -> tuple[Path, ...]: ...
        @property
        def import_paths(self) -> tuple[Path, ...]: ...
        @property
        def package_directories(self) -> Mapping[str, tuple[Path, ...]]: ...
        @property
        def package_distributions(self) -> Mapping[str, tuple[str, ...]]: ...

    @runtime_checkable
    class DirectUrlReceipt(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def dir_info(self) -> p.Infra.DirectUrlDirectoryInfo | None: ...
        @property
        def url(self) -> t.NonEmptyStr: ...
        @property
        def vcs_info(self) -> p.Infra.DirectUrlVcsInfo | None: ...

    @runtime_checkable
    class LockedPackageSource(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def git(self) -> str | None: ...
        @property
        def registry(self) -> str | None: ...
        @property
        def editable(self) -> str | None: ...
        @property
        def directory(self) -> str | None: ...
        @property
        def virtual(self) -> str | None: ...
        @property
        def url(self) -> str | None: ...

    @runtime_checkable
    class LockedDependency(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def version(self) -> str | None: ...
        @property
        def source(self) -> p.Infra.LockedPackageSource | None: ...
        @property
        def marker(self) -> str | None: ...
        @property
        def extra(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class LockedPackage(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def version(self) -> t.NonEmptyStr: ...
        @property
        def source(self) -> p.Infra.LockedPackageSource: ...
        @property
        def dependencies(self) -> tuple[p.Infra.LockedDependency, ...]: ...
        @property
        def optional_dependencies(
            self,
        ) -> Mapping[str, tuple[p.Infra.LockedDependency, ...]]: ...
        @property
        def dev_dependencies(
            self,
        ) -> Mapping[str, tuple[p.Infra.LockedDependency, ...]]: ...
        @property
        def resolution_markers(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class LockedEnvironment(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package(self) -> tuple[p.Infra.LockedPackage, ...]: ...
        @property
        def members(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class EditableDirectUrl(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def url(self) -> t.NonEmptyStr: ...
        @property
        def dir_info(self) -> p.Infra.DirectUrlDirectoryInfo: ...

    @runtime_checkable
    class FleetPullRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def number(self) -> int: ...
        @property
        def head(self) -> str: ...
        @property
        def title(self) -> str: ...
        @property
        def url(self) -> str: ...

    @runtime_checkable
    class FleetRepoGaps(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> str: ...
        @property
        def root(self) -> Path: ...
        @property
        def present(self) -> bool: ...
        @property
        def dirty_paths(self) -> Sequence[str]: ...
        @property
        def open_pull_requests(self) -> tuple[p.Infra.FleetPullRequest, ...]: ...
        @property
        def unmerged_branches(self) -> int: ...
        @property
        def lint_findings(self) -> t.NonNegativeInt | None: ...
        @property
        def pyrefly_findings(self) -> t.NonNegativeInt | None: ...
        @property
        def codemod_findings(self) -> int: ...
        @property
        def agents_doc_present(self) -> bool: ...
        @property
        def skills_stamp_present(self) -> bool: ...
        @property
        def skills_stamp_distribution_version(self) -> str: ...
        @property
        def beads_config_present(self) -> bool: ...

    @runtime_checkable
    class FleetGapsReport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def schema_version(self) -> int: ...
        @property
        def workspace_root(self) -> Path: ...
        @property
        def workspace_name(self) -> str: ...
        @property
        def repos(self) -> tuple[p.Infra.FleetRepoGaps, ...]: ...

    @runtime_checkable
    class ProjectInfo(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> Path: ...
        @property
        def stack(self) -> t.NonEmptyStr: ...
        @property
        def has_tests(self) -> bool: ...
        @property
        def has_src(self) -> bool: ...
        @property
        def project_class(self) -> t.NonEmptyStr: ...
        @property
        def package_name(self) -> str: ...
        @property
        def make_profile(self) -> c.Infra.MakeProfile: ...
        @property
        def declared_subproject(self) -> bool: ...

    @runtime_checkable
    class ProjectPyprojectState(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path: ...
        @property
        def pyproject_path(self) -> Path: ...
        @property
        def payload(self) -> t.JsonMapping: ...
        @property
        def docs_meta(self) -> t.JsonMapping: ...
        @property
        def project_name(self) -> str: ...
        @property
        def package_name(self) -> str: ...
        @property
        def dependency_names(self) -> Sequence[str]: ...


__all__: list[str] = [
    "FlextInfraProtocolsWorkspace",
]
