# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from flext_cli import t

from flext_infra import c
from flext_infra._typings import FlextInfraTypesBase


class FlextInfraProtocolsCodegenLazyInit:
    """Own the structural model contracts declared by this module."""

    @runtime_checkable
    class PythonModuleFacts(Protocol):
        """Structural data contract projected from the owning model."""

        path: Path
        declaration_only: bool = ...
        members: Mapping[str, FlextInfraTypesBase.PythonMemberKind]
        imports: Mapping[str, str]
        exports: Sequence[str] | None
        classes: Mapping[str, Sequence[str]]
        class_exports: Mapping[str, Sequence[str] | None]
        values: Mapping[str, str]

    @runtime_checkable
    class LazyInitPackageContext(Protocol):
        """Structural data contract projected from the owning model."""

        pkg_dir: Path = ...
        init_path: Path = ...
        current_pkg: str = ...
        surface: str = ...
        generated_init: bool = ...
        importable: bool = ...

    @runtime_checkable
    class LazyInitPlan(Protocol):
        """Structural data contract projected from the owning model."""

        context: FlextInfraProtocolsCodegenLazyInit.LazyInitPackageContext = ...
        action: c.Infra.LazyInitAction = ...
        ownership: Literal["generator", "authored"] | None = ...
        disposition: Literal["planned", "retained"] | None = ...
        exports: Sequence[str] = ...
        lazy_map: t.LazyAliasMap = ...
        eager_dunders: t.LazyAliasMap = ...
        child_packages_for_lazy: Sequence[str] = ...

    @runtime_checkable
    class RopeModuleIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

        file_path: Path
        resource_path: str
        module_name: str
        package_name: str
        package_dir: Path
        project_root: Path | None = ...
        is_package_init: bool = ...

    @runtime_checkable
    class RopePackageIndexEntry(Protocol):
        """Structural data contract projected from the owning model."""

        package_dir: Path
        init_path: Path
        package_name: str
        project_root: Path | None = ...
        modules: tuple[
            FlextInfraProtocolsCodegenLazyInit.RopeModuleIndexEntry, ...
        ] = ...
        direct_child_dirs: tuple[Path, ...] = ...
        descendant_child_dirs: tuple[Path, ...] = ...

    @runtime_checkable
    class RopeWorkspaceIndex(Protocol):
        """Structural data contract projected from the owning model."""

        repository_root: Path
        package_dirs: tuple[Path, ...] = ...
        packages_by_dir: Mapping[
            str, FlextInfraProtocolsCodegenLazyInit.RopePackageIndexEntry
        ]
        modules_by_path: Mapping[
            str, FlextInfraProtocolsCodegenLazyInit.RopeModuleIndexEntry
        ]
        package_dir_by_name: Mapping[str, Path]
        project_package_by_root: Mapping[str, str]

    @runtime_checkable
    class RopeProjectLayout(Protocol):
        """Structural data contract projected from the owning model."""

        project_root: Path
        project_name: str
        package_name: str
        package_alias: str
        class_stem: str
        src_dir: Path
        package_dir: Path
        init_path: Path
        runtime_aliases: tuple[str, ...] = ...
        repository_namespace_packages: tuple[str, ...]


__all__: list[str] = [
    "FlextInfraProtocolsCodegenLazyInit",
]
