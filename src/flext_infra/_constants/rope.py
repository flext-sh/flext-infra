"""Rope Project configuration constants.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Final


class FlextInfraConstantsRope:
    """Rope Project configuration constants — accessed via c.Infra.*."""

    ROPE_IGNORED_RESOURCES: Final[tuple[str, ...]] = (
        ".venv",
        "*.pyc",
        "dist/",
        "__pycache__",
        ".mypy_cache",
        ".git",
    )
    "Resources rope should ignore when scanning the project tree."

    ROPE_PROJECT_PREFIX: Final[str] = "flext-"
    "Prefix identifying sub-projects inside the monorepo."

    ROPE_SRC_DIR: Final[str] = "src"
    "Source directory name within each sub-project."


__all__ = ["FlextInfraConstantsRope"]
