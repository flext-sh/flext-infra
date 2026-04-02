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

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[str, t.StrSequence]:
        """Add future annotations if missing. Returns (source, changes)."""
        if c.Infra.SourceCode.FUTURE_ANNOTATIONS in source:
            return source, []

        lines = source.splitlines()
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
                if stripped.endswith(doc_char) and len(stripped) > 3:
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
        if insert_idx > 0 and new_lines[insert_idx - 1].strip() != "":
            new_lines.insert(insert_idx, "")
            insert_idx += 1

        new_lines.insert(insert_idx, c.Infra.SourceCode.FUTURE_ANNOTATIONS)

        # Add blank line if needed after
        if insert_idx + 1 < len(new_lines) and new_lines[insert_idx + 1].strip() != "":
            new_lines.insert(insert_idx + 1, "")

        return "\\n".join(new_lines) + "\\n", [
            "Ensured: from __future__ import annotations"
        ]


__all__ = ["FlextInfraRefactorEnsureFutureAnnotationsRule"]
