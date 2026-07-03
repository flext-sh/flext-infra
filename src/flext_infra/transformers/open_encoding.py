"""Add explicit ``encoding="utf-8"`` to ``open()`` calls.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import override

from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t


class FlextInfraRefactorOpenEncoding(FlextInfraRopeTransformer):
    """Inject ``encoding="utf-8"`` into ``open()`` calls that omit it."""

    _description = "add encoding to open() calls"

    # open(<args>) where args do not contain 'encoding'.
    _OPEN_CALL_RE: re.Pattern[str] = re.compile(
        r"\bopen\s*\(\s*(?P<args>[^)]*)\s*\)",
    )

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Add encoding kwarg when missing."""

        def replacer(match: re.Match[str]) -> str:
            args = match.group("args")
            if not args or "encoding" in args:
                return match.group(0)
            self._record_change('Added encoding="utf-8" to open() call')
            return f"open({args}, encoding=\"utf-8\")"

        updated = self._OPEN_CALL_RE.sub(replacer, source)
        return updated, list(self.changes)


__all__: list[str] = ["FlextInfraRefactorOpenEncoding"]
