"""Extracted facade class for extract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.codemod._extract import FlextInfraCodemodExtractDuplicate


class FlextInfraCodemodExtract(
    FlextInfraCodemodExtractDuplicate,
):
    """Facade for extract."""


__all__: list[str] = ["FlextInfraCodemodExtract"]
