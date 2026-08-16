"""Canonical generated package artifact selection."""

from __future__ import annotations

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)


class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render a lazy facade for each importable package boundary.

        Nested packages own the same PEP 562 facade contract as the public
        root, so MRO fragments remain lazy and consistently reachable through
        their package boundary. Bootstrap and pytest fixture packages remain
        explicit side-effect-free lifecycle boundaries.
        """
        if plan.context.initializer_shape is c.Infra.LazyInitShape.STATIC:
            return cls._render_static(plan)
        return cls._render_root(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
