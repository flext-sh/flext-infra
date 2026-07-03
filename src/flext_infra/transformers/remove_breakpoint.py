"""Remove ``breakpoint()`` and ``pdb.set_trace()`` debug statements.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import override

from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t


class FlextInfraRefactorRemoveBreakpoint(FlextInfraRopeTransformer):
    """Remove ``breakpoint()`` calls and ``import pdb; pdb.set_trace()``."""

    _description = "remove breakpoint and pdb.set_trace statements"

    _BREAKPOINT_RE: re.Pattern[str] = re.compile(
        r"^[ \t]*breakpoint\s*\(\s*\)\s*[;\n]",
        re.MULTILINE,
    )
    _PDB_SET_TRACE_RE: re.Pattern[str] = re.compile(
        r"^[ \t]*import\s+pdb\s*;\s*pdb\.set_trace\s*\(\s*\)\s*[;\n]",
        re.MULTILINE,
    )

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Delete debugger statements, preserving surrounding blank lines."""
        updated = self._BREAKPOINT_RE.sub(self._on_removed, source)
        updated = self._PDB_SET_TRACE_RE.sub(self._on_removed, updated)
        return updated, list(self.changes)

    def _on_removed(self, match: re.Match[str]) -> str:
        self._record_change("Removed debugger statement")
        return "\n"


__all__: list[str] = ["FlextInfraRefactorRemoveBreakpoint"]
