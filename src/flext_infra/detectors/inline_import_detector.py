"""Detect inline/lazy imports inside function bodies and importlib calls.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, override

from flext_infra._constants.detectors import FlextInfraConstantsDetectors
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraInlineImportDetector:
    """Detect function-body imports and importlib.import_module calls.

    Only module-level imports are acceptable in governed FLEXT source.
    Function-body imports and dynamic importlib loads are flagged so they
    can be hoisted or reviewed manually.
    """

    _STDLIB_NAMES: ClassVar[frozenset[str]] = frozenset(sys.stdlib_module_names)

    @classmethod
    def fix_action_for(
        cls,
        *,
        module_name: str,
        is_importlib: bool,
    ) -> str:
        """Return 'hoist_inline_import' when no cycle risk, else 'manual'."""
        if is_importlib:
            return "manual"
        top_level = module_name.split(".", maxsplit=1)[0] if module_name else ""
        if top_level in cls._STDLIB_NAMES:
            return "hoist_inline_import"
        return "manual"

    @classmethod
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.InlineImportViolation]:
        """Return inline-import violations for one file."""
        file_path = ctx.file_path
        if cls._exempt_file(file_path):
            return ()
        res = u.Infra.fetch_python_resource(
            ctx.rope_project,
            file_path,
            skip_init_py=False,
        )
        if res is None:
            return ()
        try:
            pymodule = u.Infra.get_pymodule(ctx.rope_project, res)
            tree = pymodule.get_ast()
        except Exception:
            return ()
        if not isinstance(tree, ast.Module):
            return ()
        visitor = _InlineImportVisitor(
            file_path=file_path,
        )
        visitor.visit(tree)
        return tuple(visitor.violations)

    @classmethod
    def _exempt_file(cls, file_path: Path) -> bool:
        """Skip lazy-init scaffolds, beartype bootstrap, and flext_core.lazy."""
        parts = file_path.parts
        return (
            file_path.name == "__init__.py"
            or "beartype" in parts
            or (file_path.name == "lazy.py" and "flext_core" in parts)
        )


class _InlineImportVisitor(ast.NodeVisitor):
    """AST visitor collecting inline imports and importlib calls."""

    def __init__(
        self,
        *,
        file_path: Path,
    ) -> None:
        self.file_path = file_path
        self.violations: list[m.Infra.InlineImportViolation] = []
        self._type_checking_depth = 0
        self._function_depth = 0
        self._import_aliases: dict[str, str] = {}

    @override
    def visit_If(self, node: ast.If) -> None:
        if _is_type_checking_if(node):
            self._type_checking_depth += 1
            self.generic_visit(node)
            self._type_checking_depth -= 1
        else:
            self.generic_visit(node)

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter_function(node)

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter_function(node)

    def _enter_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._function_depth += 1
        self.generic_visit(node)
        self._function_depth -= 1

    @override
    def visit_Import(self, node: ast.Import) -> None:
        if self._type_checking_depth > 0:
            return
        for alias in node.names:
            if self._function_depth == 0:
                bound_name = alias.asname or alias.name.split(".")[0]
                self._import_aliases[bound_name] = alias.name
                continue
            module_name = alias.name.split(".")[0]
            self._add_violation(
                line=node.lineno,
                current_import=f"import {alias.name}",
                detail=f"Inline import 'import {alias.name}' inside function body",
                module_name=module_name,
                imported_symbols=(alias.asname or alias.name,),
                is_importlib=False,
            )

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self._type_checking_depth > 0:
            return
        module_name = node.module or ""
        imported_symbols = tuple(alias.name for alias in node.names)
        names_str = ", ".join(
            f"{name} as {alias.asname}" if alias.asname else name
            for name, alias in zip(imported_symbols, node.names, strict=True)
        )
        if self._function_depth == 0:
            for alias in node.names:
                bound_name = alias.asname or alias.name
                self._import_aliases[bound_name] = (
                    f"{module_name}.{alias.name}" if module_name else alias.name
                )
            return
        self._add_violation(
            line=node.lineno,
            current_import=f"from {module_name} import {names_str}",
            detail=(
                f"Inline import 'from {module_name} import {names_str}' "
                "inside function body"
            ),
            module_name=module_name,
            imported_symbols=imported_symbols,
            is_importlib=False,
        )

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if self._type_checking_depth > 0:
            return
        call_name = _resolve_call_name(node, self._import_aliases)
        if call_name == FlextInfraConstantsDetectors.IMPORTLIB_IMPORT_MODULE:
            self._add_violation(
                line=node.lineno,
                current_import="importlib.import_module(...)",
                detail="Dynamic import via importlib.import_module outside flext_core/lazy.py",
                module_name="",
                imported_symbols=(),
                is_importlib=True,
            )
        self.generic_visit(node)

    def _add_violation(
        self,
        *,
        line: int,
        current_import: str,
        detail: str,
        module_name: str,
        imported_symbols: t.StrSequence,
        is_importlib: bool,
    ) -> None:
        self.violations.append(
            m.Infra.InlineImportViolation(
                file=str(self.file_path),
                line=line,
                current_import=current_import,
                detail=detail,
                module_name=module_name,
                imported_symbols=imported_symbols,
                is_importlib=is_importlib,
            )
        )


def _is_type_checking_if(node: ast.If) -> bool:
    """Return True when the if-test is a bare ``TYPE_CHECKING`` name."""
    test = node.test
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def _resolve_call_name(
    node: ast.Call,
    import_aliases: Mapping[str, str],
) -> str:
    """Resolve a call expression to a dotted name using alias context."""
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        base = import_aliases.get(func.value.id, func.value.id)
        return f"{base}.{func.attr}"
    if isinstance(func, ast.Name):
        return import_aliases.get(func.id, func.id)
    return ""


__all__: list[str] = ["FlextInfraInlineImportDetector"]
