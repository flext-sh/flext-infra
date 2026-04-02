"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from flext_core import FlextModels


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class ClassInfo(FlextModels.FrozenStrictModel):
        """Semantic class info from rope — name, line, bases in one shot."""

        name: Annotated[str, Field(description="Class name")]
        line: Annotated[int, Field(description="Definition line number")]
        bases: Annotated[
            tuple[str, ...], Field(default=(), description="Base class names")
        ]

    class ConstantInfo(FlextModels.FrozenStrictModel):
        """Final-annotated constant definition from rope semantic analysis."""

        name: Annotated[str, Field(description="Constant name")]
        annotation: Annotated[
            str, Field(default="", description="Type annotation text")
        ]
        line: Annotated[int, Field(default=0, description="Definition line number")]
        value: Annotated[str, Field(default="", description="Value representation")]
        class_path: Annotated[
            str, Field(default="", description="Enclosing class dotted path")
        ]

    class SymbolInfo(FlextModels.FrozenStrictModel):
        """Top-level symbol metadata from rope semantic analysis."""

        name: Annotated[str, Field(description="Symbol name")]
        kind: Annotated[
            str, Field(description="Symbol kind: class, function, assignment")
        ]
        line: Annotated[int, Field(default=0, description="Definition line number")]


__all__ = ["FlextInfraModelsRope"]
