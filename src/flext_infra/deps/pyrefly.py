"""Extracted facade class for pyrefly.

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

from flext_infra.deps._pyrefly import FlextInfraDepsPyreflyFixSteps


class FlextInfraDepsPyrefly(
    FlextInfraDepsPyreflyFixSteps,
):
    """Facade for pyrefly."""


__all__: list[str] = ["FlextInfraDepsPyrefly"]
