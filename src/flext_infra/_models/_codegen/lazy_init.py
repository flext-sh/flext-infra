"""Lazy-init planning and quality-gate models.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Annotated, ClassVar, Literal

from flext_cli import m, t

from flext_infra import c
from flext_infra._models import FlextInfraModelsMixins
from flext_infra._protocols import FlextInfraProtocolsWorkspaceSnapshot
from flext_infra._typings import FlextInfraTypesBase, FlextInfraTypesRopeNative


class FlextInfraModelsCodegenLazyInit:
    """Lazy-init planning and quality-gate models."""

    class PythonModuleFacts(m.ContractModel):
        """Static top-level facts of one module source, derived once per parse."""

        path: Annotated[Path, m.Field(description="Source file the facts describe")]
        declaration_only: bool = m.Field(
            description="Native syntax contains only documentation and future imports"
        )
        members: Annotated[
            Mapping[str, FlextInfraTypesBase.PythonMemberKind],
            m.Field(description="Every bound top-level name, in declaration order"),
        ]
        imports: Annotated[
            Mapping[str, str],
            m.Field(description="Dotted import target of each imported name"),
        ]
        exports: Annotated[
            Sequence[str] | None,
            m.Field(
                description=(
                    "Literal ``__all__`` names; empty when an entry is not a "
                    "string literal; ``None`` when the module declares none"
                ),
            ),
        ]
        classes: Annotated[
            Mapping[str, Sequence[str]],
            m.Field(description="Base expressions as written, per defined class"),
        ]
        class_exports: Annotated[
            Mapping[str, Sequence[str] | None],
            m.Field(description="Class-level ``__all__`` names per defined class"),
        ]
        values: Annotated[
            Mapping[str, str],
            m.Field(description="Source text of each assigned top-level value"),
        ]

    class PythonModuleFactsDraft(m.ArbitraryTypesModel):
        """Facts of one module accumulated statement by statement, then frozen."""

        path: Annotated[Path, m.Field(description="Source file being read")]
        name: Annotated[str, m.Field(description="Dotted module name")]
        is_init: Annotated[bool, m.Field(description="Whether it is a package init")]
        members: Annotated[
            t.Port[dict[str, FlextInfraTypesBase.PythonMemberKind]],
            m.Field(exclude=True, description="Bound names so far, in order"),
        ]
        imports: Annotated[
            t.Port[dict[str, str]],
            m.Field(exclude=True, description="Import targets so far"),
        ]
        classes: Annotated[
            t.Port[dict[str, Sequence[str]]],
            m.Field(exclude=True, description="Class bases so far"),
        ]
        class_exports: Annotated[
            t.Port[dict[str, Sequence[str] | None]],
            m.Field(exclude=True, description="Class-level exports so far"),
        ]
        values: Annotated[
            t.Port[dict[str, str]],
            m.Field(exclude=True, description="Assigned value text so far"),
        ]
        exports: Annotated[
            t.Port[list[str | None]] | None,
            m.Field(exclude=True, description="``__all__`` entries so far"),
        ] = None

    class PythonModelRun(m.ArbitraryTypesModel):
        """One run of the shared static Python model: source view and parse caches."""

        source_project: Annotated[
            t.Port[FlextInfraProtocolsWorkspaceSnapshot.RopeProject],
            m.Field(
                exclude=True, description="Source view every module is read through"
            ),
        ]
        module_files: Annotated[
            Mapping[str, Path],
            m.Field(description="Indexed module names elected before installed ones"),
        ]
        modules: Annotated[
            t.Port[
                MutableMapping[
                    FlextInfraTypesRopeNative.RopeNativeParsedModule,
                    FlextInfraModelsCodegenLazyInit.PythonModuleFacts,
                ]
            ],
            m.Field(
                exclude=True,
                description="Facts of each parsed module, keyed by the run's parse",
            ),
        ]
        project_notices: Annotated[
            t.Port[dict[Path, tuple[FlextInfraTypesBase.DocumentationLanguage, str]]],
            m.Field(
                exclude=True,
                description=(
                    "Documentation language and copyright notice per owning "
                    "project root, read once per run"
                ),
            ),
        ]

    class LazyInitPackageContext(m.ContractModel):
        """Declarative package context for one lazy-init directory."""

        pkg_dir: Path = m.Field(description="Directory being processed.")
        init_path: Path = m.Field(description="Target __init__.py path.")
        current_pkg: str = m.Field(description="Importable package name.")
        surface: str = m.Field(description="Root surface for wrapper alias resolution.")
        generated_init: Annotated[
            bool,
            m.Field(
                description=(
                    "Whether the current __init__.py is generated by lazy-init."
                ),
            ),
        ] = False
        importable: Annotated[
            bool,
            m.Field(
                description="Whether the directory resolves to an importable package.",
            ),
        ] = False

    class LazyInitPlan(m.ContractModel):
        """Immutable resolved decision and its original source consumption."""

        context: FlextInfraModelsCodegenLazyInit.LazyInitPackageContext = m.Field(
            description="Discovered package context.",
        )
        action: Annotated[
            c.Infra.LazyInitAction,
            m.Field(description="Action selected for this package."),
        ] = c.Infra.LazyInitAction.SKIP
        ownership: Literal["generator", "authored"] | None = m.Field(
            default=None,
            description="Content-elected initializer owner",
        )
        disposition: Literal["planned", "retained"] | None = m.Field(
            default=None,
            description="Actual ownership decision, never a failure suppression",
        )
        exports: Sequence[str] = m.Field(
            default_factory=tuple,
            description="Public exports for generated __init__.py.",
        )
        lazy_map: t.LazyAliasMap = m.Field(
            description="Lazy import map: export name to module/attribute target.",
        )
        eager_dunders: t.LazyAliasMap = m.Field(
            description=(
                "Dunder exports bound eagerly right after the lazy installer. "
                "Required for the ``__version__.py`` submodule case where the "
                "submodule name collides with the dunder string it exports — "
                "the first submodule load rebinds the package attribute to the "
                "module, so only an eager binding pins the canonical string; "
                "running after the installer lets the submodule consume the "
                "package's own facades without an initialization cycle."
            ),
        )
        child_packages_for_lazy: Sequence[str] = m.Field(
            default_factory=tuple,
            description=(
                "Importable direct child packages recorded as metadata; "
                "their symbols are not reexported by an ancestor."
            ),
        )

    class RopeModuleIndexEntry(m.ContractModel):
        """Generic Rope-backed index entry for one Python module resource."""

        file_path: Annotated[Path, m.Field(description="Absolute filesystem path")]
        resource_path: Annotated[
            str,
            m.Field(description="Rope resource path relative to the project root"),
        ]
        module_name: Annotated[
            str,
            m.Field(description="Fully-qualified Rope module name for this file"),
        ]
        package_name: Annotated[
            str,
            m.Field(
                description="Importable package resolved for the containing directory",
            ),
        ]
        package_dir: Annotated[
            Path,
            m.Field(description="Absolute package directory for this module"),
        ]
        project_root: Annotated[
            Path | None,
            m.Field(
                description="Owning project root resolved from the Rope source folder",
            ),
        ] = None
        is_package_init: Annotated[
            bool,
            m.Field(description="Whether this resource is the package __init__.py"),
        ] = False

    class RopePackageIndexEntry(m.ContractModel):
        """Generic Rope-backed package aggregation entry."""

        package_dir: Annotated[
            Path,
            m.Field(description="Absolute package directory represented by this entry"),
        ]
        init_path: Annotated[
            Path,
            m.Field(description="Expected __init__.py path for this package directory"),
        ]
        package_name: Annotated[
            str,
            m.Field(
                description="Importable package name, or empty when non-importable",
            ),
        ]
        project_root: Annotated[
            Path | None,
            m.Field(
                description="Owning project root resolved for this package directory",
            ),
        ] = None
        modules: Annotated[
            tuple[FlextInfraModelsCodegenLazyInit.RopeModuleIndexEntry, ...],
            m.Field(
                description=(
                    "Direct Python module resources that belong to this package"
                ),
            ),
        ] = ()
        direct_child_dirs: Annotated[
            tuple[Path, ...],
            m.Field(
                description="Direct child package directories discovered from Rope",
            ),
        ] = ()
        descendant_child_dirs: Annotated[
            tuple[Path, ...],
            m.Field(
                description="All descendant package directories discovered from Rope",
            ),
        ] = ()

    class RopeWorkspaceIndex(m.ContractModel):
        """Generic Rope-backed workspace index for package planning."""

        repository_root: Annotated[
            Path,
            m.Field(
                description="Absolute repository root used to open the Rope project",
            ),
        ]
        package_dirs: Annotated[
            tuple[Path, ...],
            m.Field(
                description="All package directories discovered from Rope resources",
            ),
        ] = ()
        packages_by_dir: Annotated[
            Mapping[str, FlextInfraModelsCodegenLazyInit.RopePackageIndexEntry],
            m.Field(description="Package entries keyed by absolute directory path"),
        ]
        modules_by_path: Annotated[
            Mapping[str, FlextInfraModelsCodegenLazyInit.RopeModuleIndexEntry],
            m.Field(description="Module entries keyed by absolute file path"),
        ]
        package_dir_by_name: Annotated[
            Mapping[str, Path],
            m.Field(description="Importable package directory keyed by package name"),
        ]
        project_package_by_root: Annotated[
            Mapping[str, str],
            m.Field(
                description="Canonical source package name keyed by project root path",
            ),
        ]

    class LazyInitRun(m.ArbitraryTypesModel):
        """One repository's lazy-init planning run over its source inventory."""

        root: Annotated[Path, m.Field(description="Repository root being planned")]
        scoped: Annotated[
            bool,
            m.Field(description="Whether conformance selected the repository roots"),
        ]
        index: Annotated[
            FlextInfraModelsCodegenLazyInit.RopeWorkspaceIndex,
            m.Field(description="The repository's shared source inventory"),
        ]
        model: Annotated[
            FlextInfraModelsCodegenLazyInit.PythonModelRun,
            m.Field(description="The run's parse-once static Python model"),
        ]
        plans: Annotated[
            t.Port[dict[Path, FlextInfraModelsCodegenLazyInit.LazyInitPlan]],
            m.Field(exclude=True, description="Decided plans, children first"),
        ]
        contexts: Annotated[
            t.Port[dict[Path, FlextInfraModelsCodegenLazyInit.LazyInitPackageContext]],
            m.Field(exclude=True, description="Package contexts by directory"),
        ]
        parents: Annotated[
            t.Port[dict[Path, Sequence[str]]],
            m.Field(exclude=True, description="Facade parents by package directory"),
        ]
        declared: Annotated[
            t.Port[dict[str, frozenset[str]]],
            m.Field(exclude=True, description="Declared facade letters by package"),
        ]
        packages: Annotated[
            t.Port[dict[Path, str]],
            m.Field(exclude=True, description="Declared public package by project"),
        ]
        collisions: Annotated[
            t.Port[list[str]],
            m.Field(exclude=True, description="Ambiguous export ownership findings"),
        ]

    class RopeProjectLayout(m.ContractModel):
        """Canonical project layout derived once for Rope-backed codegen flows."""

        project_root: Annotated[Path, m.Field(description="Resolved project root path")]
        project_name: Annotated[str, m.Field(description="Canonical project name")]
        package_name: Annotated[str, m.Field(description="Primary Python package name")]
        package_alias: Annotated[
            str,
            m.Field(description="Canonical root alias derived from the package"),
        ]
        class_stem: Annotated[
            str,
            m.Field(description="Canonical facade class stem derived from the project"),
        ]
        src_dir: Annotated[
            Path,
            m.Field(description="Resolved source directory for the project"),
        ]
        package_dir: Annotated[
            Path,
            m.Field(description="Resolved package directory for the project"),
        ]
        init_path: Annotated[
            Path,
            m.Field(description="Resolved package __init__.py path"),
        ]
        runtime_aliases: Annotated[
            tuple[str, ...],
            m.Field(
                description="Canonical runtime aliases published by the package root",
            ),
        ] = ()
        repository_namespace_packages: Annotated[
            tuple[str, ...],
            m.Field(description="Independent packages from the captured declaration"),
        ]

    class LazyInitRootRender(m.ArbitraryTypesModel):
        """Template context for one lazy public root ``__init__.py``."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(extra="forbid", frozen=True)

        autogen_header: t.NonEmptyStr = m.Field(description="Generated file header.")
        docstring: t.NonEmptyStr = m.Field(description="Generated module docstring.")
        runtime_import_lines: t.NonEmptyStr = m.Field(
            description="Isort-ordered runtime imports of the lazy helpers.",
        )
        eager_binding_lines: str = m.Field(
            default_factory=str,
            description=(
                "Runtime-only eager dunder bindings emitted after the lazy "
                "installer, so the bound submodule may consume the package's "
                "own facades while its static contract stays in TYPE_CHECKING."
            ),
        )
        type_checking_lines: str = m.Field(
            default_factory=str,
            description="Static declarations for public lazy exports.",
        )
        exports_tuple: t.NonEmptyStr = m.Field(
            description="Canonical rendered root ``__all__`` tuple.",
        )
        lazy_export_mapping: t.NonEmptyStr = m.Field(
            description="Immutable elected export-to-target installer argument.",
        )

    class QualityGateCheck(m.ArbitraryTypesModel):
        """A single quality gate check result entry."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Check identifier")]
        passed: Annotated[bool, m.Field(description="Whether check passed")]
        detail: Annotated[str, m.Field(description="Human-readable check detail")] = ""
        critical: Annotated[bool, m.Field(description="Whether failure is critical")]

    class QualityGateProjectFinding(
        FlextInfraModelsMixins.ProjectNameMixin,
        m.ArbitraryTypesModel,
    ):
        """Per-project quality gate findings."""

        violations_total: Annotated[
            t.NonNegativeInt,
            m.Field(description="Total violations"),
        ]
        validator_passed: Annotated[
            bool,
            m.Field(description="Whether validator passed"),
        ]


__all__: list[str] = ["FlextInfraModelsCodegenLazyInit"]
