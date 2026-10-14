"""Resolve declaration roles through Rope scopes, ancestry and native matching.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesRopeRuntimeRefactors,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)


class FlextInfraUtilitiesDeclarationPayload:
    """Identify inherited declarations without parsing or spelling heuristics."""

    @staticmethod
    def _class_ancestry(
        value: p.Infra.RopePyObject,
    ) -> t.SequenceOf[p.Infra.RopePyObject]:
        pending = [value]
        found: list[p.Infra.RopePyObject] = []
        while pending:
            current = pending.pop()
            if current in found:
                continue
            found.append(current)
            if FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(current):
                pending.extend(current.get_superclasses())
        return found

    @classmethod
    def payload_declaration(
        cls,
        project: p.Infra.RopeProject,
        path: Path,
        qualified_name: str,
    ) -> p.Infra.RopePyName | None:
        """Resolve a data declaration, including fields inherited from a preset.

        Recognition follows the actual BaseModel identity. Relocation admission
        additionally rejects settings, class decorators and behavioral methods.
        Validators, serializers and computed fields retain their native identity.

        Args:
            project: The Rope project context for the resolution.
            path: The file path containing the declaration.
            qualified_name: The fully qualified name of the declaration.

        Returns:
            The bound model declaration, or ``None`` for a different contract.
        """
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                path.relative_to(Path(project.root.real_path)).as_posix(),
            ),
            path,
        )
        module = project.get_pymodule(resource)
        owner = module.get_attributes()
        binding: p.Infra.RopePyName | None = None
        for name in qualified_name.split("."):
            binding = owner.get(name)
            if binding is None:
                return None
            owner = binding.get_object().get_attributes()
        if binding is None:
            return None
        value = binding.get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.abstract_class(value):
            return None
        ancestry = cls._class_ancestry(value)
        base = project.get_module("pydantic").get_attribute("BaseModel").get_object()
        settings = (
            project
            .get_module("pydantic_settings")
            .get_attribute("BaseSettings")
            .get_object()
        )
        if base not in ancestry or settings in ancestry:
            return None
        scope = value.get_scope()
        if scope is None:
            return None
        statements = FlextInfraUtilitiesRopeStructure.logical_statements(
            module.source_code,
        )
        begin, _end = scope.get_region()
        if any(
            begin < statement.end_offset and statement.line < scope.get_start()
            for statement in statements
        ):
            return None
        if not cls._payload_body(value, scope, statements):
            return None
        finder = FlextInfraUtilitiesRopeRuntimeRefactors.semantic_finder(module)
        for member in scope.get_defined_names().values():
            method = member.get_object()
            if FlextInfraUtilitiesRopeRuntimeTypes.py_function(
                method
            ) and not cls._payload_method(finder, method, statements):
                return None
        return binding

    @staticmethod
    def _payload_body(
        value: p.Infra.RopePyObject,
        scope: p.Infra.RopeScope,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> bool:
        """Reject class-body behavior using the existing Rope statement boundary.

        Returns:
            Whether the class body contains only declaration statements.
        """
        return all(
            statement.category
            in {
                c.Infra.StatementCategory.ANN_ASSIGN,
                c.Infra.StatementCategory.ASSIGN,
                c.Infra.StatementCategory.FUNC_DEF,
            }
            or statement.text.strip() == "pass"
            or statement.text.lstrip().startswith("@")
            or (
                statement.line == scope.get_body_start() and value.get_doc() is not None
            )
            for statement in statements
            if scope.get_start() < statement.line <= scope.get_end()
            and statement.enclosing_kind == c.Infra.RopeScopeKind.CLASS
            and statement.enclosing_name == value.get_name()
        )

    @staticmethod
    def _payload_method(
        finder: p.Infra.RopeSimilarFinder,
        method: p.Infra.RopePyObject,
        statements: t.SequenceOf[m.Infra.LogicalStatement],
    ) -> bool:
        """Admit only native declaration decorators in Rope's header region.

        Returns:
            Whether every decorator is allowed and one belongs to Pydantic.
        """
        scope = method.get_scope()
        if scope is None:
            return False
        begin, _end = scope.get_region()
        known = False
        for statement in statements:
            if not (
                begin < statement.end_offset and statement.line < scope.get_start()
            ):
                continue
            identities = tuple(
                identity
                for identity in (
                    *c.Infra.PYDANTIC_PAYLOAD_DECORATORS,
                    *c.Infra.PAYLOAD_DESCRIPTOR_DECORATORS,
                )
                if tuple(
                    finder.get_match_regions(
                        "${decorator}",
                        {"decorator": f"name={identity}"},
                        start=statement.start_offset,
                        end=statement.end_offset,
                    )
                )
            )
            if not identities:
                return False
            known |= any(
                identity in c.Infra.PYDANTIC_PAYLOAD_DECORATORS
                for identity in identities
            )
        return known


__all__: list[str] = ["FlextInfraUtilitiesDeclarationPayload"]
