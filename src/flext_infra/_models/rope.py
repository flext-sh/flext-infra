"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Mapping,
)
from pathlib import Path
from typing import Annotated

from flext_cli import m

from flext_infra import FlextInfraModelsCodegen, FlextInfraModelsMixins as mm, t


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class ClassInfo(
        mm.PositiveLineMixin,
        m.ContractModel,
    ):
        """Semantic class info from rope — name, line, bases in one shot."""

        name: Annotated[str, m.Field(description="Class name")]
        bases: Annotated[tuple[str, ...], m.Field(description="Base class names")] = ()

    class ConstantInfo(
        mm.NonNegativeLineMixin,
        mm.NestedClassPathMixin,
        m.ContractModel,
    ):
        """Final-annotated constant definition from rope semantic analysis."""

        name: Annotated[str, m.Field(description="Constant name")]
        annotation: Annotated[str, m.Field(description="Type annotation text")] = ""
        value: Annotated[str, m.Field(description="Value representation")] = ""

    class SymbolInfo(
        mm.NonNegativeLineMixin,
        m.ContractModel,
    ):
        """Top-level symbol metadata from rope semantic analysis."""

        name: Annotated[str, m.Field(description="Symbol name")]
        kind: Annotated[
            str, m.Field(description="Symbol kind: class, function, assignment")
        ]

    class ModuleSemanticState(m.ContractModel):
        """Unified semantic snapshot for one Rope module analysis pass.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        class_infos: Annotated[
            tuple[FlextInfraModelsRope.ClassInfo, ...],
            m.Field(description="Local classes discovered in the module"),
        ] = ()
        declared_imports: Annotated[
            t.StrMapping,
            m.Field(
                default_factory=dict, description="Declared import targets by name"
            ),
        ]
        semantic_imports: Annotated[
            t.StrMapping,
            m.Field(
                default_factory=dict, description="Resolved import targets by name"
            ),
        ]

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
                description="Importable package resolved for the containing directory"
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
            m.Field(
                description="Whether this resource is the package __init__.py",
            ),
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
                description="Importable package name, or empty when non-importable"
            ),
        ]
        project_root: Annotated[
            Path | None,
            m.Field(
                description="Owning project root resolved for this package directory",
            ),
        ] = None
        modules: Annotated[
            tuple[FlextInfraModelsRope.RopeModuleIndexEntry, ...],
            m.Field(
                description="Direct Python module resources that belong to this package",
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
        """Generic Rope-backed workspace index for package planning.

        Enforcement exemption: internal tooling model with intentional
        mutable state.
        """

        workspace_root: Annotated[
            Path,
            m.Field(
                description="Absolute workspace root used to open the Rope project"
            ),
        ]
        package_dirs: Annotated[
            tuple[Path, ...],
            m.Field(
                description="All package directories discovered from Rope resources",
            ),
        ] = ()
        packages_by_dir: Annotated[
            Mapping[str, FlextInfraModelsRope.RopePackageIndexEntry],
            m.Field(
                default_factory=dict,
                description="Package entries keyed by absolute directory path",
            ),
        ]
        modules_by_path: Annotated[
            Mapping[str, FlextInfraModelsRope.RopeModuleIndexEntry],
            m.Field(
                default_factory=dict,
                description="Module entries keyed by absolute file path",
            ),
        ]
        package_dir_by_name: Annotated[
            Mapping[str, Path],
            m.Field(
                default_factory=dict,
                description="Importable package directory keyed by package name",
            ),
        ]
        project_package_by_root: Annotated[
            t.StrMapping,
            m.Field(
                default_factory=dict,
                description="Canonical source package name keyed by project root path",
            ),
        ]

    class RopeProjectLayout(m.ContractModel):
        """Canonical project layout derived once for Rope-backed codegen flows."""

        project_root: Annotated[
            Path,
            m.Field(description="Resolved project root path"),
        ]
        project_name: Annotated[
            str,
            m.Field(description="Canonical project name"),
        ]
        package_name: Annotated[
            str,
            m.Field(description="Primary Python package name"),
        ]
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

    class RopeModuleConvention(m.ContractModel):
        """Unified module naming and namespace convention for one file."""

        file_path: Annotated[
            Path,
            m.Field(description="Resolved Python module path"),
        ]
        relative_path: Annotated[
            Path,
            m.Field(description="Module path relative to its package directory"),
        ]
        module_name: Annotated[
            str,
            m.Field(description="Fully-qualified module name"),
        ]
        package_name: Annotated[
            str,
            m.Field(description="Importable package name for the module"),
        ]
        package_dir: Annotated[
            Path,
            m.Field(description="Resolved package directory containing the module"),
        ]
        package_context: Annotated[
            FlextInfraModelsCodegen.LazyInitPackageContext,
            m.Field(description="Resolved lazy-init package context for the module"),
        ]
        module_policy: Annotated[
            FlextInfraModelsCodegen.NamespaceModulePolicy,
            m.Field(description="Canonical module policy derived for the module"),
        ]
        project_layout: Annotated[
            FlextInfraModelsRope.RopeProjectLayout | None,
            m.Field(
                description="Resolved project layout, when the module belongs to one",
            ),
        ] = None

    class RopeWorkspaceSession(m.ContractModel):
        """Public Rope workspace snapshot used by the service DSL."""

        workspace_root: Annotated[
            Path,
            m.Field(description="Resolved workspace root requested by the caller"),
        ]
        rope_workspace_root: Annotated[
            Path,
            m.Field(description="Canonical root used to open the shared Rope project"),
        ]
        project_prefix: Annotated[
            str,
            m.Field(description="Project prefix passed to the Rope bootstrap"),
        ]
        src_dir: Annotated[
            str,
            m.Field(description="Primary source directory hint for Rope bootstrap"),
        ]
        ignored_resources: Annotated[
            tuple[str, ...],
            m.Field(description="Ignored Rope resource patterns"),
        ] = ()
        workspace_index: Annotated[
            FlextInfraModelsRope.RopeWorkspaceIndex,
            m.Field(description="Materialized workspace index for the open session"),
        ]


__all__: list[str] = ["FlextInfraModelsRope"]
