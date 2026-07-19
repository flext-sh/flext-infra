"""Canonical generated package artifact selection.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, p
from flext_infra.codegen._codegen_generation_standard import (
    FlextInfraCodegenGenerationStandardMixin,
)


# mro-76mz (Sisyphus-Junior): PEP 562 belongs only to the production root;
# wrapper roots bind inherited facades eagerly before importing local modules.
class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def render_init(cls, plan: p.Infra.LazyInitPlan) -> str:
        """Render the package's canonical initializer form."""
        is_production_root = (
            plan.context.pkg_dir.parent.name == c.Infra.DEFAULT_SRC_DIR
            and cls._is_lazy_root_namespace(plan.context.current_pkg)
        )
        if is_production_root:
            return cls._render_root(plan)
        return cls._render_static(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
