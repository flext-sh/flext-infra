"""Application-level protocols for Rope-backed infra utilities.

Concrete Rope objects are typed in ``t.Infra.Rope*``. This module keeps only
FLEXT callback contracts that do not have a concrete Rope class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

from flext_cli import p as cli_p

if TYPE_CHECKING:
    # mro-wkii.17.26.2 (codex): every imported facade/type below is used only
    # by postponed protocol annotations; runtime loading closes p -> m/t.
    from pathlib import Path
    from types import TracebackType

    from flext_infra import c, p, t


@runtime_checkable
class FlextInfraProtocolsRope(Protocol):
    """Application contracts layered around the concrete Rope boundary."""

    # NOTE (multi-agent, mro-wkii.17.24 / agent: codex): source discovery is a
    # Rope boundary and consumes the exact field-only runtime request model.
    @runtime_checkable
    class SourceScanRequest(Protocol):
        """Fields required by production-source discovery."""

        @property
        def project_roots(self) -> tuple[Path, ...]:
            """Non-empty ordered project roots selected at the boundary."""
            ...

    # mro-dxrp.3.1 (rope-worker): mirror every live Rope model field structurally.
    @runtime_checkable
    class ClassInfo(cli_p.BaseModel, Protocol):
        """Semantic class information fields."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def name(self) -> str: ...

        @property
        def bases(self) -> t.StrSequence: ...

    @runtime_checkable
    class ConstantInfo(cli_p.BaseModel, Protocol):
        """Final-annotated constant definition fields."""

        @property
        def line(self) -> t.NonNegativeInt: ...

        @property
        def class_path(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def annotation(self) -> str: ...

        @property
        def value(self) -> str: ...

    @runtime_checkable
    class ExportOptions(cli_p.BaseModel, Protocol):
        """Rope module export discovery option fields."""

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
    class IgnoredRegion(cli_p.BaseModel, Protocol):
        """Rope-classified source region fields."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def start_offset(self) -> int: ...

        @property
        def end_offset(self) -> int: ...

        @property
        def text(self) -> t.NonEmptyStr: ...

        @property
        def is_comment(self) -> bool: ...

    @runtime_checkable
    class ImportFact(cli_p.BaseModel, Protocol):
        """Normalized Rope import binding fields."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def module(self) -> t.NonEmptyStr: ...

        @property
        def member(self) -> str: ...

        @property
        def local_name(self) -> t.NonEmptyStr: ...

        @property
        def is_from_import(self) -> bool: ...

    @runtime_checkable
    class LogicalStatement(cli_p.BaseModel, Protocol):
        """Rope logical statement fields."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def indent(self) -> int: ...

        @property
        def end_line(self) -> int: ...

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
    class ModuleSemanticState(cli_p.BaseModel, Protocol):
        """Unified Rope module semantic state fields."""

        @property
        def class_infos(self) -> tuple[p.Infra.ClassInfo, ...]: ...

        @property
        def declared_imports(self) -> t.StrMapping: ...

        @property
        def semantic_imports(self) -> t.StrMapping: ...

    @runtime_checkable
    class RopeInventoryRecordInput(cli_p.BaseModel, Protocol):
        """Rope inventory record input fields."""

        @property
        def rope_project(self) -> t.Infra.RopeProject: ...

        @property
        def resource(self) -> t.Infra.RopeResource: ...

        @property
        def source(self) -> str: ...

        @property
        def name(self) -> str: ...

        @property
        def pyname(self) -> t.Infra.RopePyName: ...

        @property
        def module_name(self) -> str: ...

        @property
        def project_name(self) -> str: ...

        @property
        def convention(self) -> p.Infra.RopeModuleConvention: ...

        @property
        def scope_chain(self) -> t.StrSequence: ...

        @property
        def class_chain(self) -> t.StrSequence: ...

        @property
        def child_scope(self) -> p.Infra.RopeScopeDsl | None: ...

        @property
        def rope_workspace(self) -> p.Infra.RopeWorkspaceDsl | None: ...

    @runtime_checkable
    class RopeModuleConvention(cli_p.BaseModel, Protocol):
        """Rope module convention fields."""

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
    class RopeModuleIndexEntry(cli_p.BaseModel, Protocol):
        """Rope module index entry fields."""

        @property
        def file_path(self) -> Path: ...

        @property
        def resource_path(self) -> str: ...

        @property
        def module_name(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def package_dir(self) -> Path: ...

        @property
        def project_root(self) -> Path | None: ...

        @property
        def is_package_init(self) -> bool: ...

    @runtime_checkable
    class RopePackageIndexEntry(cli_p.BaseModel, Protocol):
        """Rope package index entry fields."""

        @property
        def package_dir(self) -> Path: ...

        @property
        def init_path(self) -> Path: ...

        @property
        def package_name(self) -> str: ...

        @property
        def project_root(self) -> Path | None: ...

        @property
        def modules(self) -> tuple[p.Infra.RopeModuleIndexEntry, ...]: ...

        @property
        def direct_child_dirs(self) -> tuple[Path, ...]: ...

        @property
        def descendant_child_dirs(self) -> tuple[Path, ...]: ...

    @runtime_checkable
    class RopeProjectLayout(cli_p.BaseModel, Protocol):
        """Rope project layout fields."""

        @property
        def project_root(self) -> Path: ...

        @property
        def project_name(self) -> str: ...

        @property
        def package_name(self) -> str: ...

        @property
        def package_alias(self) -> str: ...

        @property
        def class_stem(self) -> str: ...

        @property
        def src_dir(self) -> Path: ...

        @property
        def package_dir(self) -> Path: ...

        @property
        def init_path(self) -> Path: ...

        @property
        def runtime_aliases(self) -> t.StrSequence: ...

    @runtime_checkable
    class RopeWorkspaceIndex(cli_p.BaseModel, Protocol):
        """Rope workspace index fields."""

        @property
        def workspace_root(self) -> Path: ...

        @property
        def package_dirs(self) -> tuple[Path, ...]: ...

        @property
        def packages_by_dir(
            self,
        ) -> t.MappingKV[str, p.Infra.RopePackageIndexEntry]: ...

        @property
        def modules_by_path(
            self,
        ) -> t.MappingKV[str, p.Infra.RopeModuleIndexEntry]: ...

        @property
        def package_dir_by_name(self) -> t.MappingKV[str, Path]: ...

        @property
        def project_package_by_root(self) -> t.StrMapping: ...

    @runtime_checkable
    class ScopeDefinition(cli_p.BaseModel, Protocol):
        """Rope semantic scope definition fields."""

        @property
        def line(self) -> t.PositiveInt: ...

        @property
        def name(self) -> str: ...

        @property
        def kind(self) -> c.Infra.RopeScopeKind: ...

        @property
        def is_module_level(self) -> bool: ...

    @runtime_checkable
    class SymbolInfo(cli_p.BaseModel, Protocol):
        """Rope top-level symbol information fields."""

        @property
        def line(self) -> t.NonNegativeInt: ...

        @property
        def name(self) -> str: ...

        @property
        def kind(self) -> str: ...

    @runtime_checkable
    class ChangeTracker(Protocol):
        """Transformer contract for in-memory source rewrites with change tracking."""

        changes: t.MutableSequenceOf[str]

        def apply_to_source(self, source: str) -> t.Infra.TransformResult: ...

    @runtime_checkable
    class RopeScopeDsl(Protocol):
        """Public scope contract for Rope semantic traversal."""

        def get_scopes(self) -> t.SequenceOf[FlextInfraProtocolsRope.RopeScopeDsl]: ...

        def get_names(self) -> t.MappingKV[str, t.Infra.RopePyName]: ...

        def get_defined_names(self) -> t.MappingKV[str, t.Infra.RopePyName]: ...

        def get_kind(self) -> str: ...

        def get_start(self) -> int: ...

        def get_end(self) -> int: ...

        @property
        def pyobject(self) -> t.Infra.RopePyObject: ...

    @runtime_checkable
    class RopeWorkspaceDsl(Protocol):
        """Public DSL contract for one shared Rope workspace session."""

        workspace_root: Path

        @property
        def rope_workspace_root(self) -> Path: ...

        @property
        def rope_project(self) -> t.Infra.RopeProject: ...

        @property
        def workspace_index(self) -> p.Infra.RopeWorkspaceIndex: ...

        def refresh(
            self, *, preserve_indexes: bool = False, validate_project: bool = True
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

        def resource(self, file_path: Path) -> t.Infra.RopeResource | None: ...

        def module(self, file_path: Path) -> p.Infra.RopeModuleIndexEntry | None: ...

        def package(
            self, package_dir: Path
        ) -> p.Infra.RopePackageIndexEntry | None: ...

        def modules(
            self, *, project_names: t.StrSequence | None = None
        ) -> t.SequenceOf[p.Infra.RopeModuleIndexEntry]: ...

        def source(self, file_path: Path) -> str: ...

        def surface(self, file_path: Path) -> str: ...

        def name_index(
            self,
        ) -> t.MappingKV[str, tuple[tuple[Path, str, tuple[int, ...]], ...]]: ...

        def registry_imports(self, name: str) -> tuple[tuple[Path, str], ...]: ...

        def objects(
            self,
            file_path: Path,
            *,
            include_local_scopes: bool = True,
            include_references: bool = True,
        ) -> t.SequenceOf[p.Infra.Census.Object]: ...

        def projects(self) -> t.SequenceOf[p.Infra.ProjectInfo]: ...

        def layout(self, project_root: Path) -> p.Infra.RopeProjectLayout | None: ...

        def package_context(
            self, package_dir: Path
        ) -> p.Infra.LazyInitPackageContext: ...

        def policy(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
            current_pkg: str = "",
        ) -> p.Infra.NamespaceModulePolicy: ...

        def convention(
            self, file_path: Path, *, rel_path: Path | None = None
        ) -> p.Infra.RopeModuleConvention: ...

        def semantic(self, file_path: Path) -> p.Infra.ModuleSemanticState: ...

        def exports(
            self,
            file_path: Path,
            *,
            export_options: p.Infra.ExportOptions | None = None,
        ) -> t.StrSequence: ...

    # mro-qc84 (fix-forward): protocol-of-model for the Rope workspace session
    # snapshot (m.Infra.RopeWorkspaceSession). Consumed at runtime by the
    # workspace service base class ``s[p.Infra.RopeWorkspaceSession]`` and by the
    # DSL refresh/reload return contracts above.
    @runtime_checkable
    class RopeWorkspaceSession(Protocol):
        """Public structural view of one materialized Rope workspace session."""

        @property
        def workspace_root(self) -> Path: ...

        @property
        def rope_workspace_root(self) -> Path: ...

        @property
        def workspace_index(self) -> p.Infra.RopeWorkspaceIndex: ...

    @runtime_checkable
    class RopePostHook(Protocol):
        """Contract for post-processing hooks invoked after Rope refactoring."""

        def __call__(
            self, path: Path, *, dry_run: bool
        ) -> t.SequenceOf[p.Infra.Result]:
            """Execute the hook and return results."""
            ...

    @runtime_checkable
    class PatchingASTWalker(Protocol):
        """Structural contract for rope's internal ``_PatchingASTWalker``.

        Used by ``FlextInfraUtilitiesRopePep695Patch`` to install PEP 695
        type-parameter handlers without depending on rope's private class.
        """

        # mro-j47u (codex): model Rope node capabilities structurally; the
        # FLEXT static path never imports or traverses Python's AST directly.
        @runtime_checkable
        class PositionedNode(Protocol):
            """Source position exposed by a Rope parser node."""

            lineno: int
            col_offset: int

        @runtime_checkable
        class TypeParameterOwner(Protocol):
            """Rope node carrying PEP 695 type parameters."""

            type_params: t.SequenceOf[p.AttributeProbe]

        @runtime_checkable
        class FunctionDefinitionNode(TypeParameterOwner, Protocol):
            """Function-definition capabilities consumed by the Rope patch."""

            decorator_list: t.SequenceOf[p.AttributeProbe]
            name: str
            args: p.AttributeProbe
            body: t.SequenceOf[p.AttributeProbe]

        @runtime_checkable
        class ClassDefinitionNode(TypeParameterOwner, Protocol):
            """Class-definition capabilities consumed by the Rope patch."""

            decorator_list: t.SequenceOf[p.AttributeProbe]
            name: str
            bases: t.SequenceOf[p.AttributeProbe]
            body: t.SequenceOf[p.AttributeProbe]

        @runtime_checkable
        class TypeAliasNode(TypeParameterOwner, Protocol):
            """Type-alias capabilities consumed by the Rope patch."""

            name: p.AttributeProbe
            value: p.AttributeProbe

        @runtime_checkable
        class TypeVariableNode(Protocol):
            """Bound type-variable capabilities consumed by the Rope patch."""

            name: str
            bound: p.AttributeProbe | None

        @runtime_checkable
        class NamedNode(Protocol):
            """Rope node exposing a name."""

            name: str

        @runtime_checkable
        class MatchSequenceNode(PositionedNode, Protocol):
            """Sequence-pattern capabilities consumed by the Rope patch."""

            patterns: t.SequenceOf[p.AttributeProbe]

        @runtime_checkable
        class MatchSingletonNode(Protocol):
            """Singleton-pattern capabilities consumed by the Rope patch."""

            value: p.AttributeProbe

        @runtime_checkable
        class MatchStarNode(Protocol):
            """Star-pattern capabilities consumed by the Rope patch."""

            name: str | None

        @runtime_checkable
        class MatchOrNode(Protocol):
            """Alternative-pattern capabilities consumed by the Rope patch."""

            patterns: t.SequenceOf[p.AttributeProbe]

        @runtime_checkable
        class SourceLines(Protocol):
            """Minimal line adapter contract exposed by rope patched AST walkers."""

            def get_line_start(self, lineno: int) -> int: ...

        @runtime_checkable
        class SourceBuffer(Protocol):
            """Minimal source buffer contract exposed by rope patched AST walkers."""

            source: str

        lines: FlextInfraProtocolsRope.PatchingASTWalker.SourceLines
        source: FlextInfraProtocolsRope.PatchingASTWalker.SourceBuffer
        empty_tuple: p.AttributeProbe

        def _handle(
            self,
            node: p.AttributeProbe,
            children: list[p.AttributeProbe],
            *,
            eat_parens: bool = False,
            eat_spaces: bool = False,
        ) -> None: ...

        def _child_nodes(
            self, nodes: t.SequenceOf[p.AttributeProbe], separator: str
        ) -> list[p.AttributeProbe]: ...

    @runtime_checkable
    class RopeAnalysisMethods(Protocol):
        """Class contract shared by the Rope analysis mixins."""

        @staticmethod
        def get_module_classes(
            rope_project: t.Infra.RopeProject, resource: t.Infra.RopeResource
        ) -> t.StrSequence: ...

        @staticmethod
        def get_class_methods(
            rope_project: t.Infra.RopeProject,
            resource: t.Infra.RopeResource,
            class_name: str,
            *,
            include_private: bool = False,
        ) -> t.StrMapping: ...

        @staticmethod
        def project_root(file_path: Path) -> Path | None: ...

        @staticmethod
        def init_rope_project(workspace_root: Path) -> t.Infra.RopeProject: ...

        @staticmethod
        def get_resource_from_path(
            rope_project: t.Infra.RopeProject, file_path: Path
        ) -> t.Infra.RopeResource | None: ...


__all__: list[str] = ["FlextInfraProtocolsRope"]
