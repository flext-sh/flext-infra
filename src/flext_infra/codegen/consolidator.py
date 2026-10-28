"""Extracted facade class for consolidator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra.codegen._consolidator import FlextInfraCodegenConsolidatorSteps


class FlextInfraCodegenConsolidator(
    FlextInfraCodegenConsolidatorSteps,
):
    """Facade for consolidator."""


__all__: list[str] = ["FlextInfraCodegenConsolidator"]
