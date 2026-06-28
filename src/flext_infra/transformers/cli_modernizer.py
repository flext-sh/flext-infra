"""CLI modernizer transformer — migrate legacy CLI helpers to ``flext_cli``.

Conservative AST rewrites for CLI anti-patterns:

- Remove ``import`` / ``from`` statements for ``typer``, ``click``,
  ``argparse``, ``rich`` and ``tabulate``.
- Rewrite ``print(msg)`` → ``cli.display_text(msg)`` when ``cli`` has been
  imported from ``flext_cli``.
- Flag direct ``typer.Typer()``, ``click.group()`` / ``click.command()`` and
  ``argparse.ArgumentParser()`` instantiations for manual conversion.

The transformer is intentionally conservative: it only rewrites code when the
result is unambiguous and records every change.
"""

from __future__ import annotations

import ast
import re
from typing import ClassVar, override

from flext_infra import FlextInfraRopeTransformer, t


class FlextInfraRefactorCliModernizer(FlextInfraRopeTransformer):
    """AST-driven transformer for FLEXT CLI anti-patterns."""

    _description = "migrate legacy CLI constructs to the flext_cli facade"

    _CLI_PKG: ClassVar[str] = "flext_cli"
    _BANNED_MODULES: ClassVar[frozenset[str]] = frozenset(
        {"typer", "click", "argparse", "rich", "tabulate"},
    )
    _MANUAL_ATTRS: ClassVar[dict[str, frozenset[str]]] = {
        "typer": frozenset({"Typer"}),
        "click": frozenset({"group", "command"}),
        "argparse": frozenset({"ArgumentParser"}),
    }

    class _Rewrite:
        """One source rewrite: replace ``source[start:end]`` with ``text``."""

        __slots__ = ("end", "start", "text")

        def __init__(self, start: int, end: int, text: str) -> None:
            self.start = start
            self.end = end
            self.text = text

        def __lt__(self, other: object) -> bool:
            if not isinstance(other, FlextInfraRefactorCliModernizer._Rewrite):
                return NotImplemented
            return (self.start, self.end) < (other.start, other.end)

        def __gt__(self, other: object) -> bool:
            if not isinstance(other, FlextInfraRefactorCliModernizer._Rewrite):
                return NotImplemented
            return (self.start, self.end) > (other.start, other.end)

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply CLI modernizations to source text."""
        self.changes.clear()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source, list(self.changes)

        visitor = self._CliVisitor(source)
        visitor.visit(tree)

        updated = (
            source
            if not visitor.rewrites
            else self._apply_rewrites(source, visitor.rewrites)
        )

        for module, attr in visitor.manual_conversions:
            if module in visitor.removed_modules:
                self._record_change(
                    f"Manual conversion required for {module}.{attr}()",
                )

        for change in visitor.changes:
            self._record_change(change)

        return updated, list(self.changes)

    @classmethod
    def _apply_rewrites(
        cls,
        source: str,
        rewrites: list[_Rewrite],
    ) -> str:
        """Apply rewrites from bottom-right to top-left to preserve offsets."""
        result = source
        for rewrite in sorted(rewrites, reverse=True):
            result = result[: rewrite.start] + rewrite.text + result[rewrite.end :]
        return result

    @staticmethod
    def _banned_modules() -> frozenset[str]:
        """Return the set of CLI helper modules whose imports are removed."""
        return FlextInfraRefactorCliModernizer._BANNED_MODULES

    @staticmethod
    def _cli_pkg() -> str:
        """Return the canonical FLEXT CLI package name."""
        return FlextInfraRefactorCliModernizer._CLI_PKG

    @staticmethod
    def _manual_attrs() -> dict[str, frozenset[str]]:
        """Return banned-module attributes that require manual conversion."""
        return FlextInfraRefactorCliModernizer._MANUAL_ATTRS

    class _CliVisitor(ast.NodeVisitor):
        """Collect rewrites for CLI anti-patterns."""

        def __init__(self, source: str) -> None:
            super().__init__()
            self._source = source
            self.rewrites: list[FlextInfraRefactorCliModernizer._Rewrite] = []
            self.changes: list[str] = []
            self.manual_conversions: list[tuple[str, str]] = []
            self.removed_modules: set[str] = set()
            self._cli_symbol: str | None = None

        def _offset(self, lineno: int, col_offset: int) -> int:
            """Convert (1-based line, 0-based column) to byte offset."""
            lines = self._source.splitlines(keepends=True)
            return sum(len(lines[i]) for i in range(lineno - 1)) + col_offset

        def _node_offset(self, node: ast.AST, *, start: bool) -> int:
            """Return byte offset for a node's start or end position."""
            if start:
                lineno = getattr(node, "lineno", 1)
                col_offset = getattr(node, "col_offset", 0)
            else:
                lineno = getattr(node, "end_lineno", getattr(node, "lineno", 1))
                col_offset = getattr(node, "end_col_offset", 0)
            return self._offset(lineno, col_offset)

        def _node_text(self, node: ast.AST) -> str:
            """Return source text for a node."""
            start = self._node_offset(node, start=True)
            end = self._node_offset(node, start=False)
            return self._source[start:end]

        def _append_rewrite(
            self,
            node: ast.AST,
            text: str,
            change: str,
        ) -> None:
            """Record a rewrite spanning a node's source range."""
            start = self._node_offset(node, start=True)
            end = self._node_offset(node, start=False)
            self.rewrites.append(
                FlextInfraRefactorCliModernizer._Rewrite(start, end, text),
            )
            self.changes.append(change)

        @override
        def visit_Import(self, node: ast.Import) -> None:
            """Remove ``import <banned-module>`` statements."""
            banned = FlextInfraRefactorCliModernizer._banned_modules()
            if node.names and all(alias.name in banned for alias in node.names):
                names = ", ".join(alias.name for alias in node.names)
                self._append_rewrite(node, "", f"Removed import {names}")
                for alias in node.names:
                    self.removed_modules.add(alias.name)
            self.generic_visit(node)

        @override
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            """Remove ``from <banned-module> import ...`` and detect cli import."""
            module = node.module
            if module is None:
                self.generic_visit(node)
                return
            banned = FlextInfraRefactorCliModernizer._banned_modules()
            if module in banned:
                self._append_rewrite(node, "", f"Removed from {module} import")
                self.removed_modules.add(module)
            elif module == FlextInfraRefactorCliModernizer._cli_pkg():
                for alias in node.names:
                    if alias.name == "cli":
                        self._cli_symbol = alias.asname or alias.name
            self.generic_visit(node)

        @override
        def visit_Call(self, node: ast.Call) -> None:
            """Rewrite ``print()`` and flag banned direct instantiations."""
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                self._maybe_rewrite_print(node)
            elif isinstance(func, ast.Attribute):
                self._maybe_flag_manual_conversion(func)
            self.generic_visit(node)

        def _maybe_rewrite_print(self, node: ast.Call) -> None:
            """Rewrite ``print(msg)`` when ``cli`` is imported from ``flext_cli``."""
            if self._cli_symbol is None:
                return
            if len(node.args) != 1 or node.keywords:
                return
            call_text = self._node_text(node)
            new_call = re.sub(
                r"\bprint\b",
                f"{self._cli_symbol}.display_text",
                call_text,
                count=1,
            )
            self._append_rewrite(
                node,
                new_call,
                f"Replaced print() with {self._cli_symbol}.display_text()",
            )

        def _maybe_flag_manual_conversion(self, func: ast.Attribute) -> None:
            """Note banned direct instantiations that need manual conversion."""
            value = func.value
            if not isinstance(value, ast.Name):
                return
            module = value.id
            banned = FlextInfraRefactorCliModernizer._banned_modules()
            if module not in banned:
                return
            attrs = FlextInfraRefactorCliModernizer._manual_attrs().get(
                module,
                frozenset(),
            )
            if func.attr in attrs:
                self.manual_conversions.append((module, func.attr))


__all__: list[str] = ["FlextInfraRefactorCliModernizer"]
