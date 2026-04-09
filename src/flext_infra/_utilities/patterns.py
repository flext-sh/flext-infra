"""Consolidated regex patterns for infrastructure scripts.

Merges patterns from ``scripts/libs/patterns.py`` and
``scripts/libs/doc_patterns.py`` into a single namespace.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from typing import ClassVar, TypeIs

from flext_infra import t


class FlextInfraUtilitiesPatterns:
    """Centralized regex patterns for infrastructure operations.

    Consolidates tooling patterns (mypy, stubs) and documentation
    patterns (markdown links, headings, TOC) into a single class.
    """

    MYPY_HINT_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r'note: Hint: "python3 -m pip install ([^"]+)"',
    )
    """Match mypy install hint messages, capturing the package name."""

    MYPY_STUB_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r'Library stubs not installed for "([^"]+)"',
    )
    """Match mypy missing stub messages, capturing the library name."""

    INTERNAL_PREFIXES: ClassVar[tuple[str, ...]] = ("flext_",)
    """Prefixes identifying internal FLEXT packages."""

    MARKDOWN_LINK_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"\[([^\]]+)\]\(([^)]+)\)"
    )
    """Match markdown links capturing text (group 1) and URL (group 2)."""

    MARKDOWN_LINK_URL_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"\[[^\]]+\]\(([^)]+)\)",
    )
    """Match markdown links capturing only the URL (group 1)."""

    HEADING_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^#{1,6}\s+(.+?)\s*$",
        re.MULTILINE,
    )
    """Match any markdown heading (h1-h6), capturing the text."""

    HEADING_H2_H3_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^(##|###)\s+(.+?)\s*$",
        re.MULTILINE,
    )
    """Match h2/h3 headings, capturing level (group 1) and text (group 2)."""

    ANCHOR_LINK_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"\[([^\]]+)\]\(#([^)]+)\)"
    )
    """Match internal anchor links, capturing text and anchor."""

    INLINE_CODE_RE: ClassVar[t.Infra.RegexPattern] = re.compile(r"`[^`]*`")
    """Match inline code spans for stripping before analysis."""

    # ── Source code patterns (shared across rules/transformers/codegen) ──

    CLASS_DEF_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^class\s+(\w+)",
        re.MULTILINE,
    )
    """Match class definitions, capturing the class name."""

    FUNCTION_DEF_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^(?:async\s+)?def\s+(\w+)",
        re.MULTILINE,
    )
    """Match function/async function definitions, capturing the name."""

    FROM_IMPORT_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^from\s+([\w.]+)\s+import\s+(.+)$",
        re.MULTILINE,
    )
    """Match 'from X import Y' statements, capturing module and names."""

    IMPORT_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^import\s+([\w.]+)",
        re.MULTILINE,
    )
    """Match 'import X' statements, capturing module name."""

    ASSIGN_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^(\w+)\s*(?::\s*\S+\s*)?=",
        re.MULTILINE,
    )
    """Match module-level assignments, capturing the target name."""

    FINAL_ASSIGN_RE: ClassVar[t.Infra.RegexPattern] = re.compile(
        r"^\s+(\w+)\s*:\s*(?:Final|ClassVar\[Final)\b.*?=\s*(.+)$",
        re.MULTILINE,
    )
    """Match Final/ClassVar[Final] assignments, capturing name and value."""

    CONSTANT_NAME_RE: ClassVar[t.Infra.RegexPattern] = re.compile(r"^[A-Z][A-Z0-9_]+$")
    """Match UPPER_CASE constant naming convention."""

    @staticmethod
    def _is_str_pattern(
        value: t.Infra.RegexPattern | None,
    ) -> TypeIs[t.Infra.RegexPattern]:
        """Check if value is a compiled regex pattern.

        Args:
            value: Value to check.

        Returns:
            True if value is a compiled t.Infra.RegexPattern.

        """
        return isinstance(value, re.Pattern)

    @staticmethod
    def matches_pattern(pattern_name: str, text: str) -> bool:
        """Check if a pattern matches text.

        Dynamically retrieves a pattern class variable by name and searches
        the text against it.

        Args:
            pattern_name: Name of the pattern class variable (e.g., 'MYPY_HINT_RE').
            text: Text to match against.

        Returns:
            True if the pattern matches, False if pattern not found or no match.

        """
        pattern_obj: t.Infra.RegexPattern | None = getattr(
            FlextInfraUtilitiesPatterns,
            pattern_name,
            None,
        )
        if not FlextInfraUtilitiesPatterns._is_str_pattern(pattern_obj):
            return False
        return pattern_obj.search(text) is not None


__all__ = ["FlextInfraUtilitiesPatterns"]
