"""Canonical generated package artifact selection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m
from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)


# mro-wkii.17.26.2 (codex): only production roots are lazy; every other package is static.
class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render the package's canonical initializer form."""
        if (
            plan.context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and cls._is_lazy_root_namespace(plan.context.current_pkg)
        ):
            return cls._render_root(plan)
        return cls._render_static(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
