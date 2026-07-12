"""Declarative rope-backed detector for pattern/typing enforcement smells.

Replaces per-smell visitor methods with small canonical maps so adding a new
rule is a one-line catalog + one-line map entry, not a new visitor method.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from flext_infra import t


class FlextInfraPatternSmellDetector:
    """Detect ENFORCE-026..033 / ENFORCE-083..084 / ENFORCE-091..096 smells."""

    # module name -> (kind, detail)
    _BANNED_MODULE_IMPORTS: ClassVar[t.MappingKV[str, t.StrPair]] = {
        "pydantic": (
            "direct_pydantic_import",
            (
                "bare pydantic import FORBIDDEN — use m.BaseModel, m.ConfigDict, "
                "m.TypeAdapter, u.Field, u.field_validator, u.model_validator, "
                "u.computed_field, u.PrivateAttr"
            ),
        ),
        "structlog": (
            "direct_structlog_import",
            "bare structlog import FORBIDDEN — use u.fetch_logger(__name__)",
        ),
        "oracledb": (
            "direct_oracledb_import",
            (
                "bare oracledb import FORBIDDEN — route through flext-db-oracle / "
                "flext-oracle-* facades"
            ),
        ),
        "ldap3": (
            "direct_ldap3_import",
            (
                "bare ldap3 import FORBIDDEN — route through flext-ldap / "
                "flext-target-ldap facades"
            ),
        ),
        "pdb": (
            "breakpoint",
            "import pdb is forbidden — remove debugging code",
        ),
    }

    # module name -> {imported name -> (kind, detail)}; "*" bans any name.
    _BANNED_FROM_IMPORTS: ClassVar[t.MappingKV[str, t.MappingKV[str, t.StrPair]]] = {
        "typing": {
            "Dict": (
                "typing_dict_import",
                "from typing import Dict is banned — use dict / Mapping",
            ),
            "List": (
                "typing_list_import",
                "from typing import List is banned — use list / Sequence",
            ),
        },
        "pdb": {
            "*": (
                "breakpoint",
                "from pdb import ... is forbidden — remove debugging code",
            ),
        },
    }

    # (canonical module name, attribute name) -> (kind, detail)
    _BANNED_ATTRIBUTES: ClassVar[t.MappingKV[t.StrPair, t.StrPair]] = {
        ("typing", "Dict"): (
            "typing_dict_attr",
            "typing.Dict attribute usage — use collections.abc.Mapping family",
        ),
        ("typing", "List"): (
            "typing_list_attr",
            (
                "typing.List attribute usage — use t.SequenceOf or "
                "collections.abc.Sequence"
            ),
        ),
    }

    # bare call name -> (kind, detail)
    _BANNED_BARE_CALLS: ClassVar[t.MappingKV[str, t.StrPair]] = {
        "print": (
            "print",
            "print() call in source code — use structured logging",
        ),
        "breakpoint": (
            "breakpoint",
            "breakpoint() left in code",
        ),
    }

    # call name -> (kind, required kwarg, detail)
    _BANNED_CALLS_MISSING_KWARG: ClassVar[t.MappingKV[str, tuple[str, str, str]]] = {
        "open": (
            "open_encoding",
            "encoding",
            'open() without explicit encoding — add encoding="utf-8"',
        ),
    }

    # annotation root name -> (kind, detail)
    _BANNED_ANNOTATIONS: ClassVar[t.MappingKV[str, t.StrPair]] = {
        "dict": (
            "dict_annotation",
            "`dict` in type annotation — prefer Mapping / MutableMapping / TypedDict",
        ),
    }

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
    def _is_owned_library_exempt(
        cls,
        project_name: str | None,
        module_name: str,
    ) -> bool:
        """Return True when the current project owns the library abstraction.

        Direct imports of pydantic/structlog/oracledb/ldap3 are allowed inside
        the owning project's facade definition; consumers must route through the
        canonical project facade.
        """
        owner: object = c.ENFORCEMENT_LIBRARY_OWNERS.get(module_name)
        if project_name is None or not isinstance(owner, str):
            return False
        return project_name == owner

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
        except (*c.Infra.SYNTAX_ERRORS,) as exc:
            if ctx.parse_failures is None:
                raise
            ctx.parse_failures.append(
                m.Infra.ParseFailureViolation(
                    file=str(ctx.file_path),
                    stage="pattern_smell",
                    error_type=type(exc).__name__,
                    detail=str(exc),
                ),
            )
            return ()
        if not isinstance(tree, ast.Module):
            return ()
        source = resource.read()
        display_path = cls._display_path(ctx.file_path, ctx.project_root)
        visitor = _PatternSmellVisitor(
            file_path=display_path,
            source=source,
            project_name=ctx.project_name,
            owned_exempt=cls._is_owned_library_exempt,
            banned_module_imports=cls._BANNED_MODULE_IMPORTS,
            banned_from_imports=cls._BANNED_FROM_IMPORTS,
            banned_attributes=cls._BANNED_ATTRIBUTES,
            banned_bare_calls=cls._BANNED_BARE_CALLS,
            banned_calls_missing_kwarg=cls._BANNED_CALLS_MISSING_KWARG,
            banned_annotations=cls._BANNED_ANNOTATIONS,
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
                    ),
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
                    ),
                )
        return violations


class _PatternSmellVisitor(ast.NodeVisitor):
    """AST visitor driven by declarative smell maps."""

    def __init__(
        self,
        *,
        file_path: Path,
        source: str,
        project_name: str | None,
        owned_exempt: Callable[[str | None, str], bool],
        banned_module_imports: t.MappingKV[str, t.StrPair],
        banned_from_imports: t.MappingKV[str, t.MappingKV[str, t.StrPair]],
        banned_attributes: t.MappingKV[t.StrPair, t.StrPair],
        banned_bare_calls: t.MappingKV[str, t.StrPair],
        banned_calls_missing_kwarg: t.MappingKV[str, tuple[str, str, str]],
        banned_annotations: t.MappingKV[str, t.StrPair],
    ) -> None:
        self.file_path = file_path
        self.source = source
        self.project_name = project_name
        self._owned_exempt = owned_exempt
        self.violations: list[m.Infra.PatternSmellViolation] = []
        self._module_aliases: dict[str, str] = {}
        self._banned_module_imports = banned_module_imports
        self._banned_from_imports = banned_from_imports
        self._banned_attributes = banned_attributes
        self._banned_bare_calls = banned_bare_calls
        self._banned_calls_missing_kwarg = banned_calls_missing_kwarg
        self._banned_annotations = banned_annotations

    @override
    def visit_Import(self, node: ast.Import) -> None:
        tracked_modules = {module for module, _attr in self._banned_attributes}
        for alias in node.names:
            canonical = alias.name
            if canonical in self._banned_module_imports and not self._owned_exempt(
                self.project_name,
                canonical,
            ):
                kind, detail = self._banned_module_imports[canonical]
                self._add_violation(node.lineno, kind, detail)
            if canonical in tracked_modules:
                local = alias.asname or canonical
                self._module_aliases[local] = canonical
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        banned_from = self._banned_from_imports.get(module)
        if banned_from:
            for alias in node.names:
                key = "*" if "*" in banned_from else alias.name
                if key in banned_from:
                    kind, detail = banned_from[key]
                    self._add_violation(node.lineno, kind, detail)
        if module in self._banned_module_imports and not self._owned_exempt(
            self.project_name,
            module,
        ):
            kind, detail = self._banned_module_imports[module]
            self._add_violation(node.lineno, kind, detail)
        self.generic_visit(node)

    @override
    def visit_Expr(self, node: ast.Expr) -> None:
        value = node.value
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name):
            func_id = value.func.id
            if func_id in self._banned_bare_calls:
                kind, detail = self._banned_bare_calls[func_id]
                self._add_violation(node.lineno, kind, detail)
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
        if isinstance(node.func, ast.Name):
            func_id = node.func.id
            if func_id in self._banned_calls_missing_kwarg:
                kind, required_kwarg, detail = self._banned_calls_missing_kwarg[func_id]
                if not any(kw.arg == required_kwarg for kw in node.keywords):
                    self._add_violation(node.lineno, kind, detail)
        self.generic_visit(node)

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._is_banned_annotation(node.annotation):
            kind, detail = self._banned_annotations["dict"]
            self._add_violation(node.lineno, kind, detail)
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
        if isinstance(node.value, ast.Name):
            canonical = self._module_aliases.get(node.value.id)
            key = (canonical, node.attr) if canonical else None
            if key and key in self._banned_attributes:
                kind, detail = self._banned_attributes[key]
                self._add_violation(node.lineno, kind, detail)
        self.generic_visit(node)

    def _is_banned_annotation(self, node: ast.expr | None) -> bool:
        """Return True for banned root annotations like ``dict`` or ``dict[...]``."""
        if isinstance(node, ast.Name) and node.id in self._banned_annotations:
            return True
        return (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in self._banned_annotations
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
            ),
        )


__all__: list[str] = ["FlextInfraPatternSmellDetector"]
