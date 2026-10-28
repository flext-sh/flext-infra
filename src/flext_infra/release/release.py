"""Extracted facade class for release.

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

from flext_infra.release._release import FlextInfraReleaseReleasePlan


class FlextInfraReleaseRelease(
    FlextInfraReleaseReleasePlan,
):
    """Facade for release."""


__all__: list[str] = ["FlextInfraReleaseRelease"]
