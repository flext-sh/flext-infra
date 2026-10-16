"""Public accessor warning detection for semantic migration review.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from flext_infra import c, m

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t


class FlextInfraAccessorMigrationWarningsMixin:
    """Identify loose public accessors needing manual contract review."""

    _AUTOMATED_NAMES: ClassVar[frozenset[str]] = frozenset(
        c.ENFORCEMENT_ACCESSOR_RENAMES,
    )
    _MANUAL_WARNING_REASON: ClassVar[str] = (
        "Public {prefix}-prefixed accessor: rename to canonical verb "
        "(drop the prefix or use resolve_/fetch_/build_/etc.)"
    )

    @staticmethod
    def _declared_function_name(stripped: str) -> str | None:
        """Return the function name one source line declares, when any.

        Returns:
            The declared function name.

        """
        function_prefix = ""
        if stripped.startswith("def "):
            function_prefix = "def "
        elif stripped.startswith("async def "):
            function_prefix = "async def "
        if not function_prefix:
            return None
        return (
            stripped
            .split(function_prefix, maxsplit=1)[1]
            .split("(", maxsplit=1)[0]
            .strip()
        )

    def _function_is_exempt(self, function_name: str) -> bool:
        """Determine whether a function is already covered without a warning.

        Returns:
            Whether the declared function is exempt.

        """
        return (
            function_name.startswith("_")
            or function_name in self._AUTOMATED_NAMES
            or function_name in c.ENFORCEMENT_ACCESSOR_EXTERNAL_CONTRACTS
        )

    def _collect_manual_warnings(
        self,
        py_file: Path,
        source: str,
    ) -> t.SequenceOf[m.Infra.AccessorMigrationChange]:
        """Collect public accessor warnings.

        Returns:
            The manual contract review receipts.

        """
        lines = source.splitlines()
        warnings: t.MutableSequenceOf[m.Infra.AccessorMigrationChange] = []
        scope_stack: t.MutableSequenceOf[t.Pair[str, int]] = []
        for line_index, line_text in enumerate(lines, start=1):
            stripped = line_text.lstrip()
            if not stripped or stripped.startswith("#"):
                continue
            indent = len(line_text) - len(stripped)
            while scope_stack and indent <= scope_stack[-1][1]:
                scope_stack.pop()
            if stripped.startswith("class "):
                class_name = (
                    stripped
                    .split("class ", maxsplit=1)[1]
                    .split("(", maxsplit=1)[0]
                    .split(":", maxsplit=1)[0]
                    .strip()
                )
                scope_stack.append((f"class:{class_name}", indent))
                continue
            function_name = self._declared_function_name(stripped)
            if function_name is None:
                continue
            parent_scope = scope_stack[-1][0] if scope_stack else "module"
            scope_stack.append((f"def:{function_name}", indent))
            if parent_scope.startswith("def:") or self._function_is_exempt(
                function_name,
            ):
                continue
            matched_prefix = next(
                (
                    prefix
                    for prefix in c.Infra.ACCESSOR_WARNING_PREFIXES
                    if function_name.startswith(prefix)
                ),
                None,
            )
            if matched_prefix is None:
                continue
            warnings.append(
                m.Infra.AccessorMigrationChange(
                    file=str(py_file),
                    line=line_index,
                    original_name=function_name,
                    replacement_name=function_name[len(matched_prefix) :],
                    automated=False,
                    reason=self._MANUAL_WARNING_REASON.format(
                        prefix=matched_prefix.rstrip("_"),
                    ),
                ),
            )
        return warnings


__all__: list[str] = ["FlextInfraAccessorMigrationWarningsMixin"]
