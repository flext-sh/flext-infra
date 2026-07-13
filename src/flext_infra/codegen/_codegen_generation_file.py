"""Canonical generated package artifact selection."""

from __future__ import annotations

from flext_infra import m
from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)


# mro-i6nq.10: Every package uses one manifest-backed thin initializer contract.
class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the package's cycle-safe thin initializer."""
        return cls._render_root_thin(plan)

    @classmethod
    def render_unit_manifest(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the package's lazy-import manifest."""
        return cls._render_unit_manifest(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
