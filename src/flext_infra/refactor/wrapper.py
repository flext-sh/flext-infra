"""Extracted facade class for wrapper.

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

from flext_infra.refactor._wrapper import FlextInfraRefactorWrapperRewrite


class FlextInfraRefactorWrapper(
    FlextInfraRefactorWrapperRewrite,
):
    """Facade for wrapper."""


__all__: list[str] = ["FlextInfraRefactorWrapper"]
