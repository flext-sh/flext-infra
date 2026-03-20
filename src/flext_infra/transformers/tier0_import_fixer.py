"""Detect and rewrite forbidden Tier-0 self-import alias patterns."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import FlextInfraTransformerImportInsertion, ProjectAliasDiscovery


@dataclass(slots=True)
class Tier0ImportAnalysis:
    package_name: str
    alias_to_module: dict[str, str]
    category_a: set[str] = field(default_factory=lambda: set[str]())
    category_b: set[str] = field(default_factory=lambda: set[str]())
    category_c: set[str] = field(default_factory=lambda: set[str]())
    category_d: set[str] = field(default_factory=lambda: set[str]())

    @property
    def has_violations(self) -> bool:
        """Return whether categories B/C/D contain any violations."""
        return bool(self.category_b or self.category_c or self.category_d)


class Tier0ImportCstTools:
    @staticmethod
    def module_name(expr: cst.BaseExpression | None) -> str:
        if expr is None:
            return ""
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            prefix = Tier0ImportCstTools.module_name(expr.value)
            return f"{prefix}.{expr.attr.value}" if prefix else expr.attr.value
        return ""

    @staticmethod
    def is_type_checking_test(node: cst.BaseExpression) -> bool:
        if isinstance(node, cst.Name):
            return node.value == "TYPE_CHECKING"
        if isinstance(node, cst.Attribute):
            return (
                isinstance(node.value, cst.Name)
                and node.value.value == "typing"
                and node.attr.value == "TYPE_CHECKING"
            )
        return False

    @staticmethod
    def collect_bound_names(node: cst.ImportFrom) -> set[str]:
        if isinstance(node.names, cst.ImportStar):
            return set()
        names: set[str] = set()
        for item in node.names:
            if not isinstance(item.name, cst.Name):
                continue
            if item.asname is not None and isinstance(item.asname.name, cst.Name):
                names.add(item.asname.name.value)
            else:
                names.add(item.name.value)
        return names

    @staticmethod
    def import_line(module_name: str, aliases: list[str]) -> cst.SimpleStatementLine:
        root, *rest = module_name.split(".")
        module_expr: cst.BaseExpression = cst.Name(root)
        for part in rest:
            module_expr = cst.Attribute(value=module_expr, attr=cst.Name(part))
        return cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=module_expr,
                    names=tuple(
                        cst.ImportAlias(name=cst.Name(alias)) for alias in aliases
                    ),
                ),
            ],
        )


class Tier0ImportContextDiscovery:
    def __init__(self, *, file_path: Path) -> None:
        self._file_path = file_path

    @property
    def file_path(self) -> Path:
        return self._file_path

    def package_context(self) -> tuple[Path, str]:
        parts = self._file_path.parts
        if "src" not in parts:
            return (self._file_path.parent, "")
        src_idx = parts.index("src")
        if src_idx + 1 >= len(parts):
            return (self._file_path.parent, "")
        package_dir = Path(*parts[: src_idx + 2])
        return (package_dir, parts[src_idx + 1])

    def alias_map(self, *, package_dir: Path, package_name: str) -> dict[str, str]:
        discovered = ProjectAliasDiscovery.discover_facade_alias_map(package_dir)
        alias_map = {
            alias: module.removesuffix(".py")
            for alias, module in discovered.items()
            if module.endswith(".py")
        }
        alias_map.update(
            self._lazy_alias_map(
                package_init=package_dir / "__init__.py",
                package_name=package_name,
            ),
        )
        return alias_map

    def _lazy_alias_map(
        self, *, package_init: Path, package_name: str
    ) -> dict[str, str]:
        if not package_init.exists():
            return {}
        try:
            tree = cst.parse_module(package_init.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return {}
        for stmt_line in tree.body:
            if not isinstance(stmt_line, cst.SimpleStatementLine):
                continue
            for stmt in stmt_line.body:
                if (
                    isinstance(stmt, cst.AnnAssign)
                    and isinstance(stmt.target, cst.Name)
                    and stmt.target.value == "_LAZY_IMPORTS"
                ):
                    return self._extract_lazy_aliases(stmt.value, package_name)
        return {}

    def _extract_lazy_aliases(
        self,
        value: cst.BaseExpression | None,
        package_name: str,
    ) -> dict[str, str]:
        if not isinstance(value, cst.Dict):
            return {}
        result: dict[str, str] = {}
        for element in value.elements:
            if not isinstance(element, cst.DictElement):
                continue
            if not isinstance(element.key, cst.SimpleString):
                continue
            key = element.key.evaluated_value
            if (
                not isinstance(key, str)
                or len(key) != 1
                or not key.isalpha()
                or not key.islower()
            ):
                continue
            if (
                not isinstance(element.value, cst.Tuple)
                or len(element.value.elements) < 1
            ):
                continue
            first = element.value.elements[0].value
            if not isinstance(first, cst.SimpleString):
                continue
            module_path = first.evaluated_value
            if not isinstance(module_path, str) or not module_path.startswith(
                f"{package_name}."
            ):
                continue
            result[key] = module_path.split(".")[-1]
        return result


class Tier0ImportAnalyzer(cst.CSTVisitor):
    def __init__(
        self,
        *,
        file_path: Path,
        tier0_modules: tuple[str, ...],
        core_aliases: tuple[str, ...],
    ) -> None:
        """Initialize analyzer state for one target file and tier configuration."""
        self._discovery = Tier0ImportContextDiscovery(file_path=file_path)
        self._tier0_modules = {name.removesuffix(".py") for name in tier0_modules}
        self._core_aliases = set(core_aliases)
        self._package_name = ""
        self._alias_to_module: dict[str, str] = {}
        self._import_depth = 0
        self._annotation_depth = 0
        self._type_alias_depth = 0
        self._type_checking_depth = 0
        self._self_import_aliases: set[str] = set()
        self._runtime_aliases: set[str] = set()

    def build_analysis(self) -> Tier0ImportAnalysis:
        """Build categorized import-violation analysis from collected aliases."""
        aggregator = self._detect_aggregator_module()
        analysis = Tier0ImportAnalysis(
            package_name=self._package_name,
            alias_to_module=dict(self._alias_to_module),
        )
        for alias in sorted(self._self_import_aliases):
            module_name = self._alias_to_module.get(alias, "")
            if alias in self._core_aliases or (
                aggregator and module_name == aggregator
            ):
                analysis.category_b.add(alias)
            elif module_name in self._tier0_modules:
                analysis.category_a.add(alias)
            elif alias in self._runtime_aliases:
                analysis.category_d.add(alias)
            else:
                analysis.category_c.add(alias)
        return analysis

    def _detect_aggregator_module(self) -> str:
        """Detect if file is inside _<dir>/ and return the aggregator module name.

        Files inside _models/ have aggregator 'models', _utilities/ has 'utilities'.
        Returns empty string if file is not inside an internal subpackage.
        """
        parts = self._discovery.file_path.parts
        for part in parts:
            if part.startswith("_") and not part.startswith("__"):
                return part.lstrip("_")
        return ""

    @override
    def visit_Module(self, node: cst.Module) -> None:
        del node
        package_dir, package_name = self._discovery.package_context()
        self._package_name = package_name
        if package_name:
            self._alias_to_module = self._discovery.alias_map(
                package_dir=package_dir,
                package_name=package_name,
            )

    @override
    def visit_Import(self, node: cst.Import) -> None:
        del node
        self._import_depth += 1

    @override
    def leave_Import(self, original_node: cst.Import) -> None:
        del original_node
        self._import_depth = max(0, self._import_depth - 1)

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        self._import_depth += 1
        if not self._package_name or node.module is None or node.relative:
            return
        if Tier0ImportCstTools.module_name(node.module) != self._package_name:
            return
        if isinstance(node.names, cst.ImportStar):
            return
        for item in node.names:
            if not isinstance(item.name, cst.Name):
                continue
            bound = item.name.value
            if item.asname is not None and isinstance(item.asname.name, cst.Name):
                bound = item.asname.name.value
            if len(bound) == 1 and bound.islower() and bound.isalpha():
                self._self_import_aliases.add(bound)

    @override
    def leave_ImportFrom(self, original_node: cst.ImportFrom) -> None:
        del original_node
        self._import_depth = max(0, self._import_depth - 1)

    @override
    def visit_Annotation(self, node: cst.Annotation) -> None:
        del node
        self._annotation_depth += 1

    @override
    def leave_Annotation(self, original_node: cst.Annotation) -> None:
        del original_node
        self._annotation_depth = max(0, self._annotation_depth - 1)

    @override
    def visit_TypeAlias(self, node: cst.TypeAlias) -> None:
        del node
        self._type_alias_depth += 1

    @override
    def leave_TypeAlias(self, original_node: cst.TypeAlias) -> None:
        del original_node
        self._type_alias_depth = max(0, self._type_alias_depth - 1)

    @override
    def visit_If(self, node: cst.If) -> None:
        if Tier0ImportCstTools.is_type_checking_test(node.test):
            self._type_checking_depth += 1

    @override
    def leave_If(self, original_node: cst.If) -> None:
        if Tier0ImportCstTools.is_type_checking_test(original_node.test):
            self._type_checking_depth = max(0, self._type_checking_depth - 1)

    @override
    def visit_Name(self, node: cst.Name) -> None:
        if node.value not in self._self_import_aliases or self._import_depth > 0:
            return
        if self._type_alias_depth > 0:
            self._runtime_aliases.add(node.value)
            return
        if self._annotation_depth > 0 or self._type_checking_depth > 0:
            return
        self._runtime_aliases.add(node.value)


class Tier0ImportFixer(cst.CSTTransformer):
    def __init__(
        self,
        *,
        analysis: Tier0ImportAnalysis,
        alias_to_submodule: dict[str, str],
        core_package: str,
    ) -> None:
        """Initialize fixer state from analyzer output and alias resolution map."""
        self.analysis = analysis
        self._package_name = analysis.package_name
        self._core_package = core_package
        self._root_remove = (
            set(analysis.category_b)
            | set(analysis.category_c)
            | set(analysis.category_d)
        )
        self._core_pending = set(analysis.category_b)
        self._type_checking_pending = set(analysis.category_c)
        self._direct_pending: dict[str, set[str]] = {}
        for alias in sorted(analysis.category_d):
            submodule = alias_to_submodule.get(
                alias, analysis.alias_to_module.get(alias, "")
            )
            if submodule:
                self._direct_pending.setdefault(submodule, set()).add(alias)
        self._changes: list[str] = []
        self._type_checking_depth = 0
        self._type_checking_import_present = False

    @property
    def changes(self) -> list[str]:
        """Return accumulated human-readable change descriptions."""
        return self._changes

    @override
    def visit_If(self, node: cst.If) -> None:
        if Tier0ImportCstTools.is_type_checking_test(node.test):
            self._type_checking_depth += 1

    @override
    def leave_If(
        self, original_node: cst.If, updated_node: cst.If
    ) -> cst.BaseStatement:
        if not Tier0ImportCstTools.is_type_checking_test(original_node.test):
            return updated_node
        self._type_checking_depth = max(0, self._type_checking_depth - 1)
        return self._merge_type_checking_imports(updated_node)

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        del original_node
        module_name = Tier0ImportCstTools.module_name(updated_node.module)
        if module_name == "typing" and (
            "TYPE_CHECKING" in Tier0ImportCstTools.collect_bound_names(updated_node)
        ):
            self._type_checking_import_present = True
        if module_name == self._package_name and self._type_checking_depth == 0:
            return self._rewrite_root_self_import(updated_node)
        if module_name == self._core_package:
            return self._merge_into_import(updated_node, self._core_pending)
        for submodule, pending in self._direct_pending.items():
            if module_name == f"{self._package_name}.{submodule}":
                return self._merge_into_import(updated_node, pending)
        return updated_node

    @override
    def leave_Module(
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        del original_node
        body = list(updated_node.body)
        insert_idx = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
            body,
        )
        additions = self._build_top_level_imports()
        if additions:
            body = body[:insert_idx] + additions + body[insert_idx:]
        if self._type_checking_pending:
            if not self._type_checking_import_present:
                import_stmt = Tier0ImportCstTools.import_line(
                    "typing", ["TYPE_CHECKING"]
                )
                body = body[:insert_idx] + [import_stmt] + body[insert_idx:]
                self._changes.append("Added import: from typing import TYPE_CHECKING")
            block = cst.If(
                test=cst.Name("TYPE_CHECKING"),
                body=cst.IndentedBlock(
                    body=[
                        Tier0ImportCstTools.import_line(
                            self._package_name,
                            sorted(self._type_checking_pending),
                        ),
                    ],
                ),
            )
            block_idx = self._index_after_import_block(body)
            body = body[:block_idx] + [block] + body[block_idx:]
            self._changes.append(
                "Added TYPE_CHECKING block for annotation-only aliases"
            )
            self._type_checking_pending.clear()
        return updated_node.with_changes(body=body)

    def _rewrite_root_self_import(
        self,
        node: cst.ImportFrom,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        if isinstance(node.names, cst.ImportStar):
            return node
        kept: list[cst.ImportAlias] = []
        removed: list[str] = []
        for item in node.names:
            if not isinstance(item.name, cst.Name):
                kept.append(item)
                continue
            bound = item.name.value
            if item.asname is not None and isinstance(item.asname.name, cst.Name):
                bound = item.asname.name.value
            if bound in self._root_remove:
                removed.append(bound)
            else:
                kept.append(item)
        if not removed:
            return node
        self._changes.append(
            f"Removed self-import aliases: {', '.join(sorted(removed))}"
        )
        if not kept:
            return cst.RemovalSentinel.REMOVE
        cleaned = list(kept)
        cleaned[-1] = cleaned[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
        return node.with_changes(names=tuple(cleaned))

    def _merge_into_import(
        self,
        node: cst.ImportFrom,
        pending: set[str],
    ) -> cst.BaseSmallStatement:
        if len(pending) == 0 or isinstance(node.names, cst.ImportStar):
            return node
        existing = Tier0ImportCstTools.collect_bound_names(node)
        missing = sorted(alias for alias in pending if alias not in existing)
        if not missing:
            return node
        pending.difference_update(missing)
        self._changes.append(
            f"Merged import aliases into {Tier0ImportCstTools.module_name(node.module)}: {', '.join(missing)}",
        )
        return node.with_changes(
            names=tuple(
                list(node.names) + [cst.ImportAlias(name=cst.Name(x)) for x in missing]
            ),
        )

    def _merge_type_checking_imports(self, node: cst.If) -> cst.If:
        if len(self._type_checking_pending) == 0 or not isinstance(
            node.body, cst.IndentedBlock
        ):
            return node
        statements = list(node.body.body)
        for idx, stmt in enumerate(statements):
            if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
                continue
            single = stmt.body[0]
            if not isinstance(single, cst.ImportFrom):
                continue
            if Tier0ImportCstTools.module_name(single.module) != self._package_name:
                continue
            merged = self._merge_into_import(single, self._type_checking_pending)
            statements[idx] = stmt.with_changes(body=[merged])
            if len(self._type_checking_pending) == 0:
                break
        if self._type_checking_pending:
            aliases = sorted(self._type_checking_pending)
            statements.append(
                Tier0ImportCstTools.import_line(self._package_name, aliases)
            )
            self._changes.append(
                f"Added TYPE_CHECKING imports from {self._package_name}: {', '.join(aliases)}",
            )
            self._type_checking_pending.clear()
        return node.with_changes(body=node.body.with_changes(body=tuple(statements)))

    def _build_top_level_imports(self) -> list[cst.BaseStatement]:
        additions: list[cst.BaseStatement] = []
        if self._core_pending:
            aliases = sorted(self._core_pending)
            additions.append(
                Tier0ImportCstTools.import_line(self._core_package, aliases)
            )
            self._changes.append(
                f"Added core alias redirect import from {self._core_package}: {', '.join(aliases)}",
            )
            self._core_pending.clear()
        for submodule in sorted(self._direct_pending):
            pending = self._direct_pending[submodule]
            if not pending:
                continue
            aliases = sorted(pending)
            module_name = f"{self._package_name}.{submodule}"
            additions.append(Tier0ImportCstTools.import_line(module_name, aliases))
            self._changes.append(
                f"Added direct submodule imports from {module_name}: {', '.join(aliases)}",
            )
            pending.clear()
        return additions

    def _index_after_import_block(self, body: Sequence[cst.BaseStatement]) -> int:
        index = FlextInfraTransformerImportInsertion.index_after_docstring_and_future_imports(
            body,
        )
        while index < len(body):
            stmt = body[index]
            if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
                break
            if not isinstance(stmt.body[0], (cst.Import, cst.ImportFrom)):
                break
            index += 1
        return index


__all__ = [
    "Tier0ImportAnalysis",
    "Tier0ImportAnalyzer",
    "Tier0ImportFixer",
]
