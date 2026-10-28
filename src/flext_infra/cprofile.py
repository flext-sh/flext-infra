"""Extracted facade class for cprofile.

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

from flext_infra._cprofile import FlextInfraCprofileEntry


class FlextInfraFlextInfraCprofile(
    FlextInfraCprofileEntry,
):
    """Facade for cprofile."""


__all__: list[str] = ["FlextInfraFlextInfraCprofile"]
