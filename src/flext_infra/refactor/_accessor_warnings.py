"""Public accessor warning detection for semantic migration review.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraAccessorMigrationWarningsMixin:
    """Declare the shared automated accessor rules used by migration planning."""

    _AUTOMATED_RULES: ClassVar[t.VariadicTuple[m.Infra.AccessorMigrationRule]] = tuple(
        m.Infra.AccessorMigrationRule(
            source_name=src,
            replacement_name=repl,
            reason=reason,
            origin="flext_core",
        )
        for src, (repl, reason) in c.ENFORCEMENT_ACCESSOR_RENAMES.items()
    )


__all__: list[str] = ["FlextInfraAccessorMigrationWarningsMixin"]
