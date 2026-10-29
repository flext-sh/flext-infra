"""Extracted facade class for project.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.refactor._project import FlextInfraRefactorProjectClassifierFamily


class FlextInfraRefactorProject(
    FlextInfraRefactorProjectClassifierFamily,
):
    """Facade for project."""


__all__: list[str] = ["FlextInfraRefactorProject"]
