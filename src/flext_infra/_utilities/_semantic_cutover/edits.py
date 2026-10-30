"""Shared edit plumbing for every semantic ``make mod`` cutover planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t

if TYPE_CHECKING:
    from collections.abc import Callable

    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverEdits:
    """Turn per-module rewrites into edits while keeping every module failure."""

    @staticmethod
    def _editable_sources(
        sources: Mapping[Path, str],
    ) -> tuple[tuple[Path, str], ...]:
        """Return resolved hand-written sources in stable path order.

        Returns:
            Resolved hand-written sources in stable path order.

        """
        return tuple(
            sorted(
                (path.resolve(), source)
                for path, source in sources.items()
                if not source.startswith(c.Infra.AUTOGEN_HEADER)
            ),
        )

    @staticmethod
    def _finding_statement(finding: m.Infra.ModOccurrence) -> ast.stmt | None:
        """Parse the single statement an ast-grep finding reports.

        Returns:
            The resulting ``ast.stmt | None``.

        """
        body = ast.parse(finding.text).body
        return body[0] if len(body) == 1 else None

    @staticmethod
    def _semantic_edits(
        items: Sequence[tuple[Path, str]],
        rewrite: Callable[[Path, str], t.Infra.TransformResult],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Plan one edit per module, preserving the first original exception.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]``.

        """
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for path, source in items:
            updated, changes = rewrite(path, source)
            if updated != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=source,
                        updated_source=updated,
                        changes=tuple(changes),
                    ),
                )
        return r[tuple[m.Infra.SemanticMigrationEdit, ...]].ok(tuple(edits))

    @classmethod
    def _semantic_checked_edits(
        cls,
        items: Sequence[tuple[Path, str]],
        rewrite: Callable[[Path, str], p.Result[t.Infra.TransformResult]],
    ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
        """Admit typed rewrites before constructing the complete coherent edits.

        Returns:
            Complete edits or the unchanged first failed Result.

        """

        def planned(
            values: Sequence[t.Infra.TransformResult],
        ) -> p.Result[tuple[m.Infra.SemanticMigrationEdit, ...]]:
            ordered = iter(values)
            return cls._semantic_edits(items, lambda _path, _source: next(ordered))

        return r.traverse(items, lambda item: rewrite(*item)).flat_map(planned)


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverEdits"]
