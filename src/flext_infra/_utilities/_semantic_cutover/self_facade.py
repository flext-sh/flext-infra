"""Bind elected self-facade calls to their declared utility owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from flext_infra import c, config, m
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)
from flext_infra._utilities._semantic_cutover.facade_bases import (
    FlextInfraUtilitiesSemanticCutoverFacadeBases,
)
from flext_infra._utilities.import_law import FlextInfraUtilitiesImportLaw
from flext_infra._utilities.project_discovery import FlextInfraUtilitiesProjectDiscovery

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
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        selected: dict[Path, set[str]] = {}
        declarations: dict[Path, set[str]] = {}
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        for path, source in sources.items():
            project = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                root, path
            )
            if project is None:
                continue
            namespace = FlextInfraUtilitiesImportLaw.import_namespace(project, path)
            if namespace is None:
                continue
            layer = FlextInfraUtilitiesImportLaw.module_import_layer(namespace[1])
            imported_modules = {
                node.module
                for node in ast.parse(source, filename=str(path)).body
                if isinstance(node, ast.ImportFrom)
                and node.module
                and not node.level
                and any(alias.name == c.Infra.FacadeFamily.U for alias in node.names)
            }
            if layer == order.index(c.Infra.FacadeFamily.U):
                own_modules = imported_modules.intersection({namespace[0].name})
                if own_modules:
                    selected[path.resolve()] = own_modules
            elif layer <= order.index(c.Infra.FacadeFamily.M):
                external_modules = imported_modules.difference({namespace[0].name})
                if external_modules:
                    declarations[path.resolve()] = external_modules
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
                and node.module in selected.get(path, set())
                and not node.level
                for alias in node.names
                if alias.name == c.Infra.FacadeFamily.U
            )
            eligible = frozenset(
                (node.module, alias.name)
                for node in ast.parse(source, filename=str(path)).body
                if isinstance(node, ast.ImportFrom)
                and node.module in declarations.get(path, set())
                and not node.level
                for alias in node.names
                if alias.name == c.Infra.FacadeFamily.U
            )
            if not (elected or eligible):
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
                    declaration_imports=eligible,
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
                item
                for item in cls._editable_sources(sources)
                if item[0] in selected or item[0] in declarations
            ),
            rewrite,
        )


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverSelfFacade"]
