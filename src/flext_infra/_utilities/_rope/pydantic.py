"""Native Pydantic facts served by Rope to the census.

The methods read Rope's semantic model only: class scopes and superclasses for
bases, and the source-binding type hints for literals. Preset identities come
from the live model facade, so no role table is duplicated here.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from pathlib import Path

from flext_infra import c, m, p
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope._analysis import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)


class FlextInfraUtilitiesRopePydantic:
    """Serve the exact Pydantic facts the census classifies."""

    @staticmethod
    def class_bases(
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
    ) -> Mapping[str, str]:
        """Read the first declared superclass of every class in one module.

        Returns:
            Class names mapped to their first native superclass short name.

        """
        pending = list(
            FlextInfraUtilitiesRopePydantic
            ._module(workspace, path)
            .get_scope()
            .get_scopes()
        )
        bases: dict[str, str] = {}
        while pending:
            scope = pending.pop()
            value = scope.pyobject
            if scope.get_kind() == "Class" and FlextInfraUtilitiesRopeRuntime.py_class(
                value
            ):
                pending.extend(scope.get_scopes())
                bases[value.get_name()] = FlextInfraUtilitiesRopePydantic._first_base(
                    value
                )
        return bases

    @staticmethod
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
    def literals(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
    ) -> Iterator[tuple[str, tuple[str, ...], c.Infra.PydanticLiteralKind, int]]:
        """Serve every ``Literal`` annotation of one module as native facts.

        Yields:
            Owner name, values, classification and line per annotation.

        """
        scopes = [cls._module(workspace, path).get_scope()]
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
                    walked = FlextInfraUtilitiesRopeAnalysisAstHelpers
                    for node in walked.walk_ast_nodes(hint):
                        values = cls._values(node)
                        if values is not None:
                            yield name, values, cls._kind(hint, node), hint.lineno

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
    def _first_base(value: p.Infra.RopeSourceClass) -> str:
        """Read the first declared superclass short name.

        Returns:
            The superclass name, or an empty string.

        """
        modules = FlextInfraUtilitiesRopeRuntimeModules
        for base in FlextInfraUtilitiesDeclarationPayload.direct_bases(value):
            identity = modules.native_object_identity(base)
            if identity:
                return identity.rsplit("::", 1)[-1].rsplit(".", 1)[-1]
        return ""

    @staticmethod
    def _values(node: p.Infra.RopeAstNode) -> tuple[str, ...] | None:
        """Read one ``Literal[...]`` value set from a native node.

        Returns:
            The literal values, or ``None`` when the node is not a literal.

        """
        if (
            FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node) != "Subscript"
            or FlextInfraUtilitiesRopePydantic._name(getattr(node, "value", node))
            != c.Infra.PYDANTIC_LITERAL_NAME
        ):
            return None
        return tuple(
            str(element.value)
            for element in getattr(getattr(node, "slice", None), "elts", ())
            if FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(element)
            == "Constant"
        )

    @staticmethod
    def _kind(
        hint: p.Infra.RopeAstNode, node: p.Infra.RopeAstNode
    ) -> c.Infra.PydanticLiteralKind:
        """Classify one literal from its native annotation shape.

        Returns:
            Full domain, subset or discriminator.

        """
        if hint is node:
            return c.Infra.PydanticLiteralKind.FULL_DOMAIN
        if FlextInfraUtilitiesRopePydantic._name(getattr(hint, "value", hint)) == (
            c.Infra.PYDANTIC_ANNOTATED_NAME
        ):
            members = getattr(getattr(hint, "slice", None), "elts", ())
            first = getattr(members[0], "value", members[0]) if members else None
            if FlextInfraUtilitiesRopePydantic._name(first) == (
                c.Infra.PYDANTIC_UNION_NAME
            ):
                return c.Infra.PydanticLiteralKind.DISCRIMINATOR
        return c.Infra.PydanticLiteralKind.SUBSET

    @staticmethod
    def _name(node: p.AttributeProbe | None) -> str:
        """Read the trailing identifier of one native expression node.

        Returns:
            The trailing name, or an empty string.

        """
        return getattr(node, "id", None) or getattr(node, "attr", None) or ""


__all__: list[str] = ["FlextInfraUtilitiesRopePydantic"]
