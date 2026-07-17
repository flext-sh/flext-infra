"""MRO base for workspace services that use FlextInfraBaseMkGenerator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_infra import m
from flext_infra.basemk.generator import FlextInfraBaseMkGenerator


class FlextInfraWorkspaceGeneratorBase(m.ArbitraryTypesModel):
    """Pydantic mixin exposing the generator field to workspace services.

    Extends ``m.ArbitraryTypesModel`` (same Pydantic root as ``FlextService``/
    ``s``) so ``generator`` is visible through MRO to both Pydantic's runtime
    metaclass and static type checkers (pyrefly/pyright).
    """

    generator: Annotated[
        FlextInfraBaseMkGenerator | None,
        m.Field(exclude=True, description="Optional custom generator service"),
    ] = None

    def _get_generator(self) -> FlextInfraBaseMkGenerator:
        """Return the configured generator."""
        return self.generator or FlextInfraBaseMkGenerator()
