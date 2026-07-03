"""Rewrite ``from typing import Dict`` usages to canonical ``t.MappingKV``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import override

from flext_infra.constants import c
from flext_infra.transformers._canonical_t_import import (
    FlextInfraEnsureCanonicalTImportMixin,
)
from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraRefactorTypingDictImport(
    FlextInfraEnsureCanonicalTImportMixin,
    FlextInfraRopeTransformer,
):
    """Remove ``from typing import Dict`` and rewrite ``Dict[K, V]`` annotations.

    Safe deterministic rewrite: every ``Dict[K, V]`` becomes ``t.MappingKV[K, V]``
    and the canonical ``t`` import is injected when needed.
    """

    _description = "rewrite from typing import Dict to t.MappingKV"

    # Matches a `from typing import ...` line that includes Dict.
    _TYPING_DICT_IMPORT_RE: re.Pattern[str] = re.compile(
        r"^from\s+typing\s+import\s+(?P<items>[^#\n]+)",
        re.MULTILINE,
    )

    # Matches Dict[...] usage (bare name, imported from typing).
    _DICT_USAGE_RE: re.Pattern[str] = re.compile(
        r"\bDict\s*\[",
    )

    def __init__(
        self,
        *,
        file_path: Path | None = None,
    ) -> None:
        """Initialize with optional file path for canonical t import resolution."""
        super().__init__()
        self._file_path = file_path

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Remove typing.Dict import, rewrite usages, ensure t import."""
        updated = self._remove_dict_import(source)
        updated = self._rewrite_dict_annotations(updated)
        if updated != source:
            added, did_add = self._ensure_t_import(
                updated,
                self._canonical_import_module(),
            )
            if did_add:
                self._record_change(
                    f"Added canonical t import from {self._canonical_import_module()}"
                )
            updated = added
        return updated, list(self.changes)

    def _remove_dict_import(self, source: str) -> str:
        """Drop ``Dict`` from ``from typing import ...`` lines."""

        def replacer(match: re.Match[str]) -> str:
            items = match.group("items")
            original_items = items.strip()
            cleaned = self._remove_dict_item(items)
            if not cleaned:
                if original_items == "Dict":
                    self._record_change("Removed from typing import Dict")
                    return ""
                return match.group(0)
            if cleaned != original_items:
                self._record_change("Removed Dict from typing import")
                return f"from typing import {cleaned}\n"
            return match.group(0)

        return self._TYPING_DICT_IMPORT_RE.sub(replacer, source)

    @staticmethod
    def _remove_dict_item(items: str) -> str:
        """Return the item list with ``Dict`` removed, or empty if nothing remains."""
        parts = [part.strip() for part in items.split(",")]
        cleaned = [part for part in parts if part and part != "Dict"]
        if not cleaned:
            return ""
        return ", ".join(cleaned)

    def _rewrite_dict_annotations(self, source: str) -> str:
        """Rewrite every ``Dict[K, V]`` occurrence to ``t.MappingKV[K, V]``."""

        def replacer(_match: re.Match[str]) -> str:
            self._record_change("Rewrote Dict[...] annotation to t.MappingKV[...]")
            return "t.MappingKV["

        return self._DICT_USAGE_RE.sub(replacer, source)

    def _canonical_import_module(self) -> str:
        """Return the root package name for the file under transformation."""
        if self._file_path is None:
            return c.Infra.PKG_CORE_UNDERSCORE
        package_name: str = u.Infra.package_name(self._file_path)
        if not package_name:
            return c.Infra.PKG_CORE_UNDERSCORE
        return package_name.split(".", maxsplit=1)[0]


__all__: list[str] = ["FlextInfraRefactorTypingDictImport"]
