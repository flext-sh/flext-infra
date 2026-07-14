"""Canonical generated package artifact selection."""

from __future__ import annotations

from flext_infra import m
from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)


# mro-wkii.17.26 (codex): Public roots are lazy; every internal package is static.
class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the package's canonical initializer form."""
        if cls._is_public_api_root_namespace(plan.context.current_pkg):
            return cls._render_root(plan)
        return cls._render_static(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
