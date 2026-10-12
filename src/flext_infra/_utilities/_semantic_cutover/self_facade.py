"""Bind elected self-facade calls to their declared utility owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra import c, m
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)
from flext_infra._utilities._semantic_cutover.facade_bases import (
    FlextInfraUtilitiesSemanticCutoverFacadeBases,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraUtilitiesSemanticCutoverSelfFacade(
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Reuse declared behavior discovery without delaying imports."""

    @classmethod
    def _plan_self_facade_imports(
        cls,
        root: Path,
        sources: t.MappingKV[Path, str],
        findings: t.SequenceOf[m.Infra.ModScanFinding],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        selected = {
            (root / finding.file).resolve(): {
                declaration.module
                for candidate in findings
                if candidate.file == finding.file
                and isinstance(
                    declaration := cls._finding_statement(candidate),
                    ast.ImportFrom,
                )
                and declaration.module
            }
            for finding in findings
        }
        behavior = FlextInfraUtilitiesSemanticCutoverFacadeBases
        typing_directory = (
            FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                c.Infra.TYPINGS_PY,
            ).directory
        )

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            elected = frozenset(
                (node.module, alias.name)
                for node in ast.parse(source, filename=str(path)).body
                if isinstance(node, ast.ImportFrom)
                and node.module
                and node.module in selected[path]
                and not node.level
                for alias in node.names
                if alias.name == c.Infra.FacadeFamily.U
            )
            if not elected:
                return source, ()
            modules = behavior.behavior_source_modules(sources, typing_directory)
            ownership = behavior.behavior_utility_owners(
                modules,
                FlextInfraUtilitiesCodegenNamespace.facade_family_declared_by(
                    c.Infra.UTILITIES_PY,
                ).directory,
            )
            updated, changes = behavior.rewrite_behavior_consumer(
                m.Infra.SemanticBehaviorRewriteRequest(
                    path=path,
                    source=source,
                    modules=modules,
                    ownership=ownership,
                    utility_imports=elected,
                ),
            )
            for node in ast.parse(updated, filename=str(path)).body:
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and any(
                        (node.module, alias.name) in elected for alias in node.names
                    )
                ):
                    msg = (
                        f"self-facade reference has no declared callable binding: "
                        f"{path}"
                    )
                    raise ValueError(msg)
            return updated, changes

        return cls._semantic_edits(
            tuple(
                item for item in cls._editable_sources(sources) if item[0] in selected
            ),
            rewrite,
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverSelfFacade"]
