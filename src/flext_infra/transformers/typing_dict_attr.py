"""Rewrite ``typing.Dict[K, V]`` annotations to canonical ``t.MappingKV``.

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


class FlextInfraRefactorTypingDictAttr(FlextInfraRopeTransformer):
    """Rewrite ``typing.Dict[K, V]`` to ``t.MappingKV[K, V]``.

    Safe deterministic rewrite for attribute-style typing references.
    The ``typing`` module import is left untouched; only the annotation form
    is canonicalized and the ``t`` import is injected when needed.
    """

    _description = "rewrite typing.Dict to t.MappingKV"

    # Matches typing.Dict[...] usage.
    _TYPING_DICT_ATTR_RE: re.Pattern[str] = re.compile(
        r"\btyping\s*\.\s*Dict\s*\[",
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
        """Rewrite typing.Dict usages and ensure t import."""
        updated = self._rewrite_dict_annotations(source)
        if updated != source:
            updated = self._ensure_t_import(updated)
        return updated, list(self.changes)

    def _rewrite_dict_annotations(self, source: str) -> str:
        """Rewrite every ``typing.Dict[K, V]`` occurrence to ``t.MappingKV[K, V]``."""

        def replacer(match: re.Match[str]) -> str:
            self._record_change(
                "Rewrote typing.Dict[...] annotation to t.MappingKV[...]"
            )
            return "t.MappingKV["

        return self._TYPING_DICT_ATTR_RE.sub(replacer, source)

    def _ensure_t_import(self, source: str) -> str:
        """Inject ``from <pkg> import t`` when ``t.`` is used without import."""
        if "t." not in source or self._has_t_import(source):
            return source
        module_name = self._canonical_import_module()
        if not module_name:
            module_name = "flext_core"
        insertion = self._import_insertion_offset(source)
        updated = (
            f"{source[:insertion]}from {module_name} import t\n{source[insertion:]}"
        )
        self._record_change(f"Added canonical t import from {module_name}")
        return updated

    def _canonical_import_module(self) -> str:
        """Return the root package name for the file under transformation."""
        if self._file_path is None:
            return ""
        package_name: str = u.Infra.package_name(self._file_path)
        return package_name.split(".", maxsplit=1)[0]

    @staticmethod
    def _has_t_import(source: str) -> bool:
        """Return whether the source already imports ``t``."""
        return (
            re.search(r"^from\s+\S+\s+import\s+.*\bt\b", source, re.MULTILINE)
            is not None
        )

    @staticmethod
    def _import_insertion_offset(source: str) -> int:
        """Return the byte offset after the last import line."""
        lines = source.splitlines(keepends=True)
        last_import = -1
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("from ", "import ")):
                last_import = index
        if last_import == -1:
            return 0
        return sum(len(line) for line in lines[: last_import + 1])


__all__: list[str] = ["FlextInfraRefactorTypingDictAttr"]
