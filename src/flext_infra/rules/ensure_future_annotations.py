"""Rule ensuring future annotations import in module header.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import FlextInfraRefactorRule, c, t


class FlextInfraRefactorEnsureFutureAnnotationsRule(FlextInfraRefactorRule):
    """Ensure ``from __future__ import annotations`` exists and is properly placed."""

    _SINGLE_LINE_DOCSTRING_MIN_LENGTH = 3

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        """Ensure future annotations exists once and is placed in the header."""
        future_import = c.Infra.FUTURE_ANNOTATIONS
        lines = [line for line in source.splitlines() if line.strip() != future_import]
        insert_idx = 0
        in_docstring = False
        docstring_char = ""

        for i, line in enumerate(lines):
            stripped = line.strip()

            if in_docstring:
                if stripped.endswith(docstring_char):
                    in_docstring = False
                    insert_idx = i + 1
                continue

            if stripped.startswith(('"""', "'''")):
                doc_char = '"""' if stripped.startswith('"""') else "'''"
                # Check if it's a single-line docstring
                if (
                    stripped.endswith(doc_char)
                    and len(stripped) > self._SINGLE_LINE_DOCSTRING_MIN_LENGTH
                ):
                    insert_idx = i + 1
                    continue
                in_docstring = True
                docstring_char = doc_char
                continue

            if not stripped:
                continue

            insert_idx = i
            break  # Found first line of code

        # Keep within bounds
        insert_idx = min(insert_idx, len(lines))

        new_lines = list(lines)

        # Add blank line if needed before
        if insert_idx > 0 and new_lines[insert_idx - 1].strip():
            new_lines.insert(insert_idx, "")
            insert_idx += 1

        new_lines.insert(insert_idx, future_import)

        # Add blank line if needed after
        if insert_idx + 1 < len(new_lines) and new_lines[insert_idx + 1].strip():
            new_lines.insert(insert_idx + 1, "")

        updated = "\n".join(new_lines) + "\n"
        if updated == source:
            no_changes: list[str] = []
            return source, no_changes
        return updated, ["Ensured: from __future__ import annotations"]


__all__ = ["FlextInfraRefactorEnsureFutureAnnotationsRule"]
