"""Shared edit plumbing for every semantic ``make mod`` cutover planner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t
from flext_infra._utilities import FlextInfraUtilitiesCodegenFacades

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from flext_infra import p


class FlextInfraUtilitiesSemanticCutoverEdits:
    """Turn per-module rewrites into edits while keeping every module failure."""

    @staticmethod
    @contextmanager
    def _semantic_source_project(
        project: p.Infra.RopeProject,
    ) -> Generator[p.Infra.RopeProject]:
        """Borrow original authority, or capture it independently of the mutable SDK.

        Yields:
            The existing authenticated source owner for this semantic phase.

        """
        if project.authenticated_sources:
            with project.source_consumer() as source_project:
                yield source_project
        else:
            with FlextInfraUtilitiesCodegenFacades.facade_source_project(
                Path(project.root.real_path)
            ) as (source_project, _, _):
                yield source_project

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
        *,
        source_project: p.Infra.RopeProject | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan one edit per module, preserving the first original exception.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for path, source in items:
            with (
                source_project.source_consumption()
                if source_project is not None
                else nullcontext()
            ) as consumption:
                updated, changes = rewrite(path, source)
            if updated != source:
                edits.append(
                    m.Infra.SemanticMigrationEdit(
                        file_path=path,
                        original_source=source,
                        updated_source=updated,
                        source_states=(
                            consumption.receipt().inputs
                            if consumption is not None
                            else ()
                        ),
                        changes=tuple(changes),
                    ),
                )
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(edits))

    @classmethod
    def _semantic_checked_edits(
        cls,
        items: t.SequenceOf[t.Pair[Path, str]],
        rewrite: Callable[[Path, str], t.Infra.TransformResult],
        *,
        source_project: p.Infra.RopeProject,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Keep declarative validation failures on their typed result boundary.

        Returns:
            Complete edits or the first original validation exception.

        """
        try:
            return cls._semantic_edits(items, rewrite, source_project=source_project)
        except ValueError as exc:
            return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].fail(
                str(exc), exception=exc
            )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverEdits"]
