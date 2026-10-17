"""Shared edit plumbing for every semantic ``make mod`` cutover planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverEdits:
    """Turn per-module rewrites into edits while keeping every module failure."""

    @staticmethod
    def _editable_sources(
        sources: t.MappingKV[Path, str],
    ) -> t.VariadicTuple[t.Pair[Path, str]]:
        """Return resolved hand-written sources in stable path order.

        Returns:
            Resolved hand-written sources in stable path order.

        """
        return tuple(
            sorted(
                (path.resolve(), source)
                for path, source in sources.items()
                if not source.startswith(c.Infra.AUTOGEN_HEADERS)
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
        items: t.SequenceOf[t.Pair[Path, str]],
        rewrite: Callable[[Path, str], t.Infra.TransformResult],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan one edit per module, preserving the first original exception.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

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
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(edits))


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverEdits"]
