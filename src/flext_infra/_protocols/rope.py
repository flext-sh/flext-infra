from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import c
    from flext_infra._protocols import (
        FlextInfraProtocolsCensus,
        FlextInfraProtocolsWorkspace,
    )
    from flext_infra._protocols._codegen import (
        FlextInfraProtocolsCodegenFix,
        FlextInfraProtocolsCodegenLazyInit,
        FlextInfraProtocolsCodegenPipeline,
        FlextInfraProtocolsCodegenTransaction,
    )


from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import Literal, Protocol, Self, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra import t
from flext_infra._protocols.base import FlextInfraProtocolsBase

"""Application-level protocols for Rope-backed infra utilities.

Concrete Rope objects are typed in ``t.Infra.Rope*``. This module keeps only
FLEXT callback contracts that do not have a concrete Rope class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""


if TYPE_CHECKING:
    from types import TracebackType

    from flext_infra._protocols import (
        FlextInfraProtocolsCheck,
        FlextInfraProtocolsRopeRuntime,
        FlextInfraProtocolsWorkspaceSnapshot,
    )


@runtime_checkable
class FlextInfraProtocolsRope(Protocol):
    """Application contracts layered around the concrete Rope boundary."""

    @runtime_checkable
    class ModelEnvelopeChecker(Protocol):
        """Native diagnostics bound to the supplied complete source candidate."""

        def __call__(
            self, sources: Mapping[Path, str]
        ) -> Sequence[FlextInfraProtocolsCheck.Issue]:
            """Run the native checker without publishing the candidate."""
            ...

    @runtime_checkable
    class RopeWorkspaceSession(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Resolved repository root requested by the caller."""
            ...

        @property
        def rope_repository_root(self) -> Path:
            """Canonical root used to open the shared Rope project."""
            ...

        @property
        def workspace_index(
            self,
        ) -> FlextInfraProtocolsCodegenLazyInit.RopeWorkspaceIndex:
            """Materialized workspace index for the open session."""
            ...

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

    # NOTE (multi-agent, flext-wkii.17.24 / agent: codex): source discovery is a
    # Rope boundary and consumes the exact field-only runtime request model.
    @runtime_checkable
    class ClassInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt:
            """Line number."""
            ...

        @property
        def name(self) -> str:
            """Class name."""
            ...

        @property
        def bases(self) -> Sequence[str]:
            """Base class names."""
            ...

    @runtime_checkable
    class ModuleSemanticState(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def class_infos(self) -> tuple[FlextInfraProtocolsRope.ClassInfo, ...]:
            """Local classes discovered in the module."""
            ...

        @property
        def declared_imports(self) -> Mapping[str, str]:
            """Declared import targets by name."""
            ...

        @property
        def semantic_imports(self) -> Mapping[str, str]:
            """Resolved import targets by name."""
            ...

    @runtime_checkable
    class SourceScanRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_roots(self) -> tuple[Path, ...]:
            """Non-empty ordered project roots to scan."""
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
        def workspace_index(
            self,
        ) -> FlextInfraProtocolsCodegenLazyInit.RopeWorkspaceIndex: ...

        def refresh(
            self,
            *,
            preserve_indexes: bool = False,
            validate_project: bool = True,
        ) -> FlextInfraProtocolsRope.RopeWorkspaceSession: ...

        def reload(self) -> FlextInfraProtocolsRope.RopeWorkspaceSession: ...

        def __enter__(self) -> Self: ...

        def __exit__(
            self,
            _exc_type: type[BaseException] | None,
            _exc: BaseException | None,
            _tb: TracebackType | None,
        ) -> None: ...

        def close(self) -> None: ...

    @runtime_checkable
    class RopeModelProtocolRoutes(Protocol):
        """Model routes of one workspace session mapped to projected protocols."""

        @property
        def model_protocol_routes(self) -> Mapping[str, str]:
            """Map every model route of the session to its projected protocol."""
            ...

        @property
        def model_protocol_identities(self) -> Mapping[str, str]:
            """Canonical native identities from the same source projection."""
            ...

    @runtime_checkable
    class RopeWorkspaceDsl(RopeSessionLifecycleDsl, RopeModelProtocolRoutes, Protocol):
        """Public DSL contract for one shared Rope workspace session."""

        semantic_rename_planner: (
            FlextInfraProtocolsBase.NativeSemanticRenamePlanner
        ) | None
        model_envelope_checker: FlextInfraProtocolsRope.ModelEnvelopeChecker | None

        def facade_projection(
            self,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ],
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
        ) -> FlextInfraProtocolsCodegenPipeline.CodegenRepositoryPlanOutcome:
            """Plan the generated family facades in this session."""
            ...

        def domain_owner_projection(
            self,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ],
            initializer: FlextInfraProtocolsBase.SourceInitializerPlanner,
            selection: tuple[Path, c.Infra.FacadeFamily | None] | None = None,
        ) -> FlextInfraProtocolsCodegenPipeline.CodegenRepositoryPlanOutcome: ...

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
            workspace_index: (FlextInfraProtocolsCodegenLazyInit.RopeWorkspaceIndex)
            | None = None,
            snapshot: FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot
            | None = None,
        ) -> Self: ...

        def bind_candidate(
            self,
            *,
            declared_files: tuple[
                FlextInfraProtocolsCodegenTransaction.CodegenFilePlan, ...
            ],
            additional_source_folders: t.StrTuple | None = None,
        ) -> None:
            """Advance the same session's source candidate without physical writes."""
            ...

        def resource(
            self,
            file_path: Path,
        ) -> FlextInfraProtocolsRopeRuntime.RopeFile | None: ...

        def module(
            self, file_path: Path
        ) -> FlextInfraProtocolsCodegenLazyInit.RopeModuleIndexEntry | None: ...

        def package(
            self,
            package_dir: Path,
        ) -> FlextInfraProtocolsCodegenLazyInit.RopePackageIndexEntry | None: ...

        def modules(
            self,
            *,
            project_names: Sequence[str] | None = None,
        ) -> Sequence[FlextInfraProtocolsCodegenLazyInit.RopeModuleIndexEntry]: ...

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
        ) -> Sequence[FlextInfraProtocolsCensus.Object]: ...

        def projects(self) -> Sequence[FlextInfraProtocolsWorkspace.ProjectInfo]: ...

        def layout(
            self, project_root: Path
        ) -> FlextInfraProtocolsCodegenLazyInit.RopeProjectLayout | None: ...

        def package_context(
            self,
            package_dir: Path,
        ) -> FlextInfraProtocolsCodegenLazyInit.LazyInitPackageContext: ...

        def policy(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
            current_pkg: str = "",
        ) -> FlextInfraProtocolsCodegenFix.NamespaceModulePolicy: ...

        def convention(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
        ) -> FlextInfraProtocolsRope.RopeModuleConvention: ...

        def semantic(
            self, file_path: Path
        ) -> FlextInfraProtocolsRope.ModuleSemanticState: ...

        def exports(
            self,
            file_path: Path,
            *,
            export_options: FlextInfraProtocolsRope.ExportOptions | None = None,
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
    class RopeRestructureRequest(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pattern(self) -> t.NonEmptyStr:
            """Native Rope match template."""
            ...

        @property
        def goal(self) -> str:
            """Native Rope replacement template; empty removes the match."""
            ...

        @property
        def arguments(self) -> Mapping[str, str | Sequence[str]]:
            """Native wildcard constraints and exact identity alternatives."""
            ...

        @property
        def resources(
            self,
        ) -> Sequence[FlextInfraProtocolsWorkspaceSnapshot.RopeResource]:
            """The complete resource inventory selected for this operation."""
            ...

        @property
        def imports(self) -> Sequence[str] | Mapping[str, str]:
            """Native imports, optionally keyed by reusable lexical bindings."""
            ...

        @property
        def match_filter(self) -> t.Infra.RopeMatchFilter | None:
            """Domain proof admitting each native source occurrence."""
            ...

    @runtime_checkable
    class RopeSourceImport(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def import_info(self) -> FlextInfraProtocolsRopeRuntime.RopeFromImport:
            """Native Rope from-import identity."""
            ...

        @property
        def start_line(self) -> int:
            """Original one-based declaration line."""
            ...

        @property
        def start_offset(self) -> int:
            """Original inclusive source character offset."""
            ...

        @property
        def end_offset(self) -> int:
            """Original exclusive source character offset."""
            ...

        @property
        def source(self) -> str:
            """Complete Rope logical import statement."""
            ...

        @property
        def type_checking_guarded(self) -> bool:
            """Import belongs to a TYPE_CHECKING suite."""
            ...

    @runtime_checkable
    class SubscriptRebind(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root_name(self) -> str:
            """Root name of the subscript's value expression."""
            ...

        @property
        def attribute(self) -> str | None:
            """Structural member projected from the owning model.

            Dotted attribute path between the root and the subscript when the
            subscript applies to an attribute expression (for example ``modules`` in
            ``sys.modules[...]``).
            """
            ...

        @property
        def is_module_table_mutation(self) -> bool:
            """Whether the rebind mutates an interpreter module table."""
            ...

    @runtime_checkable
    class ExportOptions(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def include_dunder(self) -> bool:
            """Whether dunder exports should be returned."""
            ...

        @property
        def allow_main(self) -> bool:
            """Whether a module-level main() may be exported."""
            ...

        @property
        def allow_assignments(self) -> bool:
            """Whether assignment-backed names may be exported."""
            ...

        @property
        def allow_functions(self) -> bool:
            """Whether module functions may be exported."""
            ...

        @property
        def require_explicit_all(self) -> bool:
            """Whether __all__ must exist for exports to be returned."""
            ...

    @runtime_checkable
    class SourceClassReference(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def target(self) -> str:
            """Dotted target the binding names."""
            ...

        @property
        def attributes(self) -> tuple[str, ...]:
            """Attribute path read off the binding target."""
            ...

        @property
        def qualified_base(self) -> str:
            """Fully qualified base spelling when resolved."""
            ...

    @runtime_checkable
    class RopeAttributeReadProof(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_path(self) -> Path:
            """Captured source file."""
            ...

        @property
        def source_sha256(self) -> str:
            """Digest of the complete captured source file."""
            ...

        @property
        def start_byte(self) -> int:
            """Inclusive source UTF-8 byte position."""
            ...

        @property
        def end_byte(self) -> int:
            """Exclusive source UTF-8 byte position."""
            ...

        @property
        def expression(self) -> str:
            """Native AST dump for the read."""
            ...

        @property
        def access(self) -> Literal["module", "class", "instance"]:
            """Native receiver access category."""
            ...

        @property
        def base(self) -> FlextInfraProtocolsRope.SourceClassReference:
            """Native module or class identity of the receiver."""
            ...

        @property
        def accessor(self) -> FlextInfraProtocolsRope.SourceClassReference:
            """Native __getattribute__ declaration identity."""
            ...

        @property
        def member(self) -> FlextInfraProtocolsRope.SourceClassReference:
            """Native owner and identity of the requested member."""
            ...

        @property
        def descriptor(self) -> FlextInfraProtocolsRope.SourceClassReference | None:
            """Builtin descriptor identity, or none for a plain value."""
            ...

        @property
        def project(self) -> FlextInfraProtocolsWorkspaceSnapshot.RopeProject:
            """Exact captured native project that resolved the identities."""
            ...

        @property
        def native_base(self) -> FlextInfraProtocolsRopeRuntime.RopePyName:
            """Native Rope binding of the attribute receiver type."""
            ...

        @property
        def native_accessor(self) -> FlextInfraProtocolsRopeRuntime.RopePyName:
            """Native Rope binding of the proven builtin getter."""
            ...

        @property
        def native_member(self) -> FlextInfraProtocolsRopeRuntime.RopePyName:
            """Native Rope binding selected by the captured C3 resolver."""
            ...

        @property
        def native_descriptor(self) -> FlextInfraProtocolsRopeRuntime.RopePyName | None:
            """Native Rope binding of the builtin descriptor, if present."""
            ...

    @runtime_checkable
    class SourceClassDefinition(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def identity(self) -> str:
            """Qualified identity of the declared class."""
            ...

        @property
        def bases(self) -> tuple[FlextInfraProtocolsRope.SourceClassReference, ...]:
            """Ordered base references of the declaration."""
            ...

        @property
        def members(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRope.SourceClassReference | None]:
            """Member name to shadowing reference mapping."""
            ...

    @runtime_checkable
    class SourceBindingCollectorSpec(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def module(self) -> t.NonEmptyStr:
            """Qualified module name under inventory."""
            ...

        @property
        def provider(self) -> FlextInfraProtocolsRopeRuntime.RopeSourceModule:
            """Native provider elected for the captured source."""
            ...

        @property
        def package(self) -> str:
            """Enclosing package name of the module."""
            ...

        @property
        def required_line(self) -> int | None:
            """Index only bindings visible at this line when set."""
            ...

        @property
        def allow_conditional(self) -> bool:
            """Whether conditional bindings may degrade to unknown."""
            ...

        @property
        def source_owned(self) -> bool:
            """Structural member projected from the owning model.

            Whether the scanned project's elected source roots own the module; only
            owned modules carry the explicit-binding law.
            """
            ...

        @property
        def definitions(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRope.SourceClassDefinition]:
            """Cross-module definition inventory the walk extends."""
            ...

        @property
        def lexical(
            self,
        ) -> Mapping[str, FlextInfraProtocolsRope.SourceClassReference | None]:
            """Module-scope bindings visible to every nested base."""
            ...

    @runtime_checkable
    class SourceBindingInventoryRequest(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.Infra.RopeProject:
            """Open Rope project scoped to the analysis roots."""
            ...

        @property
        def module(self) -> t.NonEmptyStr:
            """Qualified module name under inventory."""
            ...

        @property
        def path(self) -> Path:
            """Captured module path."""
            ...

        @property
        def source(self) -> str:
            """Captured module source text."""
            ...

        @property
        def required_line(self) -> int | None:
            """Index only bindings visible at this line when set."""
            ...

        @property
        def allow_conditional(self) -> bool:
            """Whether conditional bindings may degrade to unknown."""
            ...

    @runtime_checkable
    class ScopeDefinition(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt:
            """Line number."""
            ...

        @property
        def name(self) -> str:
            """Definition name."""
            ...

        @property
        def kind(self) -> c.Infra.RopeScopeKind:
            """Rope scope kind (Module/Function/Class/Unknown)."""
            ...

        @property
        def is_module_level(self) -> bool:
            """Whether the scope is a direct child of the module."""
            ...

    @runtime_checkable
    class LogicalStatement(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.PositiveInt:
            """Line number."""
            ...

        @property
        def indent(self) -> int:
            """Leading-whitespace column of the statement."""
            ...

        @property
        def end_line(self) -> int:
            """Final line in the Rope logical region."""
            ...

        @property
        def start_offset(self) -> int:
            """Source offset where the region starts."""
            ...

        @property
        def end_offset(self) -> int:
            """Source offset where the region ends."""
            ...

        @property
        def category(self) -> c.Infra.StatementCategory:
            """Lexical category of the leading token."""
            ...

        @property
        def enclosing_kind(self) -> c.Infra.RopeScopeKind:
            """Kind of the nearest enclosing def/class scope."""
            ...

        @property
        def enclosing_name(self) -> str:
            """Name of the nearest enclosing def/class, or empty."""
            ...

        @property
        def type_checking_guarded(self) -> bool:
            """Whether the statement is inside TYPE_CHECKING."""
            ...

        @property
        def text(self) -> str:
            """Rope-owned source slice for the statement."""
            ...

    @runtime_checkable
    class FamilyWrapperFlatten(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project(self) -> t.Infra.RopeProject:
            """Rope snapshot project resolving every consumer."""
            ...

        @property
        def owner_name(self) -> str:
            """Family owner class receiving promoted members."""
            ...

        @property
        def wrapper_name(self) -> str:
            """Declared name of the flattened namespace wrapper."""
            ...

        @property
        def wrapper(self) -> t.Infra.RopePyName:
            """Rope identity of the flattened namespace wrapper."""
            ...

        @property
        def names(self) -> Mapping[str, str]:
            """Wrapper member names mapped to promoted names."""
            ...

    @runtime_checkable
    class ConstantInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def class_path(self) -> str:
            """Nested class path."""
            ...

        @property
        def line(self) -> t.NonNegativeInt:
            """Line number."""
            ...

        @property
        def name(self) -> str:
            """Constant name."""
            ...

        @property
        def annotation(self) -> str:
            """Type annotation text."""
            ...

        @property
        def value(self) -> str:
            """Value representation."""
            ...

    @runtime_checkable
    class SymbolInfo(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def line(self) -> t.NonNegativeInt:
            """Line number."""
            ...

        @property
        def name(self) -> str:
            """Symbol name."""
            ...

        @property
        def kind(self) -> str:
            """Symbol kind: class, function, assignment."""
            ...

    @runtime_checkable
    class ConsolidatorScannedFile(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def resource(self) -> t.Infra.RopeResource:
            """Rope resource of the scanned module."""
            ...

        @property
        def source(self) -> str:
            """Source captured at scan; restored on failed gates."""
            ...

        @property
        def matches(
            self,
        ) -> Sequence[tuple[FlextInfraProtocolsRope.SymbolInfo, str, str]]:
            """Matched symbol, canonical reference, and raw value."""
            ...

    @runtime_checkable
    class RopeModuleConvention(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path:
            """Resolved Python module path."""
            ...

        @property
        def relative_path(self) -> Path:
            """Module path relative to its package directory."""
            ...

        @property
        def module_name(self) -> str:
            """Fully-qualified module name."""
            ...

        @property
        def package_name(self) -> str:
            """Importable package name for the module."""
            ...

        @property
        def package_dir(self) -> Path:
            """Resolved package directory containing the module."""
            ...

        @property
        def package_context(
            self,
        ) -> FlextInfraProtocolsCodegenLazyInit.LazyInitPackageContext:
            """Resolved lazy-init package context for the module."""
            ...

        @property
        def module_policy(self) -> FlextInfraProtocolsCodegenFix.NamespaceModulePolicy:
            """Canonical module policy derived for the module."""
            ...

        @property
        def project_layout(
            self,
        ) -> FlextInfraProtocolsCodegenLazyInit.RopeProjectLayout | None:
            """Resolved project layout, when the module belongs to one."""
            ...

    @runtime_checkable
    class FacadeCensus(FlextInfraProtocolsBase.FrozenArbitrary, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def snapshot(self) -> FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot:
            """The snapshot the census was read from."""
            ...

        @property
        def project(self) -> Path:
            """Absolute project root of the census."""
            ...

        @property
        def lineage(self) -> t.StrTuple:
            """Facade-publishing root packages of the lineage."""
            ...

        @property
        def references(self) -> Mapping[str, frozenset[str]]:
            """Foreign letter.member references by owner letter."""
            ...

        @property
        def exposed(self) -> Mapping[str, frozenset[str]]:
            """Own duplicate member names by declaring letter."""
            ...

        @property
        def missing(self) -> Mapping[str, frozenset[str]]:
            """Misplaced member names by declaring letter."""
            ...

        @property
        def claims(self) -> t.Infra.FacadeComponentClaims:
            """Component methods with their composing facade targets."""
            ...

    @runtime_checkable
    class RopeProjectElection(FlextCliProtocols.BaseModel, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_folders(self) -> t.StrTuple:
            """Ordered project-relative importable source folders."""
            ...

        @property
        def ignored_resources(self) -> t.StrTuple:
            """Source-scan ignore patterns elected by the caller."""
            ...

        @property
        def extension_modules(self) -> t.StrTuple:
            """Native extension modules elected by the original project."""
            ...

        @property
        def python_path_folders(self) -> t.StrTuple:
            """Ordered physical native import roots sharing the read owner."""
            ...

        @property
        def preferred_import_style(self) -> str:
            """Exact native import preference retained across source epochs."""
            ...

    @runtime_checkable
    class RopeInventoryRecordInput(FlextCliProtocols.BaseModel, Protocol):
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

        @property
        def convention(self) -> FlextInfraProtocolsRope.RopeModuleConvention:
            """Module convention metadata for tier/facade checks."""
            ...

        scope_chain: Sequence[str]
        class_chain: Sequence[str]
        child_scope: FlextInfraProtocolsRope.RopeScopeDsl | None
        rope_workspace: FlextInfraProtocolsRope.RopeWorkspaceDsl


__all__: list[str] = ["FlextInfraProtocolsRope"]
