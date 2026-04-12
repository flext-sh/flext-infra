"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated

from pydantic import Field

from flext_core import m
from flext_infra import t
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class ClassInfo(
        FlextInfraModelsMixins.PositiveLineMixin,
        m.ContractModel,
    ):
        """Semantic class info from rope — name, line, bases in one shot."""

        name: Annotated[str, Field(description="Class name")]
        bases: Annotated[
            tuple[str, ...], Field(default=(), description="Base class names")
        ]

    class ConstantInfo(
        FlextInfraModelsMixins.NonNegativeLineMixin,
        FlextInfraModelsMixins.NestedClassPathMixin,
        m.ContractModel,
    ):
        """Final-annotated constant definition from rope semantic analysis."""

        name: Annotated[str, Field(description="Constant name")]
        annotation: Annotated[
            str, Field(default="", description="Type annotation text")
        ]
        value: Annotated[str, Field(default="", description="Value representation")]

    class SymbolInfo(
        FlextInfraModelsMixins.NonNegativeLineMixin,
        m.ContractModel,
    ):
        """Top-level symbol metadata from rope semantic analysis."""

        name: Annotated[str, Field(description="Symbol name")]
        kind: Annotated[
            str, Field(description="Symbol kind: class, function, assignment")
        ]

    class ModuleSemanticState(m.ContractModel):
        """Unified semantic snapshot for one Rope module analysis pass."""

        class_infos: Annotated[
            tuple[FlextInfraModelsRope.ClassInfo, ...],
            Field(default=(), description="Local classes discovered in the module"),
        ] = ()
        declared_imports: Annotated[
            t.StrMapping,
            Field(default_factory=dict, description="Declared import targets by name"),
        ]
        semantic_imports: Annotated[
            t.StrMapping,
            Field(default_factory=dict, description="Resolved import targets by name"),
        ]

    class RopeModuleIndexEntry(m.ContractModel):
        """Generic Rope-backed index entry for one Python module resource."""

        file_path: Annotated[Path, Field(description="Absolute filesystem path")]
        resource_path: Annotated[
            str,
            Field(description="Rope resource path relative to the project root"),
        ]
        module_name: Annotated[
            str,
            Field(description="Fully-qualified Rope module name for this file"),
        ]
        package_name: Annotated[
            str,
            Field(
                description="Importable package resolved for the containing directory"
            ),
        ]
        package_dir: Annotated[
            Path,
            Field(description="Absolute package directory for this module"),
        ]
        project_root: Annotated[
            Path | None,
            Field(
                default=None,
                description="Owning project root resolved from the Rope source folder",
            ),
        ]
        is_package_init: Annotated[
            bool,
            Field(
                default=False,
                description="Whether this resource is the package __init__.py",
            ),
        ]

    class RopePackageIndexEntry(m.ContractModel):
        """Generic Rope-backed package aggregation entry."""

        package_dir: Annotated[
            Path,
            Field(description="Absolute package directory represented by this entry"),
        ]
        init_path: Annotated[
            Path,
            Field(description="Expected __init__.py path for this package directory"),
        ]
        package_name: Annotated[
            str,
            Field(description="Importable package name, or empty when non-importable"),
        ]
        project_root: Annotated[
            Path | None,
            Field(
                default=None,
                description="Owning project root resolved for this package directory",
            ),
        ]
        modules: Annotated[
            tuple[FlextInfraModelsRope.RopeModuleIndexEntry, ...],
            Field(
                default=(),
                description="Direct Python module resources that belong to this package",
            ),
        ] = ()
        direct_child_dirs: Annotated[
            tuple[Path, ...],
            Field(
                default=(),
                description="Direct child package directories discovered from Rope",
            ),
        ] = ()
        descendant_child_dirs: Annotated[
            tuple[Path, ...],
            Field(
                default=(),
                description="All descendant package directories discovered from Rope",
            ),
        ] = ()

    class RopeWorkspaceIndex(m.ContractModel):
        """Generic Rope-backed workspace index for package planning."""

        workspace_root: Annotated[
            Path,
            Field(description="Absolute workspace root used to open the Rope project"),
        ]
        package_dirs: Annotated[
            tuple[Path, ...],
            Field(
                default=(),
                description="All package directories discovered from Rope resources",
            ),
        ] = ()
        packages_by_dir: Annotated[
            Mapping[str, FlextInfraModelsRope.RopePackageIndexEntry],
            Field(
                default_factory=dict,
                description="Package entries keyed by absolute directory path",
            ),
        ]
        modules_by_path: Annotated[
            Mapping[str, FlextInfraModelsRope.RopeModuleIndexEntry],
            Field(
                default_factory=dict,
                description="Module entries keyed by absolute file path",
            ),
        ]
        package_dir_by_name: Annotated[
            Mapping[str, Path],
            Field(
                default_factory=dict,
                description="Importable package directory keyed by package name",
            ),
        ]
        project_package_by_root: Annotated[
            Mapping[str, str],
            Field(
                default_factory=dict,
                description="Canonical source package name keyed by project root path",
            ),
        ]

    class RopeWorkspaceSession(m.ContractModel):
        """Public Rope workspace snapshot used by the service DSL."""

        workspace_root: Annotated[
            Path,
            Field(description="Resolved workspace root requested by the caller"),
        ]
        rope_workspace_root: Annotated[
            Path,
            Field(description="Canonical root used to open the shared Rope project"),
        ]
        project_prefix: Annotated[
            str,
            Field(description="Project prefix passed to the Rope bootstrap"),
        ]
        src_dir: Annotated[
            str,
            Field(description="Primary source directory hint for Rope bootstrap"),
        ]
        ignored_resources: Annotated[
            tuple[str, ...],
            Field(description="Ignored Rope resource patterns"),
        ] = ()
        workspace_index: Annotated[
            FlextInfraModelsRope.RopeWorkspaceIndex,
            Field(description="Materialized workspace index for the open session"),
        ]


__all__: list[str] = ["FlextInfraModelsRope"]
