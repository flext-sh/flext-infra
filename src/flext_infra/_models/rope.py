"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, PrivateAttr

from flext_core import m
from flext_infra import FlextInfraModelsMixins, FlextInfraProtocolsRope


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class RopeModuleImports(m.ArbitraryTypesModel):
        """Typed wrapper around rope's ModuleImports helper."""

        imports: Annotated[
            tuple[FlextInfraProtocolsRope.RopeImportStatementLike, ...],
            Field(default=(), description="Import statements discovered by Rope"),
        ]

        _module_imports: FlextInfraProtocolsRope.RopeModuleImportsLike = PrivateAttr()

        @classmethod
        def from_runtime(
            cls,
            module_imports: FlextInfraProtocolsRope.RopeModuleImportsLike,
        ) -> FlextInfraModelsRope.RopeModuleImports:
            """Build a typed wrapper from Rope's raw ModuleImports helper."""
            model = cls(imports=cls._extract_imports(module_imports))
            model._module_imports = module_imports
            return model

        def add_import(
            self,
            import_info: FlextInfraProtocolsRope.RopeImportInfoLike,
        ) -> None:
            """Append one import descriptor and refresh the typed view."""
            self._module_imports.add_import(import_info)
            self._refresh_imports()

        def remove_duplicates(self) -> None:
            """Deduplicate imports and refresh the typed view."""
            self._module_imports.remove_duplicates()
            self._refresh_imports()

        def sort_imports(self) -> None:
            """Sort imports and refresh the typed view."""
            self._module_imports.sort_imports()
            self._refresh_imports()

        def get_changed_source(self) -> str:
            """Render the updated module source from Rope."""
            return self._module_imports.get_changed_source()

        def _refresh_imports(self) -> None:
            """Sync the public typed import tuple with Rope's runtime helper."""
            self.imports = self._extract_imports(self._module_imports)

        @staticmethod
        def _extract_imports(
            module_imports: FlextInfraProtocolsRope.RopeModuleImportsLike,
        ) -> tuple[FlextInfraProtocolsRope.RopeImportStatementLike, ...]:
            """Read Rope's import statements through the typed flext-infra contract."""
            raw_imports = module_imports.imports
            resolved_imports = raw_imports() if callable(raw_imports) else raw_imports
            return tuple(resolved_imports)

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


__all__ = ["FlextInfraModelsRope"]
