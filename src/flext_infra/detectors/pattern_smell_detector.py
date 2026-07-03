"""Rope-backed detector for ENFORCE-026..033 pattern smells.

Ports the retired ast-grep rules into the rope census:
- bare_except: bare ``except:`` clause
- print: ``print(...)`` call
- breakpoint: ``breakpoint()`` / ``import pdb`` / ``pdb.set_trace()``
- open_encoding: ``open(...)`` without ``encoding=``
- dict_annotation: ``dict`` used as a type annotation
- typing_dict_attr: ``typing.Dict`` attribute usage
- typing_dict_import: ``from typing import Dict``
- hardcoded_version: hardcoded ``__version__ = "..."`` assignment
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import ClassVar, override

from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraPatternSmellDetector:
    """Detect ENFORCE-026..033 pattern smells in one Python file."""

    _SMELL_KINDS: ClassVar[frozenset[str]] = frozenset({
        "bare_except",
        "print",
        "breakpoint",
        "open_encoding",
        "dict_annotation",
        "typing_dict_attr",
        "typing_dict_import",
        "hardcoded_version",
    })

    @classmethod
    def detect_file(
        cls,
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.PatternSmellViolation]:
        """Return all pattern-smell violations in ``ctx.file_path``."""
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return ()
        try:
            pymodule = u.Infra.get_pymodule(ctx.rope_project, resource)
            tree = pymodule.get_ast()
        except Exception:
            return ()
        if not isinstance(tree, ast.Module):
            return ()
        source = resource.read()
        display_path = cls._display_path(ctx.file_path, ctx.project_root)
        visitor = _PatternSmellVisitor(
            file_path=display_path,
            source=source,
        )
        visitor.visit(tree)
        return tuple(visitor.violations)

    @staticmethod
    def _display_path(file_path: Path, project_root: Path | None) -> Path:
        if project_root is not None:
            try:
                return file_path.relative_to(project_root)
            except ValueError:
                pass
        return file_path


class _PatternSmellVisitor(ast.NodeVisitor):
    """AST visitor collecting ENFORCE-026..033 pattern smells."""

    def __init__(
        self,
        *,
        file_path: Path,
        source: str,
    ) -> None:
        self.file_path = file_path
        self.source = source
        self.violations: list[m.Infra.PatternSmellViolation] = []
        self._typing_alias: str | None = None

    @override
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "typing":
                self._typing_alias = alias.asname or "typing"
            if alias.name == "pdb":
                self._add_violation(
                    node.lineno,
                    "breakpoint",
                    "import pdb is forbidden — remove debugging code",
                )
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module == "typing":
            for alias in node.names:
                if alias.name == "Dict":
                    self._add_violation(
                        node.lineno,
                        "typing_dict_import",
                        "from typing import Dict is banned — use dict / Mapping",
                    )
        if module == "pdb":
            self._add_violation(
                node.lineno,
                "breakpoint",
                "from pdb import ... is forbidden — remove debugging code",
            )
        self.generic_visit(node)

    @override
    def visit_Expr(self, node: ast.Expr) -> None:
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            if value.func.id == "print":
                self._add_violation(
                    node.lineno,
                    "print",
                    "print() call in source code — use structured logging",
                )
            elif value.func.id == "breakpoint":
                self._add_violation(
                    node.lineno,
                    "breakpoint",
                    "breakpoint() left in code",
                )
        self.generic_visit(node)

    @override
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self._add_violation(
                node.lineno,
                "bare_except",
                "Bare `except:` clause swallows all exceptions including SystemExit",
            )
        self.generic_visit(node)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "open"
            and not any(kw.arg == "encoding" for kw in node.keywords)
        ):
            self._add_violation(
                node.lineno,
                "open_encoding",
                'open() without explicit encoding — add encoding="utf-8"',
            )
        self.generic_visit(node)

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        annotation = node.annotation
        if self._is_dict_annotation(annotation):
            self._add_violation(
                node.lineno,
                "dict_annotation",
                "`dict` in type annotation — prefer Mapping / MutableMapping / TypedDict",
            )
        if (
            isinstance(node.target, ast.Name)
            and node.target.id == "__version__"
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            self._add_violation(
                node.lineno,
                "hardcoded_version",
                "Hardcoded __version__ string — use importlib.metadata",
            )
        self.generic_visit(node)

    @override
    def visit_Attribute(self, node: ast.Attribute) -> None:
        if (
            isinstance(node.value, ast.Name)
            and node.value.id == "typing"
            and node.attr == "Dict"
        ):
            self._add_violation(
                node.lineno,
                "typing_dict_attr",
                "typing.Dict attribute usage — use collections.abc.Mapping family",
            )
        self.generic_visit(node)

    def _is_dict_annotation(self, node: ast.expr | None) -> bool:
        """Return True for bare ``dict`` or ``dict[...]`` annotations."""
        if isinstance(node, ast.Name) and node.id == "dict":
            return True
        return (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "dict"
        )

    def _add_violation(
        self,
        line: int,
        kind: str,
        detail: str,
    ) -> None:
        self.violations.append(
            m.Infra.PatternSmellViolation(
                file=str(self.file_path),
                line=line,
                kind=kind,
                detail=detail,
            )
        )


__all__: list[str] = ["FlextInfraPatternSmellDetector"]
