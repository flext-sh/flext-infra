"""Pattern modernizer transformer — AST-based fixes for FLEXT code hygiene.

Applies safe, syntactic transformations that do not require type inference:

- ``print(...)`` → ``logger.info(...)`` and injects a module-level logger.
- ``breakpoint()`` / ``import pdb; pdb.set_trace()`` → removed.
- Bare ``except:`` → ``except Exception:``.
- ``open(path, mode)`` without ``encoding`` → ``open(path, mode, encoding="utf-8")``.

The transformer is intentionally conservative: it only rewrites code when the
result is unambiguous and records every change.
"""

from __future__ import annotations

import ast
import re
from typing import ClassVar, override

from flext_infra import FlextInfraRopeTransformer, c, t, u


class FlextInfraRefactorPatternModernizer(FlextInfraRopeTransformer):
    """AST-driven transformer for common FLEXT anti-patterns."""

    _description = (
        "fix common FLEXT anti-patterns (print, pdb, bare except, open encoding)"
    )

    _LOGGER_NAME: ClassVar[str] = "logger"
    _LOGGER_LINE: ClassVar[str] = "logger = u.fetch_logger(__name__)\n"
    _CORE_PKG: ClassVar[str] = c.Infra.PKG_CORE_UNDERSCORE

    class _Rewrite:
        """One source rewrite: replace ``source[start:end]`` with ``text``."""

        __slots__ = ("end", "start", "text")

        def __init__(self, start: int, end: int, text: str) -> None:
            self.start = start
            self.end = end
            self.text = text

        def __lt__(self, other: object) -> bool:
            if not isinstance(other, FlextInfraRefactorPatternModernizer._Rewrite):
                return NotImplemented
            return (self.start, self.end) < (other.start, other.end)

        def __gt__(self, other: object) -> bool:
            if not isinstance(other, FlextInfraRefactorPatternModernizer._Rewrite):
                return NotImplemented
            return (self.start, self.end) > (other.start, other.end)

    @override
    def apply_to_source(self, source: str) -> t.Infra.TransformResult:
        """Apply pattern modernizations to source text."""
        self.changes.clear()
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source, list(self.changes)

        module_has_logger = self._has_logger_binding(tree)
        visitor = self._PatternVisitor(source, module_has_logger=module_has_logger)
        visitor.visit(tree)

        if not visitor.rewrites:
            return source, list(self.changes)

        updated = self._apply_rewrites(source, visitor.rewrites)

        if visitor.needs_logger and not module_has_logger:
            updated = self._ensure_u_import(updated)
            updated = self._inject_logger(updated)

        for change in visitor.changes:
            self._record_change(change)

        return updated, list(self.changes)

    @staticmethod
    def _has_logger_binding(tree: ast.AST) -> bool:
        """Return whether the module already defines a ``logger`` name."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "logger":
                return True
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "logger":
                        return True
        return False

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

    @classmethod
    def _inject_logger(cls, source: str) -> str:
        """Inject ``logger = u.fetch_logger(__name__)`` after imports/docstring."""
        lines = source.splitlines(keepends=True)
        insert_idx = u.Infra.find_import_insert_position(lines)
        lines.insert(insert_idx, cls._LOGGER_LINE)
        return "".join(lines)

    @classmethod
    def _ensure_u_import(cls, source: str) -> str:
        """Ensure ``from flext_core import u`` is present."""
        pkg_match = re.search(
            r"^from\s+flext_core\s+import\s+([^\n]+)",
            source,
            re.MULTILINE,
        )
        if pkg_match:
            names = pkg_match.group(1).strip()
            name_set = {n.strip() for n in names.split(",")}
            if "u" in name_set:
                return source
            new_names = names + ", u"
            return source[: pkg_match.start(1)] + new_names + source[pkg_match.end(1) :]
        lines = source.splitlines(keepends=True)
        insert_idx = u.Infra.find_import_insert_position(lines, past_existing=False)
        lines.insert(insert_idx, f"from {cls._CORE_PKG} import u\n")
        return "".join(lines)

    class _PatternVisitor(ast.NodeVisitor):
        """Collect rewrites for anti-patterns."""

        def __init__(self, source: str, *, module_has_logger: bool) -> None:
            super().__init__()
            self._source = source
            self._module_has_logger = module_has_logger
            self.rewrites: list[FlextInfraRefactorPatternModernizer._Rewrite] = []
            self.changes: list[str] = []
            self.needs_logger = False

        def _offset(self, lineno: int, col_offset: int) -> int:
            """Convert (1-based line, 0-based column) to byte offset."""
            lines = self._source.splitlines(keepends=True)
            return sum(len(lines[i]) for i in range(lineno - 1)) + col_offset

        def _node_text(self, node: ast.AST) -> str:
            """Return source text for a node."""
            start = self._node_offset(node, start=True)
            end = self._node_offset(node, start=False)
            return self._source[start:end]

        def _node_offset(self, node: ast.AST, *, start: bool) -> int:
            """Return byte offset for a node's start or end position."""
            if start:
                lineno = getattr(node, "lineno", 1)
                col_offset = getattr(node, "col_offset", 0)
            else:
                lineno = getattr(node, "end_lineno", getattr(node, "lineno", 1))
                col_offset = getattr(node, "end_col_offset", 0)
            return self._offset(lineno, col_offset)

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
                FlextInfraRefactorPatternModernizer._Rewrite(start, end, text),
            )
            self.changes.append(change)

        @override
        def visit_Expr(self, node: ast.Expr) -> None:
            """Handle expression statements: print, breakpoint."""
            value = node.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
                if value.func.id == "print":
                    self.needs_logger = True
                    call_text = self._node_text(value)
                    new_call = re.sub(r"\bprint\b", "logger.info", call_text, count=1)
                    self._append_rewrite(
                        node, new_call, "Replaced print() with logger.info()"
                    )
                    return
                if value.func.id == "breakpoint":
                    self._append_rewrite(
                        node, "pass", "Replaced breakpoint() with pass"
                    )
                    return
            self.generic_visit(node)

        @override
        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            """Fix bare ``except:`` to ``except Exception:``."""
            if node.type is None:
                lines = self._source.splitlines(keepends=True)
                lineno = getattr(node, "lineno", 1)
                line = lines[lineno - 1]
                stripped = line.lstrip()
                prefix_len = len(line) - len(stripped)
                if stripped.startswith("except:"):
                    indent = line[:prefix_len]
                    new_line = f"{indent}except Exception:\n"
                    start = self._offset(lineno, 0)
                    end = start + len(line)
                    self.rewrites.append(
                        FlextInfraRefactorPatternModernizer._Rewrite(
                            start, end, new_line
                        ),
                    )
                    self.changes.append("Fixed bare except: → except Exception:")
            self.generic_visit(node)

        @override
        def visit_Call(self, node: ast.Call) -> None:
            """Fix ``open()`` calls missing ``encoding``."""
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "open"
                and not any(kw.arg == "encoding" for kw in node.keywords)
            ):
                call_text = self._node_text(node)
                if call_text.endswith(")"):
                    new_call = call_text[:-1] + ', encoding="utf-8")'
                    self._append_rewrite(
                        node,
                        new_call,
                        'Added encoding="utf-8" to open()',
                    )
            self.generic_visit(node)

        @override
        def visit_Import(self, node: ast.Import) -> None:
            """Remove ``import pdb`` statements."""
            if any(alias.name == "pdb" for alias in node.names):
                self._append_rewrite(node, "pass", "Removed import pdb")
            self.generic_visit(node)

        @override
        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            """Remove ``from pdb import ...`` statements."""
            if node.module == "pdb":
                self._append_rewrite(node, "pass", "Removed from pdb import")
            self.generic_visit(node)


__all__: list[str] = ["FlextInfraRefactorPatternModernizer"]
