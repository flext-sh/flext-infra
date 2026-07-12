"""Canonical generated package artifact selection."""

from __future__ import annotations

from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)
from flext_infra.models import m


# mro-i6nq.10: A plan has one root or eager route, never a legacy special case.
class FlextInfraCodegenGenerationFileMixin(
    FlextInfraCodegenGenerationStandardMixin,
):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the thin root initializer or an eager non-root initializer."""
        if cls._is_public_api_root_namespace(plan.context.current_pkg):
            return cls._render_root_thin(plan)
        return cls._render_eager_package(plan)

    @classmethod
    def render_unit_manifest(cls, plan: m.Infra.LazyInitPlan) -> str | None:
        """Render the project-root manifest, or None for non-root packages."""
        if not cls._is_public_api_root_namespace(plan.context.current_pkg):
            return None
        return cls._render_unit_manifest(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
