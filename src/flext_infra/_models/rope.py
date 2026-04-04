"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels
from flext_infra._models.mixins import FlextInfraModelsMixins


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class ClassInfo(
        FlextInfraModelsMixins.PositiveLineMixin,
        FlextModels.ContractModel,
    ):
        """Semantic class info from rope — name, line, bases in one shot."""

        name: Annotated[str, Field(description="Class name")]
        bases: Annotated[
            tuple[str, ...], Field(default=(), description="Base class names")
        ]

    class ConstantInfo(
        FlextInfraModelsMixins.NonNegativeLineMixin,
        FlextInfraModelsMixins.NestedClassPathMixin,
        FlextModels.ContractModel,
    ):
        """Final-annotated constant definition from rope semantic analysis."""

        name: Annotated[str, Field(description="Constant name")]
        annotation: Annotated[
            str, Field(default="", description="Type annotation text")
        ]
        value: Annotated[str, Field(default="", description="Value representation")]

    class SymbolInfo(
        FlextInfraModelsMixins.NonNegativeLineMixin,
        FlextModels.ContractModel,
    ):
        """Top-level symbol metadata from rope semantic analysis."""

        name: Annotated[str, Field(description="Symbol name")]
        kind: Annotated[
            str, Field(description="Symbol kind: class, function, assignment")
        ]


__all__ = ["FlextInfraModelsRope"]
