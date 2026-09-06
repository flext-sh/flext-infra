"""Concrete-syntax ownership moves for automatic class nesting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from flext_infra._utilities.class_nesting_references import (
    FlextInfraUtilitiesClassNestingReferences,
)

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesClassNestingCst(FlextInfraUtilitiesClassNestingReferences):
    """Move proven top-level class nodes under one existing owner class."""

    @classmethod
    def rewrite_class_nesting_source(
        cls,
        source: str,
        *,
        module_name: str,
        is_package_init: bool,
        bindings_by_module: t.MappingKV[str, t.StrMapping],
        definitions: t.StrMapping,
    ) -> str:
        """Return a binding-proven structural rewrite without filesystem effects."""
        rewritten = cls.rewrite_class_nesting_references(
            source,
            module_name=module_name,
            is_package_init=is_package_init,
            bindings_by_module=bindings_by_module,
            definitions=definitions,
        )
        return cls._nest_definitions(rewritten, definitions)

    @staticmethod
    def _nest_definitions(source: str, definitions: t.StrMapping) -> str:
        if not definitions:
            return source
        owners = frozenset(definitions.values())
        if len(owners) != 1:
            msg = f"class-nesting file has multiple owners: {sorted(owners)}"
            raise ValueError(msg)
        owner_name = next(iter(owners))
        module = cst.parse_module(source)
        owner_nodes = tuple(
            node
            for node in module.body
            if isinstance(node, cst.ClassDef) and node.name.value == owner_name
        )
        extras = {
            node.name.value: node
            for node in module.body
            if isinstance(node, cst.ClassDef) and node.name.value in definitions
        }
        if len(owner_nodes) != 1 or set(extras) != set(definitions):
            msg = (
                f"class-nesting structure mismatch for {owner_name}: "
                f"owner_count={len(owner_nodes)} extras={sorted(extras)}"
            )
            raise ValueError(msg)
        owner = owner_nodes[0]
        nested = tuple(
            extras[name].with_changes(leading_lines=(cst.EmptyLine(),))
            for name in definitions
        )
        if isinstance(owner.body, cst.IndentedBlock):
            existing = owner.body.body
            if (
                len(existing) == 1
                and isinstance(existing[0], cst.SimpleStatementLine)
                and len(existing[0].body) == 1
                and isinstance(existing[0].body[0], cst.Pass)
            ):
                existing = ()
            body = owner.body.with_changes(body=(*existing, *nested))
        else:
            statements = tuple(
                statement
                for statement in owner.body.body
                if not isinstance(statement, cst.Pass)
            )
            existing_lines = (
                (cst.SimpleStatementLine(body=statements),) if statements else ()
            )
            body = cst.IndentedBlock(body=(*existing_lines, *nested))
        nested_owner = owner.with_changes(body=body)
        return module.with_changes(
            body=tuple(
                nested_owner if node is owner else node
                for node in module.body
                if not (
                    isinstance(node, cst.ClassDef) and node.name.value in definitions
                )
            )
        ).code


__all__: list[str] = ["FlextInfraUtilitiesClassNestingCst"]
