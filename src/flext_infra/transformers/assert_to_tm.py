"""Syntax-aware migration from Python assert statements to ``flext_tests.tm``."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

from flext_infra.transformers.base import FlextInfraRopeTransformer

if TYPE_CHECKING:
    from flext_infra import t


class _UnsupportedMessageVisitor(cst.CSTVisitor):
    """Detect expressions that cannot be moved into a synchronous lambda."""

    unsupported: bool = False

    @override
    def visit_Await(self, node: cst.Await) -> bool:
        _ = node
        self.unsupported = True
        return False

    @override
    def visit_Yield(self, node: cst.Yield) -> bool:
        _ = node
        self.unsupported = True
        return False


class _AssertInventory(cst.CSTVisitor):
    """Collect whether a module needs transformation and canonical tm import."""

    has_assert: bool = False
    has_tm_import: bool = False

    @staticmethod
    def _module_name(module: cst.BaseExpression | None) -> str | None:
        """Return a dotted import module name when statically representable."""
        if module is None:
            return None
        names: list[str] = []
        current: cst.BaseExpression = module
        while isinstance(current, cst.Attribute):
            names.append(current.attr.value)
            current = current.value
        if not isinstance(current, cst.Name):
            return None
        names.append(current.value)
        return ".".join(reversed(names))

    @override
    def visit_Assert(self, node: cst.Assert) -> bool:
        _ = node
        self.has_assert = True
        return True

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        if self._module_name(node.module) != "flext_tests":
            return True
        if isinstance(node.names, cst.ImportStar):
            return True
        self.has_tm_import = any(
            isinstance(alias.name, cst.Name)
            and alias.name.value == "tm"
            and alias.asname is None
            for alias in node.names
        )
        return True


class _AssertToTmCstTransformer(cst.CSTTransformer):
    """Rewrite assert nodes while retaining their complete condition expression."""

    METADATA_DEPENDENCIES: ClassVar[tuple[type[PositionProvider], ...]] = (
        PositionProvider,
    )

    def __init__(self, *, add_import: bool) -> None:
        self._add_import = add_import
        self._import_updated = False
        self.rewritten = 0

    @staticmethod
    def _tm_that(
        condition: cst.BaseExpression,
        *,
        message: cst.BaseExpression | None = None,
    ) -> cst.Call:
        """Build one canonical tm truth assertion."""
        args = [
            cst.Arg(condition),
            cst.Arg(cst.Name("True"), keyword=cst.Name("eq")),
        ]
        if message is not None:
            args.append(cst.Arg(message, keyword=cst.Name("msg")))
        return cst.Call(
            func=cst.Attribute(value=cst.Name("tm"), attr=cst.Name("that")),
            args=args,
        )

    @staticmethod
    def _is_static_message(message: cst.BaseExpression) -> bool:
        """Return whether eager evaluation is observationally inert."""
        return isinstance(
            message,
            (
                cst.ConcatenatedString,
                cst.Float,
                cst.Imaginary,
                cst.Integer,
                cst.SimpleString,
            ),
        ) or (
            isinstance(message, cst.Name)
            and message.value in {"False", "None", "True"}
        )

    @classmethod
    def _dynamic_message_call(
        cls, condition: cst.BaseExpression, message: cst.BaseExpression
    ) -> cst.Call:
        """Evaluate the condition once and the dynamic message only on failure."""
        parameter = "_flext_assert_condition"
        condition_name = cst.Name(parameter)
        success = cls._tm_that(condition_name)
        failure = cls._tm_that(condition_name, message=message)
        return cst.Call(
            func=cst.Lambda(
                params=cst.Parameters(params=[cst.Param(cst.Name(parameter))]),
                body=cst.IfExp(
                    test=condition_name,
                    body=success,
                    orelse=failure,
                ),
            ),
            args=[cst.Arg(condition)],
        )

    @override
    def leave_Assert(
        self, original_node: cst.Assert, updated_node: cst.Assert
    ) -> cst.BaseSmallStatement:
        message = updated_node.msg
        condition = cst.Call(
            func=cst.Name("bool"), args=[cst.Arg(updated_node.test)]
        )
        if message is None:
            call: cst.BaseExpression = self._tm_that(condition)
        elif self._is_static_message(message):
            call = self._tm_that(condition, message=message)
        else:
            unsupported = _UnsupportedMessageVisitor()
            message.visit(unsupported)
            if unsupported.unsupported:
                position = self.get_metadata(PositionProvider, original_node)
                raise SyntaxError(
                    "unsupported assert message expression at "
                    f"line {position.start.line}, column {position.start.column}"
                )
            call = self._dynamic_message_call(condition, message)
        self.rewritten += 1
        return cst.Expr(value=call, semicolon=updated_node.semicolon)

    @override
    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        _ = original_node
        if (
            not self._add_import
            or self._import_updated
            or _AssertInventory._module_name(updated_node.module) != "flext_tests"
            or isinstance(updated_node.names, cst.ImportStar)
        ):
            return updated_node
        self._import_updated = True
        return updated_node.with_changes(
            names=(*updated_node.names, cst.ImportAlias(name=cst.Name("tm")))
        )

    @override
    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        _ = original_node
        if not self._add_import or self._import_updated:
            return updated_node
        statement = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Name("flext_tests"),
                    names=[cst.ImportAlias(name=cst.Name("tm"))],
                )
            ]
        )
        insert_at = 0
        for index, body_item in enumerate(updated_node.body):
            if index != insert_at:
                break
            if not isinstance(body_item, cst.SimpleStatementLine):
                break
            if len(body_item.body) != 1:
                break
            small = body_item.body[0]
            if isinstance(small, cst.Expr) and isinstance(
                small.value, cst.SimpleString
            ):
                insert_at = index + 1
                continue
            if (
                isinstance(small, cst.ImportFrom)
                and _AssertInventory._module_name(small.module) == "__future__"
            ):
                insert_at = index + 1
                continue
            break
        body = list(updated_node.body)
        body.insert(insert_at, statement)
        self._import_updated = True
        return updated_node.with_changes(body=body)


class FlextInfraAssertToTmTransformer(FlextInfraRopeTransformer):
    """Convert Python assert statements without changing condition semantics."""

    _description = "assert-to-tm migration"

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Transform one complete Python module and return tracked changes."""
        self.changes.clear()
        try:
            module = cst.parse_module(source)
        except cst.ParserSyntaxError as exc:
            raise SyntaxError(f"cannot parse Python source: {exc}") from exc
        inventory = _AssertInventory()
        module.visit(inventory)
        if not inventory.has_assert:
            return source, ()
        transformer = _AssertToTmCstTransformer(
            add_import=not inventory.has_tm_import
        )
        transformed = MetadataWrapper(module).visit(transformer)
        for _ in range(transformer.rewritten):
            self._record_change("replace assert with canonical tm truth assertion")
        return transformed.code, tuple(self.changes)


__all__: list[str] = ["FlextInfraAssertToTmTransformer"]
