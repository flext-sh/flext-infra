"""Tests modernizer transformer — migrate unittest.TestCase anti-patterns.

Conservative AST rewrites for test code:

- ``import unittest`` / ``from unittest import TestCase`` → removed.
- ``class TestFoo(unittest.TestCase):`` → ``class TestsFlextFoo(FlextTestsCase):``.
- ``self.assertEqual(a, b)`` → ``tm.that(a, eq=b)``.
- ``self.assertTrue(x)`` → ``tm.that(x, eq=True)``.
- ``self.assertFalse(x)`` → ``tm.that(x, eq=False)``.
- ``self.assertIn(x, y)`` → ``tm.that(y, has=x)``.
- ``self.assertRaises(...)`` is left unchanged but noted for manual conversion.

The transformer is conservative: it only rewrites unambiguous cases and records
every change.
"""

from __future__ import annotations

import ast
import re
from typing import ClassVar, override

from flext_infra.constants import c
from flext_infra.transformers._rewrite import (
    FlextInfraSourceRewrite,
    FlextInfraSourceRewriter,
)
from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraRefactorTestsModernizer(FlextInfraRopeTransformer):
    """AST-driven transformer for unittest-based test anti-patterns."""

    _description = "migrate unittest.TestCase tests to FLEXT test helpers"

    _FLEXT_TESTS_BASE: ClassVar[str] = "flext_tests.base"
    _FLEXT_TESTS_CASE: ClassVar[str] = "FlextTestsCase"
    _TM_MODULE: ClassVar[str] = "tests"
    _TM_NAME: ClassVar[str] = "tm"
    _UNITTEST_MODULE: ClassVar[str] = "unittest"
    _TESTCASE: ClassVar[str] = "TestCase"

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply unittest-to-FLEXT test modernizations to source text."""
        self.changes.clear()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source, list(self.changes)

        visitor = self._TestsVisitor(source)
        visitor.visit(tree)

        updated = source
        if visitor.rewrites:
            updated = FlextInfraSourceRewriter.apply_rewrites(source, visitor.rewrites)

        if visitor.needs_flext_tests_case_import:
            before = updated
            updated = self._ensure_from_import(
                updated,
                self._FLEXT_TESTS_BASE,
                self._FLEXT_TESTS_CASE,
            )
            if updated != before:
                self._record_change(
                    f"Added from {self._FLEXT_TESTS_BASE} "
                    f"import {self._FLEXT_TESTS_CASE}"
                )

        if visitor.needs_tm_import:
            before = updated
            updated = self._ensure_from_import(
                updated,
                self._TM_MODULE,
                self._TM_NAME,
            )
            if updated != before:
                self._record_change(
                    f"Added from {self._TM_MODULE} import {self._TM_NAME}"
                )

        for change in visitor.changes:
            self._record_change(change)

        return updated, list(self.changes)

    @classmethod
    def _ensure_from_import(cls, source: str, module: str, name: str) -> str:
        """Ensure ``from <module> import <name>`` is present."""
        bound_names: set[str] = set()
        for match in c.Infra.FROM_IMPORT_RE.finditer(source):
            if match.group(1) != module:
                continue
            bound_names.update(
                bound for _, bound in u.Infra.parse_import_names(match.group(2))
            )
        for match in c.Infra.FROM_IMPORT_BLOCK_RE.finditer(source):
            if match.group(1) != module:
                continue
            bound_names.update(
                bound for _, bound in u.Infra.parse_import_names(match.group(2))
            )
        if name in bound_names:
            return source

        lines = source.splitlines(keepends=True)
        insert_idx = u.Infra.find_import_insert_position(lines)
        lines.insert(insert_idx, f"from {module} import {name}\n")
        return "".join(lines)

    class _TestsVisitor(FlextInfraSourceRewriter):
        """Collect rewrites for unittest test anti-patterns."""

        def __init__(self, source: str) -> None:
            super().__init__(source)
            self.needs_flext_tests_case_import = False
            self.needs_tm_import = False
            self._unittest_aliases = self._collect_unittest_aliases(source)

        @classmethod
        def _collect_unittest_aliases(cls, source: str) -> set[str]:
            """Collect names bound by ``from unittest import ...``."""
            aliases: set[str] = set()
            module = FlextInfraRefactorTestsModernizer._UNITTEST_MODULE
            for match in c.Infra.FROM_IMPORT_RE.finditer(source):
                if match.group(1) != module:
                    continue
                aliases.update(
                    bound for _, bound in u.Infra.parse_import_names(match.group(2))
                )
            for match in c.Infra.FROM_IMPORT_BLOCK_RE.finditer(source):
                if match.group(1) != module:
                    continue
                aliases.update(
                    bound for _, bound in u.Infra.parse_import_names(match.group(2))
                )
            return aliases

        @override
        def visit_Import(self, node: ast.Import) -> None:
            """Remove ``import unittest`` statements."""
            if all(alias.name == "unittest" for alias in node.names):
                self.append_rewrite(node, "", "Removed import unittest")
            self.generic_visit(node)

        @override
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            """Remove ``from unittest import ...`` statements."""
            if node.module == "unittest":
                self.append_rewrite(node, "", "Removed from unittest import")
            self.generic_visit(node)

        @override
        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            """Rewrite unittest.TestCase test classes."""
            self._maybe_rewrite_test_case_class(node)
            self.generic_visit(node)

        def _is_unittest_base(self, base: ast.expr) -> bool:
            """Return whether ``base`` refers to ``unittest.TestCase``."""
            if (
                isinstance(base, ast.Attribute)
                and base.attr == FlextInfraRefactorTestsModernizer._TESTCASE
            ):
                value = base.value
                return (
                    isinstance(value, ast.Name)
                    and value.id == FlextInfraRefactorTestsModernizer._UNITTEST_MODULE
                )
            if isinstance(base, ast.Name):
                return base.id in self._unittest_aliases
            return False

        def _maybe_rewrite_test_case_class(self, node: ast.ClassDef) -> None:
            """Rewrite a class that directly inherits ``unittest.TestCase``."""
            if len(node.bases) != 1:
                return

            base = node.bases[0]
            if not self._is_unittest_base(base):
                return

            lines = self._source.splitlines(keepends=True)
            header_lineno = self._find_class_header_lineno(node, lines)
            if header_lineno is None:
                return

            line = lines[header_lineno]
            old_name = node.name
            if old_name.startswith("Test"):
                suffix = old_name[4:]
                new_name = f"TestsFlext{suffix}"
            else:
                new_name = f"Tests{old_name}"

            pattern = re.compile(
                r"^(?P<indent>\s*)class\s+"
                + re.escape(old_name)
                + r"\s*\([^)]*\)\s*:(?P<rest>.*)$"
            )
            match = pattern.match(line)
            if match is None:
                return

            indent = match.group("indent")
            rest = match.group("rest")
            new_line = f"{indent}class {new_name}(FlextTestsCase):{rest}\n"
            start = self._offset(header_lineno + 1, 0)
            end = start + len(line)
            self.rewrites.append(
                FlextInfraSourceRewrite(start, end, new_line),
            )
            self.changes.append(
                f"Renamed {old_name} to {new_name} and replaced base "
                "with FlextTestsCase"
            )
            self.needs_flext_tests_case_import = True

        @staticmethod
        def _find_class_header_lineno(
            node: ast.ClassDef,
            lines: list[str],
        ) -> int | None:
            """Locate the 0-based line index of a class header."""
            start_index = getattr(node, "lineno", 1) - 1
            for index in range(start_index, len(lines)):
                if f"class {node.name}" in lines[index]:
                    return index
            return None

        @override
        def visit_Call(self, node: ast.Call) -> None:
            """Rewrite unittest assertion method calls."""
            self._maybe_rewrite_assert_call(node)
            self.generic_visit(node)

        def _maybe_rewrite_assert_call(self, node: ast.Call) -> None:
            """Rewrite ``self.assert*`` calls to ``tm.that`` where unambiguous."""
            if not (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
            ):
                return

            method = node.func.attr
            if method == "assertRaises":
                self.changes.append(
                    "Noted self.assertRaises(...) requires semantic conversion"
                )
                return

            if method == "assertEqual":
                if len(node.args) != 2 or node.keywords:
                    return
                a, b = node.args
                replacement = f"tm.that({ast.unparse(a)}, eq={ast.unparse(b)})"
            elif method == "assertTrue":
                if len(node.args) != 1 or node.keywords:
                    return
                (a,) = node.args
                replacement = f"tm.that({ast.unparse(a)}, eq=True)"
            elif method == "assertFalse":
                if len(node.args) != 1 or node.keywords:
                    return
                (a,) = node.args
                replacement = f"tm.that({ast.unparse(a)}, eq=False)"
            elif method == "assertIn":
                if len(node.args) != 2 or node.keywords:
                    return
                member, container = node.args
                replacement = (
                    f"tm.that({ast.unparse(container)}, has={ast.unparse(member)})"
                )
            else:
                return

            self.append_rewrite(
                node,
                replacement,
                f"Replaced self.{method}(...) with {replacement}",
            )
            self.needs_tm_import = True


__all__: list[str] = ["FlextInfraRefactorTestsModernizer"]
