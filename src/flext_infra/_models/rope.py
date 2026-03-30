"""Domain models for rope refactoring operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_core import FlextModels
from pydantic import Field


class FlextInfraModelsRope:
    """Rope operation result models — accessed via m.Infra.Rope.*."""

    class ClassInfo(FlextModels.FrozenStrictModel):
        """Semantic class info from rope — name, line, bases in one shot."""

        name: Annotated[str, Field(description="Class name")]
        line: Annotated[int, Field(description="Definition line number")]
        bases: Annotated[
            tuple[str, ...], Field(default=(), description="Base class names")
        ]


__all__ = ["FlextInfraModelsRope"]
