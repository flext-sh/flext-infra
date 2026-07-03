"""Inject ``from __future__ import annotations`` when missing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t


class FlextInfraRefactorFutureImport(FlextInfraRopeTransformer):
    """Ensure the leading ``from __future__ import annotations`` line exists."""

    _description = "insert from __future__ import annotations"

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Add the future import at the top when absent."""
        stripped = source.lstrip()
        if stripped.startswith("from __future__ import annotations"):
            return source, list(self.changes)
        insertion = self._insertion_offset(source)
        updated = f"{source[:insertion]}from __future__ import annotations\n{source[insertion:]}"
        self._record_change("Inserted from __future__ import annotations")
        return updated, list(self.changes)

    @staticmethod
    def _insertion_offset(source: str) -> int:
        """Return the offset after leading comments/shebang, before first code."""
        lines = source.splitlines(keepends=True)
        index = 0
        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                break
            index += 1
        return sum(len(line) for line in lines[:index])


__all__: list[str] = ["FlextInfraRefactorFutureImport"]
