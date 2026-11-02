# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/lazy_init
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import t

from flext_infra import c
from flext_infra._typings import FlextInfraTypesBase, FlextInfraTypesRopeNative

if TYPE_CHECKING:
    from flext_infra import p
    from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot


class FlextInfraProtocolsCodegenLazyInit:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class PythonModuleFacts(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path: ...
        @property
        def declaration_only(self) -> bool: ...
        @property
        def members(self) -> Mapping[str, FlextInfraTypesBase.PythonMemberKind]: ...
        @property
        def imports(self) -> Mapping[str, str]: ...
        @property
        def exports(self) -> Sequence[str] | None: ...
        @property
        def classes(self) -> Mapping[str, Sequence[str]]: ...
        @property
        def class_exports(self) -> Mapping[str, Sequence[str] | None]: ...
        @property
        def values(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class PythonModuleFactsDraft(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        name: str
        is_init: bool
        members: dict[str, FlextInfraTypesBase.PythonMemberKind]
        imports: dict[str, str]
        classes: dict[str, Sequence[str]]
        class_exports: dict[str, Sequence[str] | None]
        values: dict[str, str]
        exports: list[str | None] | None

    @runtime_checkable
    class PythonModelRun(Protocol):
        """Structural data contract projected from the owning model."""

        source_project: FlextInfraProtocolsWorkspaceSnapshot.RopeProject
        module_files: Mapping[str, Path]
        modules: MutableMapping[
            FlextInfraTypesRopeNative.RopeNativeParsedModule, p.Infra.PythonModuleFacts
        ]
        project_notices: dict[
            Path, tuple[FlextInfraTypesBase.DocumentationLanguage, str]
        ]

    @runtime_checkable
    class LazyInitPackageContext(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pkg_dir(self) -> Path: ...
        @property
        def init_path(self) -> Path: ...
        @property
        def current_pkg(self) -> str: ...
        @property
        def surface(self) -> str: ...
        @property
        def generated_init(self) -> bool: ...
        @property
        def importable(self) -> bool: ...

    @runtime_checkable
    class LazyInitPlan(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def context(self) -> p.Infra.LazyInitPackageContext: ...
        @property
        def action(self) -> c.Infra.LazyInitAction: ...
        @property
        def ownership(self) -> Literal["generator", "authored"] | None: ...
        @property
        def disposition(self) -> Literal["planned", "retained"] | None: ...
        @property
        def exports(self) -> Sequence[str]: ...
        @property
        def lazy_map(self) -> t.LazyAliasMap: ...
        @property
        def eager_dunders(self) -> t.LazyAliasMap: ...
        @property
        def child_packages_for_lazy(self) -> Sequence[str]: ...

    @runtime_checkable
    class RopeModuleIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

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
    class RopePackageIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

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
    class RopeWorkspaceIndex(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path: ...
        @property
        def package_dirs(self) -> tuple[Path, ...]: ...
        @property
        def packages_by_dir(self) -> Mapping[str, p.Infra.RopePackageIndexEntry]: ...
        @property
        def modules_by_path(self) -> Mapping[str, p.Infra.RopeModuleIndexEntry]: ...
        @property
        def package_dir_by_name(self) -> Mapping[str, Path]: ...
        @property
        def project_package_by_root(self) -> Mapping[str, str]: ...

    @runtime_checkable
    class LazyInitRun(Protocol):
        """Structural data contract projected from the owning model."""

        root: Path
        scoped: bool
        index: p.Infra.RopeWorkspaceIndex
        model: p.Infra.PythonModelRun
        plans: dict[Path, p.Infra.LazyInitPlan]
        contexts: dict[Path, p.Infra.LazyInitPackageContext]
        parents: dict[Path, Sequence[str]]
        declared: dict[str, frozenset[str]]
        declarations: dict[tuple[str, str], tuple[str, bool]]
        packages: dict[Path, str]
        collisions: list[str]

    @runtime_checkable
    class RopeProjectLayout(Protocol):
        """Structural data contract projected from the owning model."""

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
        def runtime_aliases(self) -> tuple[str, ...]: ...
        @property
        def repository_namespace_packages(self) -> tuple[str, ...]: ...

    @runtime_checkable
    class LazyInitRootRender(Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def autogen_header(self) -> t.NonEmptyStr: ...
        @property
        def docstring(self) -> t.NonEmptyStr: ...
        @property
        def runtime_import_lines(self) -> t.NonEmptyStr: ...
        @property
        def eager_binding_lines(self) -> str: ...
        @property
        def type_checking_lines(self) -> str: ...
        @property
        def exports_tuple(self) -> t.NonEmptyStr: ...
        @property
        def lazy_export_mapping(self) -> t.NonEmptyStr: ...

    @runtime_checkable
    class QualityGateCheck(Protocol):
        """Structural data contract projected from the owning model."""

        name: t.NonEmptyStr
        passed: bool
        detail: str
        critical: bool

    @runtime_checkable
    class QualityGateProjectFinding(Protocol):
        """Structural data contract projected from the owning model."""

        project: t.NonEmptyStr
        violations_total: t.NonNegativeInt
        validator_passed: bool


__all__: list[str] = [
    "FlextInfraProtocolsCodegenLazyInit",
]
