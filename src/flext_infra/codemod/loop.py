"""Extracted facade class for loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.codemod._loop import (
    FlextInfraCodemodLoopPhaseAccessorRename,
    FlextInfraCodemodLoopPhaseDuplicateApply,
    FlextInfraCodemodLoopPhaseImportNormalization,
    FlextInfraCodemodLoopPhaseNamespaceRelocation,
)


class FlextInfraCodemodLoop(
    FlextInfraCodemodLoopPhaseAccessorRename,
    FlextInfraCodemodLoopPhaseDuplicateApply,
    FlextInfraCodemodLoopPhaseImportNormalization,
    FlextInfraCodemodLoopPhaseNamespaceRelocation,
):
    """Facade for loop."""


__all__: list[str] = ["FlextInfraCodemodLoop"]
