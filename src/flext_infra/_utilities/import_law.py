"""Canonical import-law facade over its source-owned capability parts.

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

from flext_infra._utilities._import_law.normalization import (
    FlextInfraUtilitiesImportLawNormalization,
)


class FlextInfraUtilitiesImportLaw(FlextInfraUtilitiesImportLawNormalization):
    """Compose source policy, semantic routing and import planning through MRO."""


__all__: list[str] = ["FlextInfraUtilitiesImportLaw"]
