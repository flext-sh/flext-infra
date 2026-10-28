"""Conservative semantic migration binding discovery over the rope owner.

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

from flext_infra._utilities._rope.rope_bindings import (
    FlextInfraUtilitiesRopeAstBindings,
)


class FlextInfraUtilitiesSemanticCutoverBindings(FlextInfraUtilitiesRopeAstBindings):
    """Enumerate language bindings without guessing their runtime values."""


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverBindings"]
