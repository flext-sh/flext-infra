"""Canonical Python file filtering iteration mixin.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c


class FlextInfraUtilitiesIterationCanonical:
    """Static helpers for identifying canonical Python source files."""

    @staticmethod
    def matches_canonical_python_file(path: Path) -> bool:
        """Return True only for real ``.py`` source files."""
        return (
            path.is_file()
            and path.suffix == c.Infra.EXT_PYTHON
            and path.suffixes == [c.Infra.EXT_PYTHON]
        )

    @staticmethod
    def is_ignored_python_path(
        path: Path,
        *,
        ignored_parts: frozenset[str] | None = None,
    ) -> bool:
        """Return whether a Python path lives under an ignored directory tree."""
        effective_ignored_parts = ignored_parts or c.Infra.ITERATION_EXCLUDED_PARTS
        return any(
            part in effective_ignored_parts
            or (part.startswith(".") and part not in {".", ".."})
            for part in path.parts
        )


__all__: list[str] = ["FlextInfraUtilitiesIterationCanonical"]
