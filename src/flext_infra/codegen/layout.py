"""Extracted facade class for layout.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_infra.codegen._layout import (
    FlextInfraCodegenLayoutApply,
    FlextInfraCodegenLayoutPlan,
)


class FlextInfraCodegenLayout(
    FlextInfraCodegenLayoutApply,
    FlextInfraCodegenLayoutPlan,
):
    """Facade for layout."""

    def check_project(self, project_dir: Path) -> m.Infra.LayoutProjectReport:
        """Report layout violations for one project without writing.

        Returns:
            The resulting ``m.Infra.LayoutProjectReport``.

        """
        return self.plan_project(project_dir)


__all__: list[str] = ["FlextInfraCodegenLayout"]
