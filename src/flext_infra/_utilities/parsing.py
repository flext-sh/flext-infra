"""Parsing utilities for infrastructure code analysis.

All AST access is deferred to function bodies via ``import ast`` to keep the
module-level namespace free of ast/cst imports. Import parsing, alias scanning,
and rule normalization live in this namespace as part of the same parsing
domain.
"""

from __future__ import annotations

import ast
import contextlib
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from pydantic import BaseModel, TypeAdapter, ValidationError

from flext_cli import FlextCliUtilitiesToml as _CliToml, u
from flext_infra import (
    FlextInfraConstantsRefactor,
    FlextInfraModelsRefactorGrep,
    FlextInfraModelsRope,
    FlextInfraProtocols,
    FlextInfraTypes,
    FlextInfraTypesAdapters,
    FlextInfraTypesBase,
    c,
    r,
)


class FlextInfraUtilitiesParsing(_CliToml):
    """Static parsing utilities for Python source and import analysis."""

    _DOCSTRING_QUOTES = ('"""', "'''")
    _SINGLE_LINE_DOCSTRING_QUOTE_COUNT = 2
    _RULE_CONFIG_SEQ_ADAPTER: TypeAdapter[
        Sequence[FlextInfraModelsRefactorGrep.ImportModernizerRuleConfig]
    ] = TypeAdapter(
        Sequence[FlextInfraModelsRefactorGrep.ImportModernizerRuleConfig],
    )

    @staticmethod
    def parse_module_ast(file_path: Path) -> FlextInfraTypesBase.AstModule | None:
        """Parse a Python file into an AST module."""
        try:
            return ast.parse(
                file_path.read_text(encoding=c.Infra.Encoding.DEFAULT),
            )
        except (OSError, SyntaxError):
            return None

    @staticmethod
    def is_module_toplevel(file_path: Path) -> bool:
        """Determine if a file is at the package root level (Facade level)."""
        parts = file_path.resolve().parts
        try:
            src_idx = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            return len(parts) == src_idx + 3
        except ValueError:
            return (file_path.parent / c.Infra.Files.INIT_PY).is_file() and not (
                file_path.parent.parent / c.Infra.Files.INIT_PY
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
            if i == 0 and c.Infra.SourceCode.DOCSTRING_RE.match(stripped):
                insert_idx = i + 1
                if not (
                    stripped.count('"""')
                    >= FlextInfraUtilitiesParsing._SINGLE_LINE_DOCSTRING_QUOTE_COUNT
                    or stripped.count("'''")
                    >= FlextInfraUtilitiesParsing._SINGLE_LINE_DOCSTRING_QUOTE_COUNT
                ):
                    in_docstring = True
                continue
            if c.Infra.SourceCode.FUTURE_IMPORT_RE.match(stripped):
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
            if past_existing and c.Infra.SourceCode.IMPORT_LINE_RE.match(line):
                idx = i + 1
                continue
            break
        return idx

    # ------------------------------------------------------------------
    # Dependency / pyproject parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def dep_name(spec: str) -> str:
        """Extract one normalized dependency name from a requirement spec."""
        base = spec.strip().split("@", 1)[0].strip()
        match = c.Infra.DEP_NAME_RE.match(base)
        if match:
            return match.group(1).lower().replace("_", "-")
        return base.lower().replace("_", "-")

    @staticmethod
    def dedupe_specs(
        specs: FlextInfraTypes.StrSequence,
    ) -> FlextInfraTypes.StrSequence:
        """Deduplicate requirement specs by normalized dependency name."""
        seen: dict[str, str] = {}
        for spec in specs:
            key = FlextInfraUtilitiesParsing.dep_name(spec)
            if key and key not in seen:
                seen[key] = spec
        return sorted(seen.values())

    @staticmethod
    def ensure_pyright_execution_envs(
        pyright: FlextInfraTypes.Cli.TomlTable,
        expected: Sequence[FlextInfraTypesBase.ContainerDict]
        | Sequence[FlextInfraProtocols.HasModelDump],
        changes: MutableSequence[str],
    ) -> None:
        """Ensure pyright ``executionEnvironments`` matches one expected payload."""
        raw = FlextInfraUtilitiesParsing.toml_unwrap_item(
            FlextInfraUtilitiesParsing.toml_get_item(pyright, "executionEnvironments")
        )
        current: Sequence[FlextInfraTypes.StrMapping] = []
        if isinstance(raw, list):
            with contextlib.suppress(ValidationError):
                current = TypeAdapter(
                    Sequence[FlextInfraTypes.StrMapping]
                ).validate_python(raw)
        normalized = [
            entry.model_dump(by_alias=True) if isinstance(entry, BaseModel) else entry
            for entry in expected
        ]
        if list(current) != list(normalized):
            pyright["executionEnvironments"] = normalized
            changes.append(
                "tool.pyright.executionEnvironments set with tests reportPrivateUsage=none",
            )

    @staticmethod
    def discover_first_party_namespaces(
        project_dir: Path,
    ) -> FlextInfraTypes.StrSequence:
        """Discover first-party namespaces directly under ``src/``."""
        src_dir = project_dir / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return []
        return [
            entry.name
            for entry in sorted(src_dir.iterdir())
            if entry.is_dir()
            and entry.name != c.Infra.Dunders.PYCACHE
            and entry.name.isidentifier()
            and "-" not in entry.name
        ]

    @staticmethod
    def workspace_dep_namespaces(
        doc: FlextInfraTypes.Cli.TomlDocument,
    ) -> FlextInfraTypes.StrSequence:
        """Return workspace dependency namespaces normalized for Python imports."""
        all_deps = FlextInfraUtilitiesParsing.declared_dependency_names(doc)
        return sorted(
            dep.replace("-", "_")
            for dep in all_deps
            if dep.startswith(c.Infra.Packages.PREFIX_HYPHEN)
        )

    @staticmethod
    def project_dev_groups(
        doc: FlextInfraTypes.Cli.TomlDocument,
    ) -> dict[str, FlextInfraTypes.StrSequence]:
        """Extract optional dependency groups from the ``project`` table."""
        project_raw = FlextInfraUtilitiesParsing.toml_get_table(
            doc,
            c.Infra.PROJECT,
        )
        if project_raw is None:
            return {}
        optional_raw = FlextInfraUtilitiesParsing.toml_get_table(
            project_raw,
            c.Infra.OPTIONAL_DEPENDENCIES,
        )
        if optional_raw is None:
            return {}

        def _group_values(group_key: str) -> FlextInfraTypes.StrSequence:
            value = FlextInfraUtilitiesParsing.toml_get_item(optional_raw, group_key)
            return FlextInfraUtilitiesParsing.toml_as_string_list(value)

        return {
            c.Infra.DEV: _group_values(c.Infra.DEV),
            c.Infra.Directories.DOCS: _group_values(c.Infra.DOCS),
            c.Infra.SECURITY: _group_values(c.Infra.SECURITY),
            c.Infra.TEST: _group_values(c.Infra.TEST),
            c.Infra.Directories.TYPINGS: _group_values(c.Infra.Directories.TYPINGS),
        }

    @staticmethod
    def declared_dependency_names(
        doc: FlextInfraTypes.Cli.TomlDocument,
    ) -> FlextInfraTypes.StrSequence:
        """Extract normalized dependency names from supported dependency groups."""
        raw: FlextInfraTypesBase.TomlData = doc.unwrap()
        names: set[str] = set()

        def _collect(items: FlextInfraTypesBase.InfraValue) -> None:
            if not isinstance(items, Sequence) or isinstance(items, str):
                return
            for item in items:
                if not isinstance(item, str):
                    continue
                dep = FlextInfraUtilitiesParsing.dep_name(item)
                if dep:
                    names.add(dep)

        project_val = raw.get(c.Infra.PROJECT)
        if u.is_mapping(project_val):
            _collect(project_val.get(c.Infra.DEPENDENCIES))
            optional_val = project_val.get(c.Infra.OPTIONAL_DEPENDENCIES)
            if u.is_mapping(optional_val):
                for specs in optional_val.values():
                    _collect(specs)

        groups_val = raw.get("dependency-groups")
        if u.is_mapping(groups_val):
            for specs in groups_val.values():
                _collect(specs)

        tool_val = raw.get(c.Infra.TOOL)
        if not u.is_mapping(tool_val):
            return sorted(names)
        poetry_val = tool_val.get(c.Infra.POETRY)
        if not u.is_mapping(poetry_val):
            return sorted(names)
        deps_val = poetry_val.get(c.Infra.DEPENDENCIES)
        if not u.is_mapping(deps_val):
            return sorted(names)
        for dep_key in deps_val:
            dep = FlextInfraUtilitiesParsing.dep_name(str(dep_key))
            if dep and dep != c.Infra.PYTHON:
                names.add(dep)
        return sorted(names)

    @staticmethod
    def canonical_dev_dependencies(
        root_doc: FlextInfraTypes.Cli.TomlDocument,
    ) -> FlextInfraTypes.StrSequence:
        """Merge and deduplicate all canonical dev dependency groups."""
        groups = FlextInfraUtilitiesParsing.project_dev_groups(root_doc)
        merged = [
            *groups.get(c.Infra.DEV, []),
            *groups.get(c.Infra.Directories.DOCS, []),
            *groups.get(c.Infra.SECURITY, []),
            *groups.get(c.Infra.TEST, []),
            *groups.get(c.Infra.Directories.TYPINGS, []),
        ]
        return FlextInfraUtilitiesParsing.dedupe_specs(merged)

    @staticmethod
    def read_plain(path: Path) -> r[FlextInfraTypesBase.ContainerDict]:
        """Read one TOML file as a plain infra mapping."""
        result = FlextInfraUtilitiesParsing.toml_read_json(path)
        if result.is_failure:
            if not path.exists():
                return r[FlextInfraTypesBase.ContainerDict].ok({})
            return r[FlextInfraTypesBase.ContainerDict].fail(
                result.error or f"TOML read error: {path}",
            )
        try:
            data = FlextInfraTypesAdapters.INFRA_MAPPING_ADAPTER.validate_python(
                result.value
            )
        except ValidationError as exc:
            return r[FlextInfraTypesBase.ContainerDict].fail(f"TOML read error: {exc}")
        return r[FlextInfraTypesBase.ContainerDict].ok(data)

    # ── Generic AST helpers (shared across validate/refactor/codegen) ──

    @staticmethod
    def ast_expr_name(node: FlextInfraTypesBase.AstExpr) -> str:
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
        node: FlextInfraTypesBase.AstExpr | None,
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
    def parse_import_names(names_str: str) -> Sequence[FlextInfraTypesBase.StrPair]:
        """Parse 'A, B as C, D' into [(name, bound), ...]."""
        result: MutableSequence[FlextInfraTypesBase.StrPair] = []
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
    def parse_param_names(params_str: str) -> FlextInfraTypesBase.StrSet:
        """Parse parameter names from a function signature string."""
        names: FlextInfraTypesBase.StrSet = set()
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
    ) -> FlextInfraTypesBase.StrSet:
        """Collect bound names imported from a target module."""
        rh = FlextInfraUtilitiesParsing
        bound_names: FlextInfraTypesBase.StrSet = set()
        for match in c.Infra.SourceCode.FROM_IMPORT_RE.finditer(source):
            if match.group(1) != module_name:
                continue
            bound_names.update(
                bound for _name, bound in rh.parse_import_names(match.group(2))
            )
        for match in c.Infra.SourceCode.FROM_IMPORT_BLOCK_RE.finditer(source):
            if match.group(1) != module_name:
                continue
            bound_names.update(
                bound for _name, bound in rh.parse_import_names(match.group(2))
            )
        return bound_names

    @staticmethod
    def parse_forbidden_rules(
        value: FlextInfraTypesBase.InfraValue,
    ) -> Sequence[FlextInfraModelsRefactorGrep.ImportModernizerRuleConfig]:
        """Parse and validate forbidden import rule configs."""
        try:
            raw_items: Sequence[FlextInfraTypesBase.ContainerDict] = (
                FlextInfraTypesAdapters.CONTAINER_DICT_SEQ_ADAPTER.validate_python(
                    value
                )
            )
        except ValidationError:
            return []
        normalized: Sequence[FlextInfraTypesBase.ContainerDict] = [
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
        runtime_aliases: FlextInfraTypesBase.StrSet,
    ) -> FlextInfraTypesBase.StrSet:
        """Collect aliases blocked by definitions, non-core imports, and assignments."""
        rh = FlextInfraUtilitiesParsing
        blocked: FlextInfraTypesBase.StrSet = set()
        for match in c.Infra.SourceCode.DEF_CLASS_RE.finditer(source):
            name = match.group(1)
            if name in runtime_aliases:
                blocked.add(name)
        for match in c.Infra.SourceCode.FROM_IMPORT_RE.finditer(source):
            module = match.group(1)
            if module == c.Infra.Packages.CORE_UNDERSCORE:
                continue
            for _name, bound in rh.parse_import_names(match.group(2)):
                if bound in runtime_aliases:
                    blocked.add(bound)
        for match in c.Infra.SourceCode.IMPORT_RE.finditer(source):
            for _name, bound in rh.parse_import_names(match.group(1)):
                if bound in runtime_aliases:
                    blocked.add(bound)
        for match in c.Infra.SourceCode.ASSIGN_RE.finditer(source):
            name = match.group(1)
            if name in runtime_aliases:
                blocked.add(name)
        return blocked

    @staticmethod
    def collect_shadowed_aliases(
        source: str,
        runtime_aliases: FlextInfraTypesBase.StrSet,
    ) -> FlextInfraTypesBase.StrSet:
        """Collect runtime-alias names shadowed inside function bodies."""
        shadowed: FlextInfraTypesBase.StrSet = set()
        for match in c.Infra.SourceCode.FUNC_PARAM_RE.finditer(source):
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
    ) -> Sequence[FlextInfraModelsRefactorGrep.MROSymbolCandidate]:
        """Find module-level Final-annotated constants via regex."""
        candidates: MutableSequence[
            FlextInfraModelsRefactorGrep.MROSymbolCandidate
        ] = []
        for i, line in enumerate(source.splitlines(), start=1):
            stripped = line.lstrip()
            if line != stripped and stripped:
                continue
            match = c.Infra.SourceCode.FINAL_ASSIGN_RE.match(stripped)
            if (
                match
                and c.Infra.SourceCode.CONSTANT_NAME_RE.match(match.group(1))
                is not None
            ):
                candidates.append(
                    FlextInfraModelsRefactorGrep.MROSymbolCandidate(
                        symbol=match.group(1),
                        line=i,
                    ),
                )
        return candidates

    @staticmethod
    def first_constants_class_name(source: str) -> str:
        """Find the first class ending with Constants suffix."""
        for match in c.Infra.SourceCode.CLASS_NAME_RE.finditer(source):
            name = match.group(1)
            if name.endswith(FlextInfraConstantsRefactor.CONSTANTS_CLASS_SUFFIX):
                return name
        return ""

    @staticmethod
    def parse_class_bases(source: str, class_name: str) -> Sequence[str]:
        """Extract base class names from a named class definition in source code.

        Finds the class matching *class_name* in *source*, parses its base classes,
        and returns the terminal (unqualified, unsubscripted) names in declaration order.
        Returns an empty sequence when the class is not found.
        """
        for match in c.Infra.SourceCode.CLASS_WITH_BASES_RE.finditer(source):
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
    def parse_all_class_bases(source: str) -> Sequence[FlextInfraModelsRope.ClassInfo]:
        """Extract class info (name, line, bases) for every class in *source*.

        Line-by-line regex scan — useful when rope cannot resolve imported bases.
        """
        result: MutableSequence[FlextInfraModelsRope.ClassInfo] = []
        for lineno, line in enumerate(source.splitlines(), start=1):
            match = c.Infra.SourceCode.CLASS_WITH_BASES_RE.match(line)
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
                FlextInfraModelsRope.ClassInfo(
                    name=name,
                    line=lineno,
                    bases=tuple(bases),
                )
            )
        return result


__all__ = ["FlextInfraUtilitiesParsing"]
