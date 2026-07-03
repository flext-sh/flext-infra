"""Rewrite bare ``print()`` calls to structured logging.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import override

from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraRefactorPrintToLogger(FlextInfraRopeTransformer):
    """Replace ``print(...)`` with ``u.fetch_logger(__name__).info(...)``.

    This is a **non-safe** fixer: it changes runtime behavior and should only
    run with ``--unsafe`` / ``safe_only=False``.
    """

    _description = "rewrite print() to structured logging"

    _PRINT_RE: re.Pattern[str] = re.compile(
        r"\bprint\s*\(\s*(?P<args>[^)]*)\s*\)",
    )

    def __init__(
        self,
        *,
        file_path: Path | None = None,
    ) -> None:
        """Initialize with optional file path for package detection."""
        super().__init__()
        self._file_path = file_path

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Rewrite print calls and ensure ``u`` import exists."""

        def replacer(match: re.Match[str]) -> str:
            args = match.group("args")
            self._record_change("Rewrote print() to u.fetch_logger(__name__).info()")
            return f"u.fetch_logger(__name__).info({args})"

        updated = self._PRINT_RE.sub(replacer, source)
        updated = self._ensure_u_import(updated)
        return updated, list(self.changes)

    def _ensure_u_import(self, source: str) -> str:
        """Add ``from <pkg> import u`` when a fetch_logger call is present."""
        if "u.fetch_logger" not in source or self._has_u_import(source):
            return source
        module_name = self._canonical_import_module()
        if not module_name:
            return source
        insertion = self._import_insertion_offset(source)
        updated = (
            f"{source[:insertion]}from {module_name} import u\n{source[insertion:]}"
        )
        self._record_change(f"Added canonical u import from {module_name}")
        return updated

    @staticmethod
    def _has_u_import(source: str) -> bool:
        """Return whether the source imports ``u``."""
        return re.search(r"\bfrom\s+\S+\s+import\s+.*\bu\b", source) is not None

    def _canonical_import_module(self) -> str:
        """Return the root package name for the file under transformation."""
        if self._file_path is None:
            return ""
        package_name: str = u.Infra.package_name(self._file_path)
        return package_name.split(".", maxsplit=1)[0]

    @staticmethod
    def _import_insertion_offset(source: str) -> int:
        """Return the byte offset after the last import line."""
        lines = source.splitlines(keepends=True)
        last_import = -1
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("from ") or stripped.startswith("import "):
                last_import = index
        if last_import == -1:
            return 0
        return sum(len(line) for line in lines[: last_import + 1])


__all__: list[str] = ["FlextInfraRefactorPrintToLogger"]
