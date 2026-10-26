"""Application-level protocols for Rope-backed infra utilities.

Concrete Rope objects are typed in ``t.Infra.Rope*``. This module keeps only
FLEXT callback contracts that do not have a concrete Rope class.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from pathlib import Path
    from types import TracebackType

    from flext_core import t

    from flext_infra import m
    from flext_infra._protocols.base import FlextInfraProtocolsBase
    from flext_infra._protocols.rope_runtime import FlextInfraProtocolsRopeRuntime
    from flext_infra._protocols.workspace_snapshot import (
        FlextInfraProtocolsWorkspaceSnapshot,
    )


@runtime_checkable
class FlextInfraProtocolsRope(Protocol):
    """Application contracts layered around the concrete Rope boundary."""

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
        def phase(self) -> str: ...

        @property
        def pattern(self) -> str: ...

        @property
        def goal(self) -> str: ...

        @property
        def arguments(self) -> t.MappingKV[str, str | t.StrSequence]: ...

        @property
        def imports(self) -> t.MappingKV[str, str]: ...

        @property
        def bindings(self) -> t.MappingKV[str, str]: ...

        @property
        def model_bases(self) -> t.StrSequence: ...

        @property
        def unshadowed_builtins(self) -> t.StrSequence: ...

        @property
        def repeats(self) -> str | None: ...

        @property
        def readonly_contract(self) -> str | None: ...

        @property
        def deferred_contract(self) -> str | None: ...

        @property
        def readonly_origins(self) -> t.StrSequence: ...

        @property
        def drops(self) -> t.StrSequence: ...

    @runtime_checkable
    class RopeContractRule(RopeContractCapturePolicy, Protocol):
        """Read-only policy consumed by the native contract planner."""

        @property
        def operation(self) -> str: ...

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
        def missing_keywords(self) -> t.StrSequence: ...

        @property
        def reorders_annotation(self) -> bool: ...

        @property
        def families(self) -> t.StrSequence: ...

        @property
        def scope_kinds(self) -> t.StrSequence: ...

        @property
        def implementation_owner(self) -> t.Pair[str, str] | None: ...

        @property
        def receiver_methods(self) -> t.StrSequence: ...

        @property
        def ownership_transfer(self) -> t.Pair[str, str] | None: ...

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
        def arg(self) -> t.StrSequence: ...

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
        def changes(self) -> t.VariadicTuple[str]: ...

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
        def bases(self) -> t.StrSequence: ...

    @runtime_checkable
    class ModuleSemanticState(Protocol):
        """Read-only semantic facts produced by the canonical module analyzer."""

        @property
        def class_infos(
            self,
        ) -> t.VariadicTuple[FlextInfraProtocolsRope.ClassInfo]: ...

        @property
        def declared_imports(self) -> t.StrMapping: ...

        @property
        def semantic_imports(self) -> t.StrMapping: ...

    @runtime_checkable
    class SourceScanRequest(Protocol):
        """Fields required by production-source discovery."""

        @property
        def project_roots(self) -> t.VariadicTuple[Path]:
            """Non-empty ordered project roots selected at the boundary."""
            ...

    @runtime_checkable
    class ChangeTracker(Protocol):
        """Transformer contract for in-memory source rewrites with change tracking."""

        changes: t.MutableSequenceOf[str]

        def apply_to_source(self, source: str) -> t.StrSequencePair: ...

    @runtime_checkable
    class RopeScopeDsl(Protocol):
        """Public scope contract for Rope semantic traversal."""

        def get_scopes(self) -> t.SequenceOf[FlextInfraProtocolsRope.RopeScopeDsl]: ...

        def get_names(
            self,
        ) -> t.MappingKV[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

        def get_defined_names(
            self,
        ) -> t.MappingKV[str, FlextInfraProtocolsRopeRuntime.RopePyName]: ...

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
        def workspace_index(self) -> m.Infra.RopeWorkspaceIndex: ...

        def refresh(
            self,
            *,
            preserve_indexes: bool = False,
            validate_project: bool = True,
        ) -> m.Infra.RopeWorkspaceSession: ...

        def reload(self) -> m.Infra.RopeWorkspaceSession: ...

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

        @property
        def snapshot(self) -> FlextInfraProtocolsWorkspaceSnapshot.WorkspaceSnapshot:
            """Return the generic source epoch already owned by this session."""
            ...

        @classmethod
        def open_workspace(
            cls,
            repository_root: Path,
            *,
            rope_repository_root: Path | None = None,
            source_project: FlextInfraProtocolsRopeRuntime.RopeProject | None = None,
            workspace_index: m.Infra.RopeWorkspaceIndex | None = None,
        ) -> Self: ...

        def resource(
            self,
            file_path: Path,
        ) -> FlextInfraProtocolsRopeRuntime.RopeFile | None: ...

        def module(self, file_path: Path) -> m.Infra.RopeModuleIndexEntry | None: ...

        def package(
            self,
            package_dir: Path,
        ) -> m.Infra.RopePackageIndexEntry | None: ...

        def modules(
            self,
            *,
            project_names: t.StrSequence | None = None,
        ) -> t.SequenceOf[m.Infra.RopeModuleIndexEntry]: ...

        def source(self, file_path: Path) -> str: ...

        def name_index(
            self,
        ) -> t.MappingKV[str, tuple[tuple[Path, str, t.VariadicTuple[int]], ...]]: ...

        def import_dependents(self, import_target: str) -> t.VariadicTuple[Path]: ...

        def objects(
            self,
            file_path: Path,
            *,
            include_local_scopes: bool = True,
            include_references: bool = True,
        ) -> t.SequenceOf[m.Infra.Object]: ...

        def projects(self) -> t.SequenceOf[FlextInfraProtocolsBase.ProjectInfo]: ...

        def layout(self, project_root: Path) -> m.Infra.RopeProjectLayout | None: ...

        def package_context(
            self,
            package_dir: Path,
        ) -> m.Infra.LazyInitPackageContext: ...

        def policy(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
            current_pkg: str = "",
        ) -> m.Infra.NamespaceModulePolicy: ...

        def convention(
            self,
            file_path: Path,
            *,
            rel_path: Path | None = None,
        ) -> m.Infra.RopeModuleConvention: ...

        def semantic(
            self, file_path: Path
        ) -> FlextInfraProtocolsRope.ModuleSemanticState: ...

        def exports(
            self,
            file_path: Path,
            *,
            export_options: m.Infra.ExportOptions | None = None,
        ) -> t.StrSequence: ...

    @runtime_checkable
    class RopeAnalysisMethods(Protocol):
        """Class contract shared by the Rope analysis mixins."""

        @staticmethod
        def resolve_module_classes(
            rope_project: FlextInfraProtocolsRopeRuntime.RopeProject,
            resource: FlextInfraProtocolsRopeRuntime.RopeResource,
        ) -> t.StrSequence: ...

        @staticmethod
        def resolve_class_methods(
            rope_project: FlextInfraProtocolsRopeRuntime.RopeProject,
            resource: FlextInfraProtocolsRopeRuntime.RopeResource,
            class_name: str,
            *,
            include_private: bool = False,
        ) -> t.StrMapping: ...

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


__all__: list[str] = ["FlextInfraProtocolsRope"]
