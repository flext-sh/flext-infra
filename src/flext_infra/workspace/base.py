"""MRO base for workspace services that use FlextInfraBaseMkGenerator."""

from __future__ import annotations

from typing import Annotated

from flext_infra import FlextInfraBaseMkGenerator, m


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
