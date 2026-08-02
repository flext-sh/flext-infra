"""AST-only silent-failure detection helpers.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping
from typing import NamedTuple, override


class _SilentFailureFinding(NamedTuple):
    line: int
    column: int
    kind: str
    detail: str
    fix_action: str
    replacement: tuple[int, int, str] | None = None


class _SilentFailureAstVisitor(ast.NodeVisitor):
    """AST visitor collecting exception-silencing patterns.

    Walks the rope-backed AST (``pymodule.get_ast()``).  No regex is used;
    all findings are derived from structural AST nodes.
    """

    _SENTINEL_CONSTANTS: frozenset[object] = frozenset({False, None})
    _BROAD_EXCEPTION_NAMES: frozenset[str] = frozenset({
        "Exception",
        "BaseException",
        "builtins.Exception",
        "builtins.BaseException",
    })
    _FAILURE_CALL_NAMES: frozenset[str] = frozenset({"fail", "fail_op"})
    _FAILURE_REPORT_CALL_NAMES: frozenset[str] = frozenset({
        "add",
        "append",
        "critical",
        "error",
        "exception",
        "extend",
        "warning",
    })

    def __init__(self, source: str) -> None:
        self.source = source
        self.lines = source.splitlines(keepends=True)
        self.findings: list[_SilentFailureFinding] = []
        self._import_aliases: dict[str, str] = {}
        self._parents: dict[ast.AST, ast.AST] = {}
        self._definitions: dict[
            str, list[ast.FunctionDef | ast.AsyncFunctionDef]
        ] = {}

    def analyze(self, tree: ast.Module) -> list[_SilentFailureFinding]:
        """Build parent map and walk the rope-backed module AST."""
        self._parents.clear()
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                self._parents[child] = parent
        self._import_aliases = self._collect_import_aliases(tree)
        self._definitions = self._function_definitions(tree)
        self.visit(tree)
        return self.findings

    def _enclosing_function(
        self, node: ast.AST
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        current: ast.AST | None = node
        while current is not None:
            if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
                return current
            current = self._parents.get(current)
        return None

    def _result_inner_type(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str | None:
        returns = func.returns
        if not isinstance(returns, ast.Subscript):
            return None
        value = returns.value
        is_result_shape = (
            isinstance(value, ast.Name) and value.id in {"r", "Result"}
        ) or (isinstance(value, ast.Attribute) and value.attr == "Result")
        if not is_result_shape:
            return None
        inner_type: str = ast.unparse(returns.slice)
        return inner_type

    def _line_offsets(self, lineno: int) -> tuple[int, int]:
        start = sum(len(self.lines[i]) for i in range(lineno - 1))
        end = start + len(self.lines[lineno - 1])
        return start, end

    def _indent_of(self, node: ast.Return) -> str:
        line = self.lines[node.lineno - 1]
        indent: str = line[: len(line) - len(line.lstrip())]
        return indent

    def _add_finding(
        self,
        *,
        line: int,
        column: int,
        kind: str,
        detail: str,
        fix_action: str = "manual",
        replacement: tuple[int, int, str] | None = None,
    ) -> None:
        self.findings.append(
            _SilentFailureFinding(
                line=line,
                column=column,
                kind=kind,
                detail=detail,
                fix_action=fix_action,
                replacement=replacement,
            )
        )

    @override
    def visit_Call(self, node: ast.Call) -> None:
        call_name = self._resolve_call_name(node, self._import_aliases)
        if call_name == "contextlib.suppress":
            self._add_finding(
                line=node.lineno,
                column=node.col_offset,
                kind="silent-failure-suppress",
                detail=(
                    "contextlib.suppress(...) silences exceptions without logging "
                    "or propagation"
                ),
            )
        elif self._is_unwrap_or_call(node):
            self._add_finding(
                line=node.lineno,
                column=node.col_offset,
                kind="silent-failure-unwrap-or",
                detail="unwrap_or(sentinel) hides a failure path",
            )
        self.generic_visit(node)

    @override
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if self._is_except_pass(node):
            self._add_finding(
                line=node.lineno,
                column=node.col_offset,
                kind="silent-failure-except-pass",
                detail="except handler with empty pass swallows the exception",
            )
        elif self._is_broad_unhandled_except(node):
            self._add_finding(
                line=node.lineno,
                column=node.col_offset,
                kind="silent-failure-broad-except",
                detail=(
                    "broad except catches Exception/BaseException without re-raise "
                    "or explicit typed failure propagation"
                ),
            )
        elif self._is_except_sentinel(node):
            self._add_except_sentinel_finding(node)
        self.generic_visit(node)

    @override
    def visit_If(self, node: ast.If) -> None:
        guard_info = self._guard_info(node)
        if guard_info is not None:
            result_name, _success_branch = guard_info
            self._add_guard_finding(node, result_name)
        self.generic_visit(node)

    def _is_except_pass(self, node: ast.ExceptHandler) -> bool:
        return all(
            isinstance(stmt, ast.Pass)
            or (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
            for stmt in node.body
        ) and any(isinstance(stmt, ast.Pass) for stmt in node.body)

    def _is_broad_unhandled_except(self, node: ast.ExceptHandler) -> bool:
        if self._body_has_explicit_failure(node.body, exception_name=node.name):
            return False
        return self._is_broad_exception_type(node.type)

    def _is_except_sentinel(self, node: ast.ExceptHandler) -> bool:
        if self._is_broad_exception_type(node.type):
            return False
        return not self._body_has_explicit_failure(
            node.body, exception_name=node.name
        ) and self._body_has_sentinel_return(node.body)

    def _body_has_sentinel_return(self, body: list[ast.stmt]) -> bool:
        return any(
            isinstance(node, ast.Return) and self._is_sentinel_value(node.value)
            for node in self._walk_body_nodes(body)
        )

    def _is_sentinel_value(self, node: ast.expr | None) -> bool:
        if node is None:
            return True
        if isinstance(node, ast.Constant) and node.value in self._SENTINEL_CONSTANTS:
            return True
        if isinstance(node, ast.List) and not node.elts:
            return True
        return isinstance(node, ast.Dict) and not node.keys

    def _body_has_explicit_failure(
        self, body: list[ast.stmt], *, exception_name: str | None
    ) -> bool:
        tainted = self._tainted_names(
            body, {exception_name} if exception_name is not None else set()
        )
        for child in self._walk_body_nodes(body):
            if isinstance(child, ast.Raise):
                return True
            if isinstance(child, ast.Call) and self._call_propagates_failure(
                child, tainted, visiting=frozenset()
            ):
                return True
        return False

    def _is_broad_exception_type(self, node: ast.expr | None) -> bool:
        """Return whether an exception expression explicitly catches every error."""
        if node is None:
            return True
        if isinstance(node, ast.Tuple):
            return any(self._is_broad_exception_type(item) for item in node.elts)
        if isinstance(node, ast.Starred):
            return self._is_broad_exception_type(node.value)
        type_name = self._expression_name(node, self._import_aliases)
        return type_name in self._BROAD_EXCEPTION_NAMES

    def _call_builds_failure(self, node: ast.Call) -> bool:
        """Return whether one call explicitly constructs or propagates failure."""
        call_name = self._call_leaf_name(node)
        if call_name in self._FAILURE_CALL_NAMES:
            return True
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        success = keywords.get("success")
        error = keywords.get("error")
        return (
            isinstance(success, ast.Constant)
            and success.value is False
            and error is not None
            and not (isinstance(error, ast.Constant) and error.value is None)
        )

    def _call_propagates_failure(
        self,
        node: ast.Call,
        tainted: set[str],
        *,
        visiting: frozenset[str],
    ) -> bool:
        """Return whether one call creates, raises, or records a failure."""
        if self._call_builds_failure(node):
            return self._is_return_value(node)
        if (
            self._is_return_value(node)
            and self._enclosing_function_returns_result(node)
            and self._call_arguments_reference_names(node, tainted)
        ):
            return True
        call_name = self._call_leaf_name(node)
        if call_name in self._FAILURE_REPORT_CALL_NAMES:
            return self._call_arguments_reference_names(node, tainted)
        candidates = self._definitions.get(call_name, ())
        if not candidates or call_name in visiting:
            return False
        nested_visiting = visiting | {call_name}
        return all(
            self._definition_propagates_failure(
                definition,
                self._tainted_call_parameters(definition, node, tainted),
                visiting=nested_visiting,
            )
            for definition in candidates
        )

    def _definition_propagates_failure(
        self,
        definition: ast.FunctionDef | ast.AsyncFunctionDef,
        sources: set[str],
        *,
        visiting: frozenset[str],
    ) -> bool:
        """Follow caught-error data through one local helper definition."""
        tainted = self._tainted_names(definition.body, sources)
        if any(
            isinstance(node, ast.Raise)
            for node in self._walk_body_nodes(definition.body)
        ):
            return True
        return any(
            isinstance(node, ast.Call)
            and self._call_propagates_failure(node, tainted, visiting=visiting)
            for node in self._walk_body_nodes(definition.body)
        )

    def _is_return_value(self, node: ast.Call) -> bool:
        """Return whether the call result is propagated directly to the caller."""
        parent = self._parents.get(node)
        return isinstance(parent, ast.Return) and parent.value is node

    def _enclosing_function_returns_result(self, node: ast.AST) -> bool:
        """Return whether the enclosing function promises a typed Result."""
        function = self._enclosing_function(node)
        if function is None or function.returns is None:
            return False
        annotation: ast.expr = function.returns
        if isinstance(annotation, ast.Subscript):
            annotation = annotation.value
        return (
            isinstance(annotation, ast.Name)
            and annotation.id in {"r", "Result"}
        ) or (isinstance(annotation, ast.Attribute) and annotation.attr == "Result")

    @classmethod
    def _tainted_names(cls, body: list[ast.stmt], sources: set[str]) -> set[str]:
        """Propagate exception-derived values through local assignments."""
        tainted = set(sources)
        changed = True
        while changed:
            changed = False
            for node in cls._walk_body_nodes(body):
                value: ast.expr | None = None
                targets: tuple[ast.expr, ...] = ()
                if isinstance(node, ast.Assign):
                    value = node.value
                    targets = tuple(node.targets)
                elif isinstance(node, ast.AnnAssign):
                    value = node.value
                    targets = (node.target,)
                elif isinstance(node, ast.NamedExpr):
                    value = node.value
                    targets = (node.target,)
                if value is None or not cls._node_references_names(value, tainted):
                    continue
                before = len(tainted)
                for target in targets:
                    tainted.update(cls._assigned_names(target))
                changed = changed or len(tainted) != before
        return tainted

    def _guard_info(self, node: ast.If) -> tuple[str, bool] | None:
        test = node.test
        if isinstance(test, ast.Attribute) and isinstance(test.value, ast.Name):
            if test.attr == "failure":
                return test.value.id, False
            if test.attr == "success":
                return test.value.id, True
        if (
            isinstance(test, ast.UnaryOp)
            and isinstance(test.op, ast.Not)
            and isinstance(test.operand, ast.Attribute)
            and isinstance(test.operand.value, ast.Name)
        ):
            if test.operand.attr == "success":
                return test.operand.value.id, False
            if test.operand.attr == "failure":
                return test.operand.value.id, True
        return None

    def _add_guard_finding(self, node: ast.If, result_name: str) -> None:
        return_node = self._first_sentinel_return(node.body)
        if return_node is None:
            return
        func = self._enclosing_function(node)
        inner_type = self._result_inner_type(func) if func is not None else None
        replacement: tuple[int, int, str] | None = None
        fix_action = "manual"
        if inner_type is not None:
            lbl = result_name.removesuffix("_result").replace("_", " ").strip()
            failure_label = f"{lbl} failed" if lbl else "operation failed"
            indent = self._indent_of(return_node)
            start, end = self._line_offsets(return_node.lineno)
            replacement = (
                start,
                end,
                (
                    f"{indent}return r[{inner_type}].fail("
                    f"{result_name}.error or {failure_label!r})\n"
                ),
            )
            fix_action = "fix_silent_failure_sentinels"
        self._add_finding(
            line=return_node.lineno,
            column=return_node.col_offset,
            kind="silent-failure-guard",
            detail=(
                f"failure branch for '{result_name}' returns sentinel "
                "instead of propagating the error"
            ),
            fix_action=fix_action,
            replacement=replacement,
        )

    def _add_except_sentinel_finding(self, node: ast.ExceptHandler) -> None:
        return_node = self._first_sentinel_return(node.body)
        if return_node is None:
            return
        exception_name = node.name
        func = self._enclosing_function(node)
        inner_type = self._result_inner_type(func) if func is not None else None
        replacement: tuple[int, int, str] | None = None
        fix_action = "manual"
        if inner_type is not None and exception_name is not None:
            indent = self._indent_of(return_node)
            start, end = self._line_offsets(return_node.lineno)
            replacement = (
                start,
                end,
                (
                    f"{indent}return r[{inner_type}].fail("
                    f"str({exception_name}), exception={exception_name})\n"
                ),
            )
            fix_action = "fix_silent_failure_sentinels"
        self._add_finding(
            line=return_node.lineno,
            column=return_node.col_offset,
            kind="silent-failure-except",
            detail=(
                "exception branch returns sentinel instead of "
                "propagating the caught error"
            ),
            fix_action=fix_action,
            replacement=replacement,
        )

    def _first_sentinel_return(self, body: list[ast.stmt]) -> ast.Return | None:
        for child in self._walk_body_nodes(body):
            if isinstance(child, ast.Return) and self._is_sentinel_value(child.value):
                return child
        return None

    @staticmethod
    def _walk_body_nodes(body: list[ast.stmt]) -> Iterator[ast.AST]:
        """Yield executable nodes without entering nested declarations."""
        pending: list[ast.AST] = list(reversed(body))
        while pending:
            node = pending.pop()
            yield node
            if isinstance(
                node,
                ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda,
            ):
                continue
            pending.extend(reversed(tuple(ast.iter_child_nodes(node))))

    @staticmethod
    def _function_definitions(
        tree: ast.Module,
    ) -> dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]]:
        """Group local functions and methods by call-visible leaf name."""
        definitions: dict[str, list[ast.FunctionDef | ast.AsyncFunctionDef]] = {}
        containers: list[ast.Module | ast.ClassDef] = [tree]
        while containers:
            container = containers.pop()
            for node in container.body:
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    definitions.setdefault(node.name, []).append(node)
                elif isinstance(node, ast.ClassDef):
                    containers.append(node)
        return definitions

    @classmethod
    def _collect_import_aliases(cls, tree: ast.Module) -> dict[str, str]:
        """Collect module import bindings before analyzing handlers."""
        aliases: dict[str, str] = {}
        for node in cls._walk_body_nodes(tree.body):
            if isinstance(node, ast.Import):
                for imported in node.names:
                    bound = imported.asname or imported.name.split(".", maxsplit=1)[0]
                    aliases[bound] = imported.name
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                for imported in node.names:
                    bound = imported.asname or imported.name
                    aliases[bound] = (
                        f"{module_name}.{imported.name}"
                        if module_name
                        else imported.name
                    )
        return aliases

    @classmethod
    def _tainted_call_parameters(
        cls,
        definition: ast.FunctionDef | ast.AsyncFunctionDef,
        call: ast.Call,
        tainted: set[str],
    ) -> set[str]:
        """Map caught-error call arguments to bound callee parameters."""
        arguments = definition.args
        positional = list((*arguments.posonlyargs, *arguments.args))
        if (
            isinstance(call.func, ast.Attribute)
            and positional
            and positional[0].arg in {"self", "cls"}
        ):
            positional = positional[1:]
        bound: set[str] = set()
        for index, value in enumerate(call.args):
            if not cls._node_references_names(value, tainted):
                continue
            if index < len(positional):
                bound.add(positional[index].arg)
            elif arguments.vararg is not None:
                bound.add(arguments.vararg.arg)
        parameter_names = {
            argument.arg
            for argument in (*positional, *arguments.kwonlyargs)
        }
        for keyword in call.keywords:
            if not cls._node_references_names(keyword.value, tainted):
                continue
            if keyword.arg in parameter_names:
                bound.add(keyword.arg)
            elif keyword.arg is None and arguments.kwarg is not None:
                bound.add(arguments.kwarg.arg)
        return bound

    @classmethod
    def _call_arguments_reference_names(
        cls, node: ast.Call, names: set[str]
    ) -> bool:
        """Return whether tracked data is sent as an argument, not a receiver."""
        values: tuple[ast.expr, ...] = (
            *node.args,
            *(keyword.value for keyword in node.keywords),
        )
        return any(cls._node_references_names(value, names) for value in values)

    @classmethod
    def _assigned_names(cls, target: ast.expr) -> set[str]:
        """Return local names bound by one assignment target."""
        if isinstance(target, ast.Name):
            return {target.id}
        if isinstance(target, ast.Starred):
            return cls._assigned_names(target.value)
        if isinstance(target, ast.Tuple | ast.List):
            return {
                name for item in target.elts for name in cls._assigned_names(item)
            }
        return set()

    @staticmethod
    def _node_references_names(node: ast.AST, names: set[str]) -> bool:
        """Return whether one expression consumes a tracked local name."""
        return any(
            isinstance(child, ast.Name) and child.id in names
            for child in ast.walk(node)
        )

    @staticmethod
    def _call_leaf_name(node: ast.Call) -> str:
        """Return the invoked function or method leaf name."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    @staticmethod
    def _resolve_call_name(
        node: ast.Call, import_aliases: Mapping[str, str]
    ) -> str:
        """Resolve a call expression to a dotted name using alias context."""
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            base = import_aliases.get(func.value.id, func.value.id)
            return f"{base}.{func.attr}"
        if isinstance(func, ast.Name):
            return import_aliases.get(func.id, func.id)
        return ""

    @staticmethod
    def _is_unwrap_or_call(node: ast.Call) -> bool:
        """Return True for ``<something>.unwrap_or(<sentinel>)``."""
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "unwrap_or":
            return False
        if not node.args:
            return False
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and first_arg.value in {False, None}:
            return True
        if isinstance(first_arg, ast.List) and not first_arg.elts:
            return True
        return isinstance(first_arg, ast.Dict) and not first_arg.keys

    @staticmethod
    def _expression_name(
        node: ast.expr | None, import_aliases: Mapping[str, str]
    ) -> str:
        """Resolve a bare expression to a dotted name."""
        if node is None:
            return ""
        if isinstance(node, ast.Name):
            return import_aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            base = import_aliases.get(node.value.id, node.value.id)
            return f"{base}.{node.attr}"
        return ""


__all__: list[str] = []
