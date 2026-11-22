"""Detection constants for the codegen package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_core import c


class FlextInfraConstantsCodegenDetection:
    """Constant detection policy for codegen."""

    DETECTION_MIN_QUOTED_LITERAL_LEN: ClassVar[int] = 2
    "Minimum length for a quoted string to be considered a literal."
    DETECTION_TRIVIAL_VALUES: ClassVar[frozenset[str]] = frozenset({
        "True",
        "False",
        "None",
        c.ParserBooleanToken.ZERO,
        c.ParserBooleanToken.ONE,
        "2",
        "3",
        "4",
        "5",
        "-1",
        '""',
        "''",
        "[]",
        "{}",
        "()",
    })
    "Literal values considered trivial for constant detection heuristics."


__all__: list[str] = ["FlextInfraConstantsCodegenDetection"]
