"""Extracted facade class for fixer.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.codegen._fixer import FlextInfraCodegenFixerWorkspace


class FlextInfraCodegenFixer(
    FlextInfraCodegenFixerWorkspace,
):
    """Facade for fixer."""


__all__: list[str] = ["FlextInfraCodegenFixer"]
