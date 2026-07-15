"""Canonical generated package artifact selection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)


# mro-wkii.17.26.2 (codex): each governed surface has one lazy root; only its
# descendants use eager static reexports.
class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the package's canonical initializer form."""
        is_production_root = (
            plan.context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and cls._is_lazy_root_namespace(plan.context.current_pkg)
        )
        is_wrapper_root = (
            plan.context.current_pkg == plan.context.surface
            and plan.context.surface in c.Infra.ROOT_WRAPPER_SEGMENTS
        )
        if is_production_root or is_wrapper_root:
            return cls._render_root(plan)
        return cls._render_static(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
