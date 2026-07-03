"""Rope-backed detector for ENFORCE-026..033 and ENFORCE-083/084 pattern smells.

Ports the retired ast-grep rules into the rope census:
- bare_except: bare ``except:`` clause
- print: ``print(...)`` call
- breakpoint: ``breakpoint()`` / ``import pdb`` / ``pdb.set_trace()``
- open_encoding: ``open(...)`` without ``encoding=``
- dict_annotation: ``dict`` used as a type annotation
- typing_dict_attr: ``typing.Dict`` attribute usage
- typing_dict_import: ``from typing import Dict``
- hardcoded_version: hardcoded ``__version__ = "..."`` assignment
- type_ignore: ``# type: ignore`` suppression comment
- noqa: ``# noqa`` suppression comment
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from pathlib import Path
from typing import ClassVar, override

from rope.base.exceptions import ModuleSyntaxError

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
        "typing_list_attr",
        "typing_list_import",
        "direct_pydantic_import",
        "direct_structlog_import",
        "direct_oracledb_import",
        "direct_ldap3_import",
        "hardcoded_version",
        "type_ignore",
        "noqa",
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
        except (ModuleSyntaxError, SyntaxError) as exc:
            if ctx.parse_failures is None:
                raise
            ctx.parse_failures.append(
                m.Infra.ParseFailureViolation(
                    file=str(ctx.file_path),
                    stage="pattern_smell",
                    error_type=type(exc).__name__,
                    detail=str(exc),
                )
            )
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
        visitor.violations.extend(cls._detect_comment_smells(source, display_path))
        return tuple(visitor.violations)

    @staticmethod
    def _display_path(file_path: Path, project_root: Path | None) -> Path:
        if project_root is not None and file_path.is_relative_to(project_root):
            return file_path.relative_to(project_root)
        return file_path

    @staticmethod
    def _detect_comment_smells(
        source: str,
        file_path: Path,
    ) -> list[m.Infra.PatternSmellViolation]:
        """Detect suppression-comment smells in ``source``."""
        violations: list[m.Infra.PatternSmellViolation] = []
        type_ignore_re = re.compile(r"#\s*type:\s*ignore\b", re.IGNORECASE)
        noqa_re = re.compile(r"#\s*noqa\b", re.IGNORECASE)
        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        except tokenize.TokenError:
            return violations
        for tok in tokens:
            if tok.type != tokenize.COMMENT:
                continue
            comment = tok.string
            if type_ignore_re.search(comment):
                violations.append(
                    m.Infra.PatternSmellViolation(
                        file=str(file_path),
                        line=tok.start[0],
                        kind="type_ignore",
                        detail=(
                            "# type: ignore suppression is forbidden "
                            "— fix the underlying typing issue"
                        ),
                    )
                )
            if noqa_re.search(comment):
                violations.append(
                    m.Infra.PatternSmellViolation(
                        file=str(file_path),
                        line=tok.start[0],
                        kind="noqa",
                        detail=(
                            "# noqa suppression is forbidden "
                            "— fix the underlying lint issue"
                        ),
                    )
                )
        return violations


class _PatternSmellVisitor(ast.NodeVisitor):
    """AST visitor collecting ENFORCE-026..033 pattern smells."""

    _BANNED_MODULE_IMPORTS: ClassVar[t.MappingKV[str, t.StrPair]] = {
        "pydantic": (
            "direct_pydantic_import",
            "bare pydantic import FORBIDDEN — use m.BaseModel, m.ConfigDict, m.TypeAdapter, u.Field, u.field_validator, u.model_validator, u.computed_field, u.PrivateAttr",
        ),
        "structlog": (
            "direct_structlog_import",
            "bare structlog import FORBIDDEN — use u.fetch_logger(__name__)",
        ),
        "oracledb": (
            "direct_oracledb_import",
            "bare oracledb import FORBIDDEN — route through flext-db-oracle / flext-oracle-* facades",
        ),
        "ldap3": (
            "direct_ldap3_import",
            "bare ldap3 import FORBIDDEN — route through flext-ldap / flext-target-ldap facades",
        ),
    }
    _BANNED_TYPING_ATTRS: ClassVar[t.MappingKV[str, t.StrPair]] = {
        "Dict": (
            "typing_dict_attr",
            "typing.Dict attribute usage — use collections.abc.Mapping family",
        ),
        "List": (
            "typing_list_attr",
            "typing.List attribute usage — use t.SequenceOf or collections.abc.Sequence",
        ),
    }
    _BANNED_TYPING_FROM_IMPORTS: ClassVar[t.MappingKV[str, t.StrPair]] = {
        "Dict": (
            "typing_dict_import",
            "from typing import Dict is banned — use dict / Mapping",
        ),
        "List": (
            "typing_list_import",
            "from typing import List is banned — use list / Sequence",
        ),
    }

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
            if alias.name in self._BANNED_MODULE_IMPORTS:
                kind, detail = self._BANNED_MODULE_IMPORTS[alias.name]
                self._add_violation(node.lineno, kind, detail)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module == "typing":
            for alias in node.names:
                if alias.name in self._BANNED_TYPING_FROM_IMPORTS:
                    kind, detail = self._BANNED_TYPING_FROM_IMPORTS[alias.name]
                    self._add_violation(node.lineno, kind, detail)
        if module in self._BANNED_MODULE_IMPORTS:
            kind, detail = self._BANNED_MODULE_IMPORTS[module]
            self._add_violation(node.lineno, kind, detail)
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
            and node.attr in self._BANNED_TYPING_ATTRS
        ):
            kind, detail = self._BANNED_TYPING_ATTRS[node.attr]
            self._add_violation(node.lineno, kind, detail)
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
