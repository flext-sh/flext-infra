# AUTO-GENERATED FILE — Regenerate with: make gen
"""Source-derived structural model contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
src/flext_infra/_protocols/_codegen/lazy_init
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

from flext_cli import FlextCliProtocols

from flext_infra._protocols import FlextInfraProtocolsMixins
from flext_infra._typings import FlextInfraTypesBase, FlextInfraTypesRopeNative

if TYPE_CHECKING:
    from flext_infra import t
    from flext_infra._constants import FlextInfraConstantsBase
    from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot


class FlextInfraProtocolsCodegenLazyInit:
    """Own the structural contracts declared by its model source."""

    @runtime_checkable
    class PythonModuleFacts(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Source file the facts describe."""
            ...

        @property
        def declaration_only(self) -> bool:
            """Native syntax contains only documentation and future imports."""
            ...

        @property
        def members(self) -> Mapping[str, FlextInfraTypesBase.PythonMemberKind]:
            """Every bound top-level name, in declaration order."""
            ...

        @property
        def imports(self) -> Mapping[str, str]:
            """Dotted import target of each imported name."""
            ...

        @property
        def exports(self) -> Sequence[str] | None:
            """Structural member projected from the owning model.

            Literal ``__all__`` names; empty when an entry is not a string literal;
            ``None`` when the module declares none.
            """
            ...

        @property
        def classes(self) -> Mapping[str, Sequence[str]]:
            """Base expressions as written, per defined class."""
            ...

        @property
        def class_exports(self) -> Mapping[str, Sequence[str] | None]:
            """Class-level ``__all__`` names per defined class."""
            ...

        @property
        def values(self) -> Mapping[str, str]:
            """Source text of each assigned top-level value."""
            ...

    @runtime_checkable
    class PythonModuleFactsDraft(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def path(self) -> Path:
            """Source file being read."""
            ...

        @property
        def name(self) -> str:
            """Dotted module name."""
            ...

        @property
        def is_init(self) -> bool:
            """Whether it is a package init."""
            ...

        @property
        def members(self) -> dict[str, FlextInfraTypesBase.PythonMemberKind]:
            """Bound names so far, in order."""
            ...

        @property
        def imports(self) -> dict[str, str]:
            """Import targets so far."""
            ...

        @property
        def classes(self) -> dict[str, Sequence[str]]:
            """Class bases so far."""
            ...

        @property
        def class_exports(self) -> dict[str, Sequence[str] | None]:
            """Class-level exports so far."""
            ...

        @property
        def values(self) -> dict[str, str]:
            """Assigned value text so far."""
            ...

        @property
        def exports(self) -> list[str | None] | None:
            """``__all__`` entries so far."""
            ...

    @runtime_checkable
    class PythonModelRun(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def source_project(self) -> FlextInfraProtocolsWorkspaceSnapshot.RopeProject:
            """Source view every module is read through."""
            ...

        @property
        def module_files(self) -> Mapping[str, Path]:
            """Indexed module names elected before installed ones."""
            ...

        @property
        def modules(
            self,
        ) -> Mapping[
            FlextInfraTypesRopeNative.RopeNativeParsedModule,
            FlextInfraProtocolsCodegenLazyInit.PythonModuleFacts,
        ]:
            """Facts of each parsed module, keyed by the run's parse."""
            ...

        @property
        def project_notices(
            self,
        ) -> dict[Path, tuple[FlextInfraTypesBase.DocumentationLanguage, str]]:
            """Structural member projected from the owning model.

            Documentation language and copyright notice per owning project root,
            read once per run.
            """
            ...

    @runtime_checkable
    class LazyInitPackageContext(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def pkg_dir(self) -> Path:
            """Directory being processed."""
            ...

        @property
        def init_path(self) -> Path:
            """Target __init__.py path."""
            ...

        @property
        def current_pkg(self) -> str:
            """Importable package name."""
            ...

        @property
        def surface(self) -> str:
            """Root surface for wrapper alias resolution."""
            ...

        @property
        def generated_init(self) -> bool:
            """Whether the current __init__.py is generated by lazy-init."""
            ...

        @property
        def importable(self) -> bool:
            """Whether the directory resolves to an importable package."""
            ...

    @runtime_checkable
    class LazyInitPlan(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def context(self) -> FlextInfraProtocolsCodegenLazyInit.LazyInitPackageContext:
            """Discovered package context."""
            ...

        @property
        def action(self) -> FlextInfraConstantsBase.LazyInitAction:
            """Action selected for this package."""
            ...

        @property
        def ownership(self) -> Literal["generator", "authored"] | None:
            """Content-elected initializer owner."""
            ...

        @property
        def disposition(self) -> Literal["planned", "retained"] | None:
            """Actual ownership decision, never a failure suppression."""
            ...

        @property
        def exports(self) -> Sequence[str]:
            """Public exports for generated __init__.py."""
            ...

        @property
        def lazy_map(self) -> t.LazyAliasMap:
            """Lazy import map: export name to module/attribute target."""
            ...

        @property
        def eager_dunders(self) -> t.LazyAliasMap:
            """Structural member projected from the owning model.

            Dunder exports bound eagerly right after the lazy installer. Required
            for the ``__version__.py`` submodule case where the submodule name
            collides with the dunder string it exports — the first submodule load
            rebinds the package attribute to the module, so only an eager binding
            pins the canonical string; running after the installer lets the
            submodule consume the package's own facades without an initialization
            cycle.
            """
            ...

        @property
        def child_packages_for_lazy(self) -> Sequence[str]:
            """Structural member projected from the owning model.

            Importable direct child packages recorded as metadata; their symbols are
            not reexported by an ancestor.
            """
            ...

    @runtime_checkable
    class RopeModuleIndexEntry(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def file_path(self) -> Path:
            """Absolute filesystem path."""
            ...

        @property
        def resource_path(self) -> str:
            """Rope resource path relative to the project root."""
            ...

        @property
        def module_name(self) -> str:
            """Fully-qualified Rope module name for this file."""
            ...

        @property
        def package_name(self) -> str:
            """Importable package resolved for the containing directory."""
            ...

        @property
        def package_dir(self) -> Path:
            """Absolute package directory for this module."""
            ...

        @property
        def project_root(self) -> Path | None:
            """Owning project root resolved from the Rope source folder."""
            ...

        @property
        def is_package_init(self) -> bool:
            """Whether this resource is the package __init__.py."""
            ...

    @runtime_checkable
    class RopePackageIndexEntry(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def package_dir(self) -> Path:
            """Absolute package directory represented by this entry."""
            ...

        @property
        def init_path(self) -> Path:
            """Expected __init__.py path for this package directory."""
            ...

        @property
        def package_name(self) -> str:
            """Importable package name, or empty when non-importable."""
            ...

        @property
        def project_root(self) -> Path | None:
            """Owning project root resolved for this package directory."""
            ...

        @property
        def modules(
            self,
        ) -> tuple[FlextInfraProtocolsCodegenLazyInit.RopeModuleIndexEntry, ...]:
            """Direct Python module resources that belong to this package."""
            ...

        @property
        def direct_child_dirs(self) -> tuple[Path, ...]:
            """Direct child package directories discovered from Rope."""
            ...

        @property
        def descendant_child_dirs(self) -> tuple[Path, ...]:
            """All descendant package directories discovered from Rope."""
            ...

    @runtime_checkable
    class RopeWorkspaceIndex(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def repository_root(self) -> Path:
            """Absolute repository root used to open the Rope project."""
            ...

        @property
        def package_dirs(self) -> tuple[Path, ...]:
            """All package directories discovered from Rope resources."""
            ...

        @property
        def packages_by_dir(
            self,
        ) -> Mapping[str, FlextInfraProtocolsCodegenLazyInit.RopePackageIndexEntry]:
            """Package entries keyed by absolute directory path."""
            ...

        @property
        def modules_by_path(
            self,
        ) -> Mapping[str, FlextInfraProtocolsCodegenLazyInit.RopeModuleIndexEntry]:
            """Module entries keyed by absolute file path."""
            ...

        @property
        def package_dir_by_name(self) -> Mapping[str, Path]:
            """Importable package directory keyed by package name."""
            ...

        @property
        def project_package_by_root(self) -> Mapping[str, str]:
            """Canonical source package name keyed by project root path."""
            ...

    @runtime_checkable
    class LazyInitRun(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def root(self) -> Path:
            """Repository root being planned."""
            ...

        @property
        def scoped(self) -> bool:
            """Whether conformance selected the repository roots."""
            ...

        @property
        def index(self) -> FlextInfraProtocolsCodegenLazyInit.RopeWorkspaceIndex:
            """The repository's shared source inventory."""
            ...

        @property
        def model(self) -> FlextInfraProtocolsCodegenLazyInit.PythonModelRun:
            """The run's parse-once static Python model."""
            ...

        @property
        def plans(
            self,
        ) -> Mapping[Path, FlextInfraProtocolsCodegenLazyInit.LazyInitPlan]:
            """Decided plans, children first."""
            ...

        @property
        def contexts(
            self,
        ) -> Mapping[Path, FlextInfraProtocolsCodegenLazyInit.LazyInitPackageContext]:
            """Package contexts by directory."""
            ...

        @property
        def parents(self) -> dict[Path, Sequence[str]]:
            """Facade parents by package directory."""
            ...

        @property
        def declared(self) -> dict[str, frozenset[str]]:
            """Declared facade letters by package."""
            ...

        @property
        def declarations(self) -> dict[tuple[str, str], tuple[str, bool]]:
            """Structural member projected from the owning model.

            Declaring module and letter status per published (package, name) whose
            route crosses only decided plans.
            """
            ...

        @property
        def packages(self) -> dict[Path, str]:
            """Declared public package by project."""
            ...

        @property
        def collisions(self) -> list[str]:
            """Ambiguous export ownership findings."""
            ...

    @runtime_checkable
    class RopeProjectLayout(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def project_root(self) -> Path:
            """Resolved project root path."""
            ...

        @property
        def project_name(self) -> str:
            """Canonical project name."""
            ...

        @property
        def package_name(self) -> str:
            """Primary Python package name."""
            ...

        @property
        def package_alias(self) -> str:
            """Canonical root alias derived from the package."""
            ...

        @property
        def class_stem(self) -> str:
            """Canonical facade class stem derived from the project."""
            ...

        @property
        def src_dir(self) -> Path:
            """Resolved source directory for the project."""
            ...

        @property
        def package_dir(self) -> Path:
            """Resolved package directory for the project."""
            ...

        @property
        def init_path(self) -> Path:
            """Resolved package __init__.py path."""
            ...

        @property
        def runtime_aliases(self) -> tuple[str, ...]:
            """Canonical runtime aliases published by the package root."""
            ...

        @property
        def repository_namespace_packages(self) -> tuple[str, ...]:
            """Independent packages from the captured declaration."""
            ...

    @runtime_checkable
    class LazyInitRootRender(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def autogen_header(self) -> t.NonEmptyStr:
            """Generated file header."""
            ...

        @property
        def docstring(self) -> t.NonEmptyStr:
            """Generated module docstring."""
            ...

        @property
        def runtime_import_lines(self) -> t.NonEmptyStr:
            """Isort-ordered runtime imports of the lazy helpers."""
            ...

        @property
        def eager_binding_lines(self) -> str:
            """Structural member projected from the owning model.

            Runtime-only eager dunder bindings emitted after the lazy installer, so
            the bound submodule may consume the package's own facades while its
            static contract stays in TYPE_CHECKING.
            """
            ...

        @property
        def type_checking_lines(self) -> str:
            """Static declarations for public lazy exports."""
            ...

        @property
        def exports_tuple(self) -> t.NonEmptyStr:
            """Canonical rendered root ``__all__`` tuple."""
            ...

        @property
        def lazy_export_mapping(self) -> t.NonEmptyStr:
            """Literal elected export-to-target installer argument."""
            ...

    @runtime_checkable
    class QualityGateCheck(FlextCliProtocols.Model, Protocol):
        """Structural data contract projected from the owning model."""

        @property
        def name(self) -> t.NonEmptyStr:
            """Check identifier."""
            ...

        @property
        def passed(self) -> bool:
            """Whether check passed."""
            ...

        @property
        def detail(self) -> str:
            """Human-readable check detail."""
            ...

        @property
        def critical(self) -> bool:
            """Whether failure is critical."""
            ...

    @runtime_checkable
    class QualityGateProjectFinding(
        FlextInfraProtocolsMixins.ProjectNameMixin, Protocol
    ):
        """Structural data contract projected from the owning model."""

        @property
        def violations_total(self) -> t.NonNegativeInt:
            """Total violations."""
            ...

        @property
        def validator_passed(self) -> bool:
            """Whether validator passed."""
            ...


__all__: list[str] = [
    "FlextInfraProtocolsCodegenLazyInit",
]
