"""Detector configuration constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final


class FlextInfraConstantsDetectors:
    """Detector constants — accessed via c.Infra.*."""

    IMPORTLIB_IMPORT_MODULE: Final[str] = "importlib.import_module"
    "Dotted name for the dynamic import helper flagged by the inline-import detector."

    CONTEXTLIB_SUPPRESS: Final[str] = "contextlib.suppress"
    "Dotted name for the failure-swallowing context manager flagged by the silent-failure detector."


__all__: list[str] = ["FlextInfraConstantsDetectors"]
