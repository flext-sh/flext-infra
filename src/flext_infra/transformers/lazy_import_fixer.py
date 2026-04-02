"""Lazy import fixer transformer — rope-based implementation.

Hoists function-local imports to module top level, deduplicating against
existing imports.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from flext_infra import FlextInfraUtilitiesRope, t, u
from flext_infra.transformers._base import FlextInfraRopeTransformer


class FlextInfraRefactorLazyImportFixer(FlextInfraRopeTransformer):
    """Hoist function-local imports to module top while preserving ordering."""

    _DEF_RE = re.compile(r"^(?:def |async def |class )", re.MULTILINE)

    def transform(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
    ) -> tuple[str, Sequence[str]]:
        """Hoist function-local imports to module level."""
        source = FlextInfraUtilitiesRope.read_source(resource)
        lines = source.splitlines(keepends=True)
        existing_imports: set[str] = set()
        hoisted: list[str] = []
        kept_lines: list[str] = []
        in_body = False
        indent_depth = 0
        for line in lines:
            stripped = line.strip()
            if not in_body and self._DEF_RE.match(stripped):
                in_body = True
                indent_depth = len(line) - len(line.lstrip())
                kept_lines.append(line)
                continue
            if in_body:
                cur_indent = (
                    len(line) - len(line.lstrip()) if stripped else indent_depth + 4
                )
                if stripped and cur_indent <= indent_depth:
                    in_body = False
                elif stripped and self._is_import_line(stripped):
                    normalized = stripped.strip()
                    if normalized not in existing_imports:
                        hoisted.append(normalized + "\n")
                        existing_imports.add(normalized)
                        self._record_change(f"Hoisted lazy import: {normalized}")
                    continue
            if not in_body and self._is_import_line(stripped):
                existing_imports.add(stripped.strip())
            kept_lines.append(line)
        if not hoisted:
            return source, []
        insert_idx = u.Infra.find_import_insert_position(kept_lines)
        new_lines = kept_lines[:insert_idx] + hoisted + kept_lines[insert_idx:]
        new_source = "".join(new_lines)
        FlextInfraUtilitiesRope.write_source(
            rope_project,
            resource,
            new_source,
            description="hoist lazy imports",
        )
        return new_source, list(self.changes)

    @staticmethod
    def _is_import_line(stripped: str) -> bool:
        return stripped.startswith(("from ", "import "))


__all__ = ["FlextInfraRefactorLazyImportFixer"]
