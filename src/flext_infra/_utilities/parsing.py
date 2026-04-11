"""Parsing utilities for infrastructure code analysis.

All AST access is deferred to function bodies via ``import ast`` to keep the
module-level namespace free of ast/cst imports. Import parsing, alias scanning,
and rule normalization live in this namespace as part of the same parsing
domain.
"""

from __future__ import annotations

import ast
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import override

from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, t


class FlextInfraUtilitiesParsing:
    """Static parsing utilities for Python source and import analysis."""

    _DOCSTRING_QUOTES = ('"""', "'''")
    _SINGLE_LINE_DOCSTRING_QUOTE_COUNT = 2
    _RULE_CONFIG_SEQ_ADAPTER: TypeAdapter[
        Sequence[m.Infra.ImportModernizerRuleConfig]
    ] = TypeAdapter(
        Sequence[m.Infra.ImportModernizerRuleConfig],
    )

    @staticmethod
    def parse_module_ast(file_path: Path) -> t.Infra.AstModule | None:
        """Parse a Python file into an AST module."""
        try:
            return ast.parse(
                file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT),
            )
        except (OSError, SyntaxError):
            return None

    @staticmethod
    def is_module_toplevel(file_path: Path) -> bool:
        """Determine if a file is at the package root level (Facade level)."""
        parts = file_path.resolve().parts
        try:
            src_idx = parts.index(c.Infra.DEFAULT_SRC_DIR)
            return len(parts) == src_idx + 3
        except ValueError:
            return (file_path.parent / c.Infra.INIT_PY).is_file() and not (
                file_path.parent.parent / c.Infra.INIT_PY
            ).is_file()

    @staticmethod
    def find_import_insert_position(
        lines: Sequence[str],
        *,
        past_existing: bool = True,
    ) -> int:
        """Find line index suitable for inserting new imports.

        Delegates to module-level ``_find_import_insert_position``.
        """
        return FlextInfraUtilitiesParsing._find_import_insert_position(
            lines,
            past_existing=past_existing,
        )

    @staticmethod
    def index_after_docstring_and_future_imports(
        lines: Sequence[str],
    ) -> int:
        """Return insertion index after module docstring and future imports.

        Operates on source lines instead of CST body nodes.
        """
        insert_idx = 0
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if in_docstring:
                insert_idx = i + 1
                if stripped.endswith(FlextInfraUtilitiesParsing._DOCSTRING_QUOTES):
                    in_docstring = False
                continue
            if i == 0 and c.Infra.DOCSTRING_RE.match(stripped):
                insert_idx = i + 1
                if not (
                    stripped.count('"""')
                    >= FlextInfraUtilitiesParsing._SINGLE_LINE_DOCSTRING_QUOTE_COUNT
                    or stripped.count("'''")
                    >= FlextInfraUtilitiesParsing._SINGLE_LINE_DOCSTRING_QUOTE_COUNT
                ):
                    in_docstring = True
                continue
            if c.Infra.FUTURE_IMPORT_RE.match(stripped):
                insert_idx = i + 1
                continue
            if stripped and not stripped.startswith("#"):
                break
            insert_idx = i + 1
        return insert_idx

    @staticmethod
    def _find_import_insert_position(
        lines: Sequence[str],
        *,
        past_existing: bool = True,
    ) -> int:
        """Find line index suitable for inserting new imports."""
        idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                idx = i + 1
                continue
            if stripped.startswith(('"""', "'''")):
                idx = i + 1
                continue
            if stripped.startswith("from __future__"):
                idx = i + 1
                continue
            if past_existing and c.Infra.IMPORT_LINE_RE.match(line):
                idx = i + 1
                continue
            break
        return idx

    @staticmethod
    @override
    def discover_first_party_namespaces(
        project_dir: Path,
    ) -> t.StrSequence:
        """Discover first-party namespaces directly under ``src/``."""
        src_dir = project_dir / c.Infra.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return list[str]()
        return [
            entry.name
            for entry in sorted(src_dir.iterdir())
            if entry.is_dir()
            and entry.name != c.Infra.DUNDER_PYCACHE
            and entry.name.isidentifier()
            and "-" not in entry.name
        ]

    # ── Generic AST helpers (shared across validate/refactor/codegen) ──

    @staticmethod
    def ast_expr_name(node: t.Infra.AstExpr) -> str:
        """Extract the simple name from any AST expression node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Subscript):
            return FlextInfraUtilitiesParsing.ast_expr_name(node.value)
        return ""

    @staticmethod
    def ast_expr_contains(
        node: t.Infra.AstExpr | None,
        name: str,
    ) -> bool:
        """Check if an AST expression tree references a given name."""
        if node is None:
            return False
        return FlextInfraUtilitiesParsing.ast_expr_name(node) == name or (
            hasattr(node, "value")
            and FlextInfraUtilitiesParsing.ast_expr_contains(
                getattr(node, "value", None),
                name,
            )
        )

    @staticmethod
    def looks_like_facade_file(*, file_path: Path, source: str) -> bool:
        """Check if a file looks like a namespace facade (e.g. models.py with ``m = FlextXxxModels``)."""
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return False
        return any(
            line.strip().startswith(f"{family} = ") for line in source.splitlines()
        )

    @staticmethod
    def find_import_line(*, lines: Sequence[str], module_name: str) -> int:
        """Find the 1-based line number of ``from <module_name> import ...``."""
        prefix = f"from {module_name} import "
        for index, line in enumerate(lines, start=1):
            if line.strip().startswith(prefix):
                return index
        return 1

    @staticmethod
    def parse_import_names(names_str: str) -> Sequence[t.Infra.StrPair]:
        """Parse 'A, B as C, D' into [(name, bound), ...]."""
        result: MutableSequence[t.Infra.StrPair] = []
        for part in names_str.split(","):
            part = part.strip().rstrip("\\").strip()
            if not part or part.startswith(("(", ")")):
                continue
            if " as " in part:
                name, alias = part.split(" as ", 1)
                result.append((name.strip(), alias.strip()))
            else:
                result.append((part, part))
        return result

    @staticmethod
    def parse_param_names(params_str: str) -> t.Infra.StrSet:
        """Parse parameter names from a function signature string."""
        names: t.Infra.StrSet = set()
        for part in params_str.split(","):
            item = part.strip()
            if not item or item == "/":
                continue
            name = item.split(":")[0].split("=")[0].strip().lstrip("*")
            if name:
                names.add(name)
        return names

    @staticmethod
    def collect_from_import_bound_names(
        source: str,
        *,
        module_name: str,
    ) -> t.Infra.StrSet:
        """Collect bound names imported from a target module."""
        rh = FlextInfraUtilitiesParsing
        bound_names: t.Infra.StrSet = set()
        for match in c.Infra.FROM_IMPORT_RE.finditer(source):
            if match.group(1) != module_name:
                continue
            bound_names.update(
                bound for _name, bound in rh.parse_import_names(match.group(2))
            )
        for match in c.Infra.FROM_IMPORT_BLOCK_RE.finditer(source):
            if match.group(1) != module_name:
                continue
            bound_names.update(
                bound for _name, bound in rh.parse_import_names(match.group(2))
            )
        return bound_names

    @staticmethod
    def parse_forbidden_rules(
        value: t.Infra.InfraValue,
    ) -> Sequence[m.Infra.ImportModernizerRuleConfig]:
        """Parse and validate forbidden import rule configs."""
        try:
            raw_items: Sequence[t.Infra.ContainerDict] = (
                t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError:
            return []
        normalized: Sequence[t.Infra.ContainerDict] = [
            {
                "module": item.get("module", ""),
                "symbol_mapping": item.get("symbol_mapping", {}),
            }
            for item in raw_items
        ]
        try:
            return FlextInfraUtilitiesParsing._RULE_CONFIG_SEQ_ADAPTER.validate_python(
                normalized,
            )
        except ValidationError:
            return []

    @staticmethod
    def collect_blocked_aliases(
        source: str,
        runtime_aliases: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        """Collect aliases blocked by definitions, non-core imports, and assignments."""
        rh = FlextInfraUtilitiesParsing
        blocked: t.Infra.StrSet = set()
        for match in c.Infra.DEF_CLASS_RE.finditer(source):
            name = match.group(1)
            if name in runtime_aliases:
                blocked.add(name)
        for match in c.Infra.FROM_IMPORT_RE.finditer(source):
            module = match.group(1)
            if module == c.Infra.PKG_CORE_UNDERSCORE:
                continue
            for _name, bound in rh.parse_import_names(match.group(2)):
                if bound in runtime_aliases:
                    blocked.add(bound)
        for match in c.Infra.IMPORT_RE.finditer(source):
            for _name, bound in rh.parse_import_names(match.group(1)):
                if bound in runtime_aliases:
                    blocked.add(bound)
        for match in c.Infra.ASSIGN_RE.finditer(source):
            name = match.group(1)
            if name in runtime_aliases:
                blocked.add(name)
        return blocked

    @staticmethod
    def collect_shadowed_aliases(
        source: str,
        runtime_aliases: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        """Collect runtime-alias names shadowed inside function bodies."""
        shadowed: t.Infra.StrSet = set()
        for match in c.Infra.FUNC_PARAM_RE.finditer(source):
            params = match.group(1)
            for param in params.split(","):
                param_name = param.strip().split(":")[0].split("=")[0].strip()
                if param_name.startswith("*"):
                    param_name = param_name.lstrip("*")
                if param_name in runtime_aliases:
                    shadowed.add(param_name)
        return shadowed

    @staticmethod
    def find_final_candidates(
        source: str,
    ) -> Sequence[m.Infra.MROSymbolCandidate]:
        """Find module-level Final-annotated constants via regex."""
        candidates: MutableSequence[m.Infra.MROSymbolCandidate] = []
        for i, line in enumerate(source.splitlines(), start=1):
            stripped = line.lstrip()
            if line != stripped and stripped:
                continue
            match = c.Infra.FINAL_ASSIGN_RE.match(stripped)
            if match and c.Infra.CONSTANT_NAME_RE.match(match.group(1)) is not None:
                candidates.append(
                    m.Infra.MROSymbolCandidate(
                        symbol=match.group(1),
                        line=i,
                    ),
                )
        return candidates

    @staticmethod
    def first_constants_class_name(source: str) -> str:
        """Find the first class ending with Constants suffix."""
        for match in c.Infra.CLASS_NAME_RE.finditer(source):
            name = match.group(1)
            if name.endswith(c.Infra.CONSTANTS_CLASS_SUFFIX):
                return name
        return ""

    @staticmethod
    def parse_class_bases(source: str, class_name: str) -> Sequence[str]:
        """Extract base class names from a named class definition in source code.

        Finds the class matching *class_name* in *source*, parses its base classes,
        and returns the terminal (unqualified, unsubscripted) names in declaration order.
        Returns an empty sequence when the class is not found.
        """
        for match in c.Infra.CLASS_WITH_BASES_RE.finditer(source):
            if match.group(1) != class_name:
                continue
            bases_str = match.group(2)
            return [
                terminal
                for base_part in bases_str.split(",")
                if (stripped := base_part.strip())
                if (
                    terminal := stripped
                    .split("[", maxsplit=1)[0]
                    .strip()
                    .rsplit(".", maxsplit=1)[-1]
                )
            ]
        return []

    @staticmethod
    def parse_all_class_bases(source: str) -> Sequence[m.Infra.ClassInfo]:
        """Extract class info (name, line, bases) for every class in *source*.

        Line-by-line regex scan — useful when rope cannot resolve imported bases.
        """
        result: MutableSequence[m.Infra.ClassInfo] = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            match = c.Infra.CLASS_WITH_BASES_RE.match(line)
            if not match:
                continue
            name = match.group(1)
            bases: list[str] = [
                terminal
                for base_part in match.group(2).split(",")
                if (stripped := base_part.strip())
                if (
                    terminal := stripped
                    .split("[", maxsplit=1)[0]
                    .strip()
                    .rsplit(".", maxsplit=1)[-1]
                )
            ]
            result.append(
                m.Infra.ClassInfo(
                    name=name,
                    line=lineno,
                    bases=tuple(bases),
                )
            )
        return result


__all__ = ["FlextInfraUtilitiesParsing"]
