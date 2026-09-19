"""Concrete-syntax ownership moves for automatic class nesting."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import libcst as cst

from .nesting_references import FlextInfraUtilitiesSemanticCutoverNestingReferences

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesSemanticCutoverNestingCst(
    FlextInfraUtilitiesSemanticCutoverNestingReferences
):
    """Move proven top-level class nodes under one existing owner class."""

    @classmethod
    def _rewrite_class_nesting_source(
        cls,
        source: str,
        *,
        module_name: str,
        is_package_init: bool,
        bindings_by_module: t.MappingKV[str, t.StrMapping],
        definitions: t.StrMapping,
    ) -> str:
        """Return a binding-proven structural rewrite without filesystem effects."""
        rewritten = cls._rewrite_class_nesting_references(
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
        if not owner_nodes:
            owner = cst.parse_statement(
                f'class {owner_name}:\n    """Canonical namespace owner."""\n'
            )
            if not isinstance(owner, cst.ClassDef):
                msg_0 = f"class-nesting could not create owner {owner_name}"
                raise TypeError(msg_0)
            index = next(
                index
                for index, node in enumerate(module.body)
                if isinstance(node, cst.ClassDef) and node.name.value in definitions
            )
            module = module.with_changes(
                body=(*module.body[:index], owner, *module.body[index:])
            )
            owner_nodes = (owner,)
        if len(owner_nodes) != 1 or set(extras) != set(definitions):
            msg = (
                f"class-nesting structure mismatch for {owner_name}: "
                f"owner_count={len(owner_nodes)} extras={sorted(extras)}"
            )
            raise ValueError(msg)
        owner = owner_nodes[0]
        nested = tuple(
            # An empty separator line carries no indentation: libcst's default
            # emits the block's indent on a blank line, which is W293 on every
            # class this mover nests.
            cls._reindented(
                extras[name].with_changes(leading_lines=(cst.EmptyLine(indent=False),)),
                module.default_indent,
            )
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
                cls._rewritten_exports(node, owner_name)
                if cls._declares_exports(node)
                else nested_owner
                if node is owner
                else node
                for node in module.body
                if not (
                    isinstance(node, cst.ClassDef) and node.name.value in definitions
                )
            )
        ).code

    @classmethod
    def _reindented(cls, node: cst.ClassDef, indent: str) -> cst.ClassDef:
        """Re-indent every multi-line string literal the moved class carries.

        Moving a class one level deeper changes the indentation of its code but
        not the bytes of its string literals: a multi-line docstring keeps its
        continuation lines and closing quotes at the old depth, which is D207
        on every class this mover nests. The literal is the only thing that has
        to be rewritten, and only after its first line.
        """
        return cst.ensure_type(node.visit(cls._StringReindenter(indent)), cst.ClassDef)

    class _StringReindenter(cst.CSTTransformer):
        """Add one indentation level to the continuation lines of a literal."""

        def __init__(self, indent: str) -> None:
            """Record the indentation unit the enclosing module declares."""
            super().__init__()
            self._indent = indent

        @override
        def leave_SimpleString(
            self, original_node: cst.SimpleString, updated_node: cst.SimpleString
        ) -> cst.SimpleString:
            """Deepen every line of a multi-line literal but the first."""
            if "\n" not in updated_node.value:
                return updated_node
            head, _, tail = updated_node.value.partition("\n")
            deepened = "\n".join(
                f"{self._indent}{line}" if line.strip() else line
                for line in tail.split("\n")
            )
            return updated_node.with_changes(value=f"{head}\n{deepened}")

    @staticmethod
    def _declares_exports(node: cst.BaseStatement) -> bool:
        """Whether one module-level statement declares ``__all__``."""
        return isinstance(node, cst.SimpleStatementLine) and any(
            isinstance(statement, cst.AnnAssign)
            and isinstance(statement.target, cst.Name)
            and statement.target.value == "__all__"
            for statement in node.body
        )

    @staticmethod
    def _rewritten_exports(
        node: cst.BaseStatement, owner_name: str
    ) -> cst.BaseStatement:
        """Rewrite the export list to the owner, keeping the node's own shape.

        Parsing a fresh statement discarded two things the original carried:
        its ``leading_lines``, so the rebuilt declaration lost the blank lines
        separating it from the preceding block (E305 on every moved module),
        and its declared annotation, so a module using a tuple annotation was
        silently rewritten to a list. Only the value changes here.
        """
        rewritten = cst.parse_statement(f'__all__ = ["{owner_name}"]\n')
        if not isinstance(node, cst.SimpleStatementLine) or not isinstance(
            rewritten, cst.SimpleStatementLine
        ):
            return rewritten
        source = rewritten.body[0]
        if not isinstance(source, cst.Assign):
            return rewritten
        body = tuple(
            statement.with_changes(value=source.value)
            if isinstance(statement, cst.AnnAssign)
            and isinstance(statement.target, cst.Name)
            and statement.target.value == "__all__"
            else statement
            for statement in node.body
        )
        return node.with_changes(body=body)

    @staticmethod
    def _split_docstring(
        body: t.SequenceOf[cst.BaseStatement],
    ) -> t.Pair[t.VariadicTuple[cst.BaseStatement], t.VariadicTuple[cst.BaseStatement]]:
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


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverNestingCst"]
