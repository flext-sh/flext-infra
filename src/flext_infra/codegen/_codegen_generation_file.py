"""Canonical generated package artifact selection."""

from __future__ import annotations

from flext_infra import m
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
        their package boundary.  Pytest fixture packages remain the explicit
        lifecycle boundary because pytest owns their registration.
        """
        if cls._is_runtime_fixture_package(plan.context.current_pkg):
            return cls._render_static(plan)
        return cls._render_root(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
