# AUTO-GENERATED FILE - Source bootstrap legacy protocol holder.
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import c, p


from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Literal, Protocol, Self, runtime_checkable

"""Application-level protocols for Rope-backed infra utilities.

Concrete Rope objects are typed in ``t.Infra.Rope*``. This module keeps only
FLEXT callback contracts that do not have a concrete Rope class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""


if TYPE_CHECKING:
    from types import TracebackType

    from flext_core import t

    from flext_infra._protocols import (
        FlextInfraProtocolsBase,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsWorkspaceSnapshot,
    )


@runtime_checkable
class FlextInfraProtocolsRope(Protocol):
    """Application contracts layered around the concrete Rope boundary."""

    @runtime_checkable
    class RopeWorkspaceSession(Protocol):
        """Materialized state exposed by one Rope workspace session."""

        @property
        def repository_root(self) -> Path:
            """Resolved repository root requested by the caller."""
            ...

        @property
        def rope_repository_root(self) -> Path:
            """Canonical root used for the shared Rope project."""
            ...

        @property
        def workspace_index(self) -> p.Infra.RopeWorkspaceIndex:
            """Materialized index for the open session."""
            ...

    @runtime_checkable
    class SourceRewrite(Protocol):
        """Read-only source span and replacement consumed by native refactoring."""

        @property
        def start(self) -> int: ...

        @property
        def end(self) -> int: ...

        @property
        def text(self) -> str: ...

    @runtime_checkable
    class RopeContractCapturePolicy(Protocol):
        """Read-only capture and replacement constraints for a native rule."""

        @property
        def id(self) -> str: ...

        @property
        def phase(self) -> c.Infra.SemanticCutoverPhase: ...

        @property
        def annotation_only(self) -> bool: ...

        @property
        def pattern(self) -> str: ...

        @property
        def goal(self) -> str: ...

        @property
        def arguments(self) -> Mapping[str, str | Sequence[str]]: ...

        @property
        def imports(self) -> Mapping[str, str]: ...

        @property
        def bindings(self) -> Mapping[str, str]: ...

        @property
        def model_bases(self) -> Sequence[str]: ...

        @property
        def unshadowed_builtins(self) -> Sequence[str]: ...

        @property
        def repeats(self) -> str | None: ...

        @property
        def readonly_contract(self) -> str | None: ...

        @property
        def deferred_contract(self) -> str | None: ...

        @property
        def readonly_origins(self) -> Sequence[str]: ...

        @property
        def drops(self) -> Sequence[str]: ...

    @runtime_checkable
    class RopeContractRule(RopeContractCapturePolicy, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def operation(self) -> c.Infra.RopeContractOperation: ...

        @property
        def source_revision(self) -> str | None: ...

        @property
        def scope(self) -> p.Infra.RopeContractScope | None: ...

        @property
        def annotation_member_source(self) -> str | None: ...

        @property
        def call_target(self) -> str | None: ...

        @property
        def explicit_arguments(self) -> bool: ...

        @property
        def required_field(self) -> bool: ...

        @property
        def defaulted_field(self) -> bool: ...

        @property
        def private_attribute(self) -> bool: ...

        @property
        def value_default(self) -> str | None: ...

        @property
        def factory_default(self) -> str | None: ...

        @property
        def missing_keywords(self) -> Sequence[str]: ...

        @property
        def reorders_annotation(self) -> bool: ...

        @property
        def families(self) -> Sequence[str]: ...

        @property
        def scope_kinds(self) -> Sequence[c.Infra.RopeScopeKind]: ...

        @property
        def implementation_owner(self) -> tuple[str, str] | None: ...

        @property
        def receiver_methods(self) -> Sequence[str]: ...

        @property
        def ownership_transfer(self) -> tuple[str, str] | None: ...

        @property
        def owner_root(self) -> Path | None: ...

    @runtime_checkable
    class SemanticSourceState(Protocol):
        """Read-only original native file receipt carried to publication."""

        @property
        def path(self) -> Path: ...

        @property
        def content(self) -> bytes | None: ...

        @property
        def mode(self) -> int | None: ...

    @runtime_checkable
    class PrimitiveOwnerCondition(Protocol):
        """The qualified primitive operands used by native owner discovery."""

        @property
        def arg(self) -> Sequence[str]: ...

    @runtime_checkable
    class SemanticMigrationEdit(Protocol):
        """Immutable proposed source bytes passed between semantic phases."""

        @property
        def file_path(self) -> Path: ...

        @property
        def original_source(self) -> str | None: ...

        @property
        def updated_source(self) -> str: ...

        @property
        def changes(self) -> tuple[str, ...]: ...

        @property
        def retire_file(self) -> bool: ...

    # NOTE (multi-agent, flext-wkii.17.24 / agent: codex): source discovery is a
    # Rope boundary and consumes the exact field-only runtime request model.
    @runtime_checkable
    class ClassInfo(Protocol):
        """Class declaration facts consumed by semantic queries."""

        @property
        def name(self) -> str: ...

        @property
        def line(self) -> int: ...

        @property
        def bases(self) -> Sequence[str]: ...

    @runtime_checkable
    class ModuleSemanticState(Protocol):
        """Read-only semantic facts produced by the canonical module analyzer."""

        @property
        def class_infos(
            self,
        ) -> tuple[FlextInfraProtocolsRope.ClassInfo, ...]: ...

        @property
        def declared_imports(self) -> Mapping[str, str]: ...

        @property
        def semantic_imports(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class SourceScanRequest(Protocol):
        """Fields required by production-source discovery."""

        @property
        def project_roots(self) -> tuple[Path, ...]:
            """Non-empty ordered project roots selected at the boundary."""
            ...

    @runtime_checkable
    class ChangeTracker(Protocol):
        """Transformer contract for in-memory source rewrites with change tracking."""

        changes: MutableSequence[str]

        def apply_to_source(self, source: str) -> t.StrSequencePair: ...

    @runtime_checkable
    class RopeScopeDsl(Protocol):
        """Public scope contract for Rope semantic traversal."""

        def get_scopes(self) -> Sequence[FlextInfraProtocolsRope.RopeScopeDsl]: ...

        def get_names(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

        def get_defined_names(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

        def get_kind(self) -> str | None: ...

        def get_start(self) -> int: ...

        def get_end(self) -> int: ...

        @property
        def pyobject(self) -> FlextInfraProtocolsRopeRuntime.RopeSourceObject: ...

    @runtime_checkable
    class RopeSessionLifecycleDsl(Protocol):
        """Lifecycle contract of one shared Rope workspace session."""

        repository_root: Path

        @property
        def rope_repository_root(self) -> Path: ...

        @property
        def rope_project(self) -> FlextInfraProtocolsRopeRuntime.RopeProject: ...

        @property
        def workspace_index(self) -> p.Infra.RopeWorkspaceIndex: ...

        def refresh(
            self,
            *,
            preserve_indexes: bool = False,
            validate_project: bool = True,
        ) -> p.Infra.RopeWorkspaceSession: ...

        def reload(self) -> p.Infra.RopeWorkspaceSession: ...

        def __enter__(self) -> Self: ...

        def __exit__(
            self,
            _exc_type: type[BaseException] | None,
            _exc: BaseException | None,
            _tb: TracebackType | None,
        ) -> None: ...

        def close(self) -> None: ...

    @runtime_checkable
    class RopeWorkspaceDsl(RopeSessionLifecycleDsl, Protocol):
        """Public DSL contract for one shared Rope workspace session."""

        semantic_rename_planner: p.Infra.NativeSemanticRenamePlanner | None

        def facade_projection(
            self,
            *,
            declared_files: tuple[p.Infra.CodegenFilePlan, ...],
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
        ) -> p.Infra.CodegenRepositoryPlanOutcome:
            """Plan the generated family facades in this session."""
            ...

        def domain_owner_projection(
            self,
            *,
            declared_files: tuple[p.Infra.CodegenFilePlan, ...],
            initializer: FlextInfraProtocolsBase.SourceInitializerPlanner,
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None = None,
        ) -> p.Infra.CodegenRepositoryPlanOutcome: ...

        @property
        def snapshot(self) -> FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot:
            """The generic source epoch already owned by this session."""
            ...

        @classmethod
        def open_workspace(
            cls,
            repository_root: Path,
            *,
            rope_repository_root: Path | None = None,
            source_project: FlextInfraProtocolsRopeRuntime.RopeProject | None = None,
            workspace_index: p.Infra.RopeWorkspaceIndex | None = None,
            snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot
            | None = None,
        ) -> Self: ...

        def bind_candidate(
            self,
            *,
            declared_files: tuple[p.Infra.CodegenFilePlan, ...],
            additional_source_folders: t.StrTuple | None = None,
        ) -> None:
            """Advance the same session's source candidate without physical writes."""
            ...

        def resource(
            self,
            file_path: Path,
        ) -> FlextInfraProtocolsRopeRuntime.RopeFile | None: ...

        def module(self, file_path: Path) -> p.Infra.RopeModuleIndexEntry | None: ...

        def package(
            self,
            package_dir: Path,
        ) -> p.Infra.RopePackageIndexEntry | None: ...

        def modules(
            self,
            *,
            project_names: Sequence[str] | None = None,
        ) -> Sequence[p.Infra.RopeModuleIndexEntry]: ...

        def source(self, file_path: Path) -> str: ...

        def name_index(
            self,
        ) -> Mapping[str, tuple[tuple[Path, str, tuple[int, ...]], ...]]: ...

        def import_dependents(self, import_target: str) -> tuple[Path, ...]: ...

        def objects(
            self,
            file_path: Path,
            *,
            include_local_scopes: bool = True,
            include_references: bool = True,
        ) -> Sequence[p.Infra.Object]: ...

        def projects(self) -> Sequence[FlextInfraProtocolsBase.ProjectInfo]: ...

        def layout(self, project_root: Path) -> p.Infra.RopeProjectLayout | None: ...

        def package_context(
            self,
            package_dir: Path,
        ) -> p.Infra.LazyInitPackageContext: ...

        def policy(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
            current_pkg: str = "",
        ) -> p.Infra.NamespaceModulePolicy: ...

        def convention(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
        ) -> p.Infra.RopeModuleConvention: ...

        def semantic(
            self, file_path: Path
        ) -> FlextInfraProtocolsRope.ModuleSemanticState: ...

        def exports(
            self,
            file_path: Path,
            *,
            export_options: p.Infra.ExportOptions | None = None,
        ) -> Sequence[str]: ...

    @runtime_checkable
    class RopeAnalysisMethods(Protocol):
        """Class contract shared by the Rope analysis mixins."""

        @staticmethod
        def resolve_module_classes(
            rope_project: FlextInfraProtocolsRopeRuntime.RopeProject,
            resource: FlextInfraProtocolsRopeRuntime.RopeResource,
        ) -> Sequence[str]: ...

        @staticmethod
        def resolve_class_methods(
            rope_project: FlextInfraProtocolsRopeRuntime.RopeProject,
            resource: FlextInfraProtocolsRopeRuntime.RopeResource,
            class_name: str,
            *,
            include_private: bool = False,
        ) -> Mapping[str, str]: ...

        @staticmethod
        def project_root(file_path: Path) -> Path | None: ...

        @staticmethod
        def init_rope_project(
            repository_root: Path,
        ) -> FlextInfraProtocolsRopeRuntime.RopeProject: ...

        @staticmethod
        def init_rope_workspace(
            repository_root: Path,
        ) -> FlextInfraProtocolsRopeRuntime.RopeProject: ...

        @staticmethod
        def resolve_resource_from_path(
            rope_project: FlextInfraProtocolsRopeRuntime.RopeProject,
            file_path: Path,
        ) -> FlextInfraProtocolsRopeRuntime.RopeResource | None: ...

    @runtime_checkable
    class RopeRestructureRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pattern(self) -> t.NonEmptyStr: ...
        @property
        def goal(self) -> str: ...
        @property
        def arguments(self) -> Mapping[str, str | Sequence[str]]: ...
        @property
        def resources(self) -> Sequence[p.Infra.RopeResource]: ...
        @property
        def imports(self) -> Sequence[str] | Mapping[str, str]: ...
        @property
        def match_filter(self) -> t.Infra.RopeMatchFilter | None: ...

    @runtime_checkable
    class RopeSourceImport(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def import_info(self) -> p.Infra.RopeFromImport: ...
        @property
        def start_line(self) -> int: ...
        @property
        def start_offset(self) -> int: ...
        @property
        def end_offset(self) -> int: ...
        @property
        def source(self) -> str: ...
        @property
        def type_checking_guarded(self) -> bool: ...

    @runtime_checkable
    class SubscriptRebind(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root_name(self) -> str: ...
        @property
        def attribute(self) -> str | None: ...
        @property
        def is_module_table_mutation(self) -> bool: ...

    @runtime_checkable
    class ExportOptions(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def include_dunder(self) -> bool: ...
        @property
        def allow_main(self) -> bool: ...
        @property
        def allow_assignments(self) -> bool: ...
        @property
        def allow_functions(self) -> bool: ...
        @property
        def require_explicit_all(self) -> bool: ...

    @runtime_checkable
    class SourceClassReference(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target(self) -> str: ...
        @property
        def attributes(self) -> tuple[str, ...]: ...
        @property
        def qualified_base(self) -> str: ...

    @runtime_checkable
    class RopeAttributeReadProof(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_path(self) -> Path: ...
        @property
        def source_sha256(self) -> str: ...
        @property
        def start_byte(self) -> int: ...
        @property
        def end_byte(self) -> int: ...
        @property
        def expression(self) -> str: ...
        @property
        def access(self) -> Literal["module", "class", "instance"]: ...
        @property
        def base(self) -> p.Infra.SourceClassReference: ...
        @property
        def accessor(self) -> p.Infra.SourceClassReference: ...
        @property
        def member(self) -> p.Infra.SourceClassReference: ...
        @property
        def descriptor(self) -> p.Infra.SourceClassReference | None: ...
        @property
        def project(self) -> p.Infra.RopeProject: ...
        @property
        def native_base(self) -> p.Infra.RopePyName: ...
        @property
        def native_accessor(self) -> p.Infra.RopePyName: ...
        @property
        def native_member(self) -> p.Infra.RopePyName: ...
        @property
        def native_descriptor(self) -> p.Infra.RopePyName | None: ...

    @runtime_checkable
    class SourceClassDefinition(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def identity(self) -> str: ...
        @property
        def bases(self) -> tuple[p.Infra.SourceClassReference, ...]: ...
        @property
        def members(self) -> Mapping[str, p.Infra.SourceClassReference | None]: ...

    @runtime_checkable
    class SourceBindingCollectorSpec(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def module(self) -> t.NonEmptyStr: ...
        @property
        def provider(self) -> p.Infra.RopeSourceModule: ...
        @property
        def package(self) -> str: ...
        @property
        def required_line(self) -> int | None: ...
        @property
        def allow_conditional(self) -> bool: ...
        @property
        def source_owned(self) -> bool: ...
        @property
        def definitions(self) -> MutableMapping[str, p.Infra.SourceClassDefinition]: ...
        @property
        def lexical(
            self,
        ) -> MutableMapping[str, p.Infra.SourceClassReference | None]: ...

    @runtime_checkable
    class SourceBindingInventoryRequest(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.Infra.RopeProject: ...
        @property
        def module(self) -> t.NonEmptyStr: ...
        @property
        def path(self) -> Path: ...
        @property
        def source(self) -> str: ...
        @property
        def required_line(self) -> int | None: ...
        @property
        def allow_conditional(self) -> bool: ...

    @runtime_checkable
    class ScopeDefinition(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt: ...
        @property
        def name(self) -> str: ...
        @property
        def kind(self) -> c.Infra.RopeScopeKind: ...
        @property
        def is_module_level(self) -> bool: ...

    @runtime_checkable
    class LogicalStatement(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt: ...
        @property
        def indent(self) -> int: ...
        @property
        def end_line(self) -> int: ...
        @property
        def start_offset(self) -> int: ...
        @property
        def end_offset(self) -> int: ...
        @property
        def category(self) -> c.Infra.StatementCategory: ...
        @property
        def enclosing_kind(self) -> c.Infra.RopeScopeKind: ...
        @property
        def enclosing_name(self) -> str: ...
        @property
        def type_checking_guarded(self) -> bool: ...
        @property
        def text(self) -> str: ...

    @runtime_checkable
    class FamilyWrapperFlatten(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.Infra.RopeProject: ...
        @property
        def owner_name(self) -> str: ...
        @property
        def wrapper_name(self) -> str: ...
        @property
        def wrapper(self) -> t.Infra.RopePyName: ...
        @property
        def names(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class ConstantInfo(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def class_path(self) -> str: ...
        @property
        def line(self) -> t.NonNegativeInt: ...
        @property
        def name(self) -> str: ...
        @property
        def annotation(self) -> str: ...
        @property
        def value(self) -> str: ...

    @runtime_checkable
    class SymbolInfo(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.NonNegativeInt: ...
        @property
        def name(self) -> str: ...
        @property
        def kind(self) -> str: ...

    @runtime_checkable
    class ConsolidatorScannedFile(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def resource(self) -> t.Infra.RopeResource: ...
        @property
        def source(self) -> str: ...
        @property
        def matches(self) -> Sequence[tuple[p.Infra.SymbolInfo, str, str]]: ...

    @runtime_checkable
    class RopeModuleConvention(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path: ...
        @property
        def relative_path(self) -> Path: ...
        @property
        def module_name(self) -> str: ...
        @property
        def package_name(self) -> str: ...
        @property
        def package_dir(self) -> Path: ...
        @property
        def package_context(self) -> p.Infra.LazyInitPackageContext: ...
        @property
        def module_policy(self) -> p.Infra.NamespaceModulePolicy: ...
        @property
        def project_layout(self) -> p.Infra.RopeProjectLayout | None: ...

    @runtime_checkable
    class FacadeCensus(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def snapshot(self) -> p.Infra.WorkspaceSnapshot: ...
        @property
        def project(self) -> Path: ...
        @property
        def lineage(self) -> t.StrTuple: ...
        @property
        def references(self) -> Mapping[str, frozenset[str]]: ...
        @property
        def exposed(self) -> Mapping[str, frozenset[str]]: ...
        @property
        def missing(self) -> Mapping[str, frozenset[str]]: ...
        @property
        def claims(self) -> t.Infra.FacadeComponentClaims: ...

    @runtime_checkable
    class RopeProjectElection(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_folders(self) -> t.StrTuple: ...
        @property
        def ignored_resources(self) -> t.StrTuple: ...
        @property
        def extension_modules(self) -> t.StrTuple: ...
        @property
        def python_path_folders(self) -> t.StrTuple: ...

    @runtime_checkable
    class RopeInventoryRecordInput(Protocol):
        """Structural data contract projected from the owning model."""

        rope_project: t.Infra.RopeProject
        resource: t.Infra.RopeResource
        source: str
        parameter_lines: Mapping[tuple[int, str], int]
        constant_bindings: frozenset[tuple[int, str]]
        name: str
        pyname: t.Infra.RopePyName
        module_name: str
        project_name: str
        convention: p.Infra.RopeModuleConvention
        scope_chain: Sequence[str]
        class_chain: Sequence[str]
        child_scope: p.Infra.RopeScopeDsl | None
        rope_workspace: p.Infra.RopeWorkspaceDsl


__all__: list[str] = ["FlextInfraProtocolsRope"]
