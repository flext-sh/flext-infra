"""Shared helper for injecting the canonical ``t`` typing alias import.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_infra.constants import c
from flext_infra.typings import t


class FlextInfraEnsureCanonicalTImportMixin:
    """Inject ``from <pkg> import t`` only when the alias is actually used.

    The mixin avoids the common false-positive where a substring such as
    ``result.success`` is mistaken for a use of the ``t`` alias. It also
    avoids recording a change when no import is needed.
    """

    # Match a real use of the ``t`` alias: ``t.`` as a standalone identifier.
    _T_ALIAS_USE_RE: t.Infra.RegexPattern = c.Infra.compile(r"\bt\.")
    _DEFAULT_ALIAS_MODULE: ClassVar[str] = c.Infra.PKG_CORE_UNDERSCORE

    def _ensure_t_import(
        self,
        source: str,
        module_name: str,
    ) -> tuple[str, bool]:
        """Inject ``from <module_name> import t`` if needed.

        Returns the (possibly unchanged) source and a boolean indicating whether
        an import was added. When ``module_name`` is absent, the canonical
        FLEXT core module is used.
        """
        if not self._t_alias_used(source) or self._has_t_import(source):
            return source, False
        target_module = module_name or self._DEFAULT_ALIAS_MODULE
        insertion = self._import_insertion_offset(source)
        updated = (
            f"{source[:insertion]}from {target_module} import t\n{source[insertion:]}"
        )
        return updated, True

    @classmethod
    def _t_alias_used(cls, source: str) -> bool:
        """Return whether the source contains a real use of the ``t`` alias."""
        return cls._T_ALIAS_USE_RE.search(source) is not None

    @staticmethod
    def _has_t_import(source: str) -> bool:
        """Return whether the source already imports ``t`` on one or multiple lines."""
        if c.Infra.T_IMPORT_RE.search(source) is not None:
            return True
        lines = source.splitlines()
        index = 0
        while index < len(lines):
            stripped = lines[index].strip()
            if stripped.startswith("from ") and stripped.endswith("import ("):
                index += 1
                while index < len(lines):
                    current = lines[index].strip().rstrip(",")
                    if current == ")":
                        break
                    if current == "t":
                        return True
                    index += 1
            index += 1
        return False

    @staticmethod
    def _import_insertion_offset(source: str) -> int:
        """Return the byte offset where a new import line should be inserted.

        The line is appended after the last existing import line. Callers that
        need strict import ordering should run an import organizer afterward.
        """
        last_match: t.Infra.RegexMatch | None = None
        for match in c.Infra.IMPORT_LINE_ANCHORED_RE.finditer(source):
            last_match = match
        if last_match is None:
            return 0
        matched_line = source[last_match.start() : last_match.end()]
        if matched_line.rstrip().endswith("("):
            tail = source[last_match.end() :]
            close_match = c.Infra.IMPORT_PAREN_CLOSE_RE.search(tail)
            if close_match is not None:
                close_offset: int = last_match.end() + close_match.end()
                if close_offset < len(source) and source[close_offset] == "\n":
                    close_offset += 1
                return close_offset
        line_end = source.find("\n", last_match.end())
        return len(source) if line_end == -1 else line_end + 1


__all__: list[str] = ["FlextInfraEnsureCanonicalTImportMixin"]
