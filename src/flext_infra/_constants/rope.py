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
        "venv",
        "node_modules",
        "*.pyc",
        "dist/",
        "build/",
        ".tox/",
        ".cache/",
        "__pycache__",
        ".mypy_cache",
        ".pyrefly_cache",
        ".pytest_cache",
        ".git",
    )
    "Resources rope should ignore when scanning the project tree."

    PROPERTY_DECORATORS: Final[frozenset[str]] = frozenset({
        "property",
        "cached_property",
        "computed_field",
    })
    "Decorator names that mark Python descriptors / Pydantic computed fields."


__all__: list[str] = ["FlextInfraConstantsRope"]
