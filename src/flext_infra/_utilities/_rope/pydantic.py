"""Native Pydantic facts served by Rope to the census.

Class declarations and literals come from Rope's source-scan and binding
owners; presets come from the live model facade. No source text is parsed here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from functools import cache
from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeRuntime
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)


class FlextInfraUtilitiesRopePydantic:
    """Serve the exact Pydantic facts the census classifies."""

    @classmethod
    def class_facts(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
    ) -> t.Infra.PydanticClassFacts:
        """Read every class's declared base and line through the native scan.

        Returns:
            Class names mapped to their first base name and logical line.

        """
        module = cls._module(workspace, path)
        return {
            name: (bases[0] if bases else "", line)
            for name, bases, line in (
                FlextInfraUtilitiesRopeAnalysisSourceScan.module_class_base_names(
                    module.get_ast()
                )
            )
        }

    @classmethod
    def literals(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
    ) -> Iterator[t.Infra.PydanticLiteralFact]:
        """Serve every ``Literal`` annotation of one module as native facts.

        Yields:
            Owner name, values, classification and line per annotation.

        """
        scopes: list[p.Infra.RopeScope] = [cls._module(workspace, path).get_scope()]
        while scopes:
            scope = scopes.pop()
            scopes.extend(scope.get_scopes())
            for name, binding in scope.get_defined_names().items():
                if not FlextInfraUtilitiesRopeRuntime.assigned_name(binding):
                    continue
                for assignment in binding.assignments:
                    hint = assignment.type_hint
                    if hint is None:
                        continue
                    helper = FlextInfraUtilitiesRopeAnalysisAstHelpers
                    position = helper.line_col_range(hint)
                    if position is None:
                        continue
                    for node in helper.walk_ast_nodes(hint):
                        values = cls._values(node)
                        if values is not None:
                            yield name, values, cls._kind(hint, node), position[0]

    @staticmethod
    @cache
    def preset_names() -> frozenset[str]:
        """Read preset identities from the live model facade.

        Returns:
            Every public ``m`` class that is a concrete Pydantic model.

        """
        return frozenset(
            name
            for name in getattr(m, "__all__", ())
            if isinstance(getattr(m, name, None), type)
            and issubclass(getattr(m, name), m.BaseModel)
        )

    @classmethod
    def tier(cls, path: Path) -> str:
        """Resolve the facade tier letter of one source path.

        Returns:
            The tier letter, or an empty string outside a family directory.

        """
        return next(
            (
                cls._tiers()[part.removeprefix("_")]
                for part in path.parts
                if part.removeprefix("_") in cls._tiers()
            ),
            "",
        )

    @staticmethod
    @cache
    def _tiers() -> Mapping[str, str]:
        """Read facade tier letters from the canonical family owner.

        Returns:
            The family directory name to facade letter map.

        """
        return {
            directory: family.suffix
            for family in FlextInfraUtilitiesCodegenNamespace.facade_families().values()
            for directory in family.directories
        }

    @staticmethod
    def _module(
        workspace: p.Infra.RopeWorkspaceDsl, path: Path
    ) -> p.Infra.RopeSourceModule:
        """Resolve one admitted path to its native source module.

        Returns:
            The native source module.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        return runtime.require_source_module(
            workspace.rope_project.get_pymodule(
                runtime.file_resource_at(workspace.rope_project, path)
            )
        )

    @staticmethod
    def _values(node: p.Infra.RopeAstNode) -> t.StrTuple | None:
        """Read one ``Literal[...]`` value set from a native node.

        Returns:
            The literal values, or ``None`` when the node is not a literal.

        """
        helper = FlextInfraUtilitiesRopeAnalysisAstHelpers
        if (
            helper.node_kind(node) != c.Infra.PYDANTIC_SUBSCRIPT_KIND
            or helper.name_of(getattr(node, "value", node))
            != c.Infra.PYDANTIC_LITERAL_NAME
        ):
            return None
        return tuple(
            str(element.value)
            for element in getattr(getattr(node, "slice", None), "elts", ())
            if helper.node_kind(element) == c.Infra.PYDANTIC_CONSTANT_KIND
        )

    @staticmethod
    def _kind(
        hint: p.Infra.RopeAstNode, node: p.Infra.RopeAstNode
    ) -> c.Infra.PydanticLiteralKind:
        """Classify one literal from its native annotation shape.

        Returns:
            Full domain, subset or discriminator.

        """
        helper = FlextInfraUtilitiesRopeAnalysisAstHelpers
        if hint is node:
            return c.Infra.PydanticLiteralKind.FULL_DOMAIN
        if helper.name_of(getattr(hint, "value", hint)) == (
            c.Infra.PYDANTIC_ANNOTATED_NAME
        ):
            members = getattr(getattr(hint, "slice", None), "elts", ())
            first = getattr(members[0], "value", members[0]) if members else None
            if helper.name_of(first) == c.Infra.PYDANTIC_UNION_NAME:
                return c.Infra.PydanticLiteralKind.DISCRIMINATOR
        return c.Infra.PydanticLiteralKind.SUBSET


__all__: list[str] = ["FlextInfraUtilitiesRopePydantic"]
