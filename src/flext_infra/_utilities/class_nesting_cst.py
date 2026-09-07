"""Concrete-syntax ownership moves for automatic class nesting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from .._utilities.class_nesting_references import (
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

    @classmethod
    def _nest_definitions(cls, source: str, definitions: t.StrMapping) -> str:
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
            # A moved class was defined before the owner at module level, so a
            # class body member may already use it as a definition-time base.
            # Appending would place the definition after that use and break
            # import; the docstring keeps position and the moves lead the rest.
            docstring, remainder = cls._split_docstring(existing)
            body = owner.body.with_changes(body=(*docstring, *nested, *remainder))
        elif isinstance(owner.body, cst.SimpleStatementSuite):
            # A simple suite can only hold small statements; narrow before
            # promoting the remaining ones into an IndentedBlock line.
            statements = tuple(
                statement
                for statement in owner.body.body
                if not isinstance(statement, cst.Pass)
            )
            existing_lines = (
                (cst.SimpleStatementLine(body=statements),) if statements else ()
            )
            docstring, remainder = cls._split_docstring(existing_lines)
            body = cst.IndentedBlock(body=(*docstring, *nested, *remainder))
        else:
            msg = (
                f"unsupported class body for {owner_name}: {type(owner.body).__name__}"
            )
            raise TypeError(msg)
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

    @staticmethod
    def _split_docstring(
        body: t.SequenceOf[cst.BaseStatement],
    ) -> tuple[tuple[cst.BaseStatement, ...], tuple[cst.BaseStatement, ...]]:
        """Split one class body into its leading docstring and the remainder."""
        if not body:
            return ((), ())
        head = body[0]
        if (
            isinstance(head, cst.SimpleStatementLine)
            and len(head.body) == 1
            and isinstance(head.body[0], cst.Expr)
            and isinstance(
                head.body[0].value, cst.SimpleString | cst.ConcatenatedString
            )
        ):
            return ((head,), tuple(body[1:]))
        return ((), tuple(body))


__all__: list[str] = ["FlextInfraUtilitiesClassNestingCst"]
