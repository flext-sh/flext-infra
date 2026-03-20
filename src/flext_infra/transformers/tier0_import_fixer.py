"""CST transformer for fixing circular Tier 0 self-imports in internal modules."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import FlextInfraTransformerImportInsertion, u
from flext_infra.transformers.project_discovery import ProjectAliasDiscovery


class FlextInfraTransformerTier0ImportFixer:
    """Namespace for Tier 0 import fixing logic and classes."""

    @dataclass(frozen=True)
    class Analysis:
        """Detection results for a single Python file's self-import patterns."""

        package_name: str
        file_path: Path
        alias_to_module: dict[str, str] = field(default_factory=dict)
        category_a: set[str] = field(default_factory=set)
        category_b: set[str] = field(default_factory=set)
        category_c: set[str] = field(default_factory=set)
        category_d: set[str] = field(default_factory=set)

        @property
        def has_violations(self) -> bool:
            """Return True if any imports need redirecting or moving."""
            return bool(self.category_b or self.category_c or self.category_d)

    class ContextDiscovery:
        """Discovery logic for package context and alias mappings."""

        def __init__(self, *, file_path: Path) -> None:
            self._file_path = file_path

        @property
        def file_path(self) -> Path:
            return self._file_path

        def package_context(self) -> tuple[Path, str]:
            """Return (package_dir, package_name) for the current file."""
            parts = self._file_path.parts
            if "src" not in parts:
                return (self._file_path.parent, "")
            src_idx = parts.index("src")
            if src_idx + 1 >= len(parts):
                return (self._file_path.parent, "")
            package_dir = Path(*parts[: src_idx + 2])
            return (package_dir, parts[src_idx + 1])

        def alias_map(self, *, package_dir: Path, package_name: str) -> dict[str, str]:
            """Build map of single-char aliases to their defining modules."""
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
                key_text = u.Infra.extract_string_literal(element.key)
                if (
                    len(key_text) != 1
                    or not key_text.isalpha()
                    or not key_text.islower()
                    or not isinstance(element.value, (cst.Tuple, cst.List))
                ):
                    continue
                if len(element.value.elements) == 0:
                    continue
                module_element = element.value.elements[0]
                module_name = u.Infra.extract_string_literal(module_element.value)
                if not module_name or not module_name.startswith(f"{package_name}."):
                    continue
                result[key_text] = module_name.split(".")[-1]
            return result

    class Analyzer(cst.CSTVisitor):
        """Analyze imports and names to identify circular Tier 0 aliases."""

        def __init__(
            self,
            *,
            file_path: Path,
            tier0_modules: tuple[str, ...],
            core_aliases: tuple[str, ...],
        ) -> None:
            """Initialize analyzer state for one target file."""
            self._discovery = FlextInfraTransformerTier0ImportFixer.ContextDiscovery(
                file_path=file_path,
            )
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

        def _is_facade_file(self) -> bool:
            """Determine if current file is a package facade (Tier 0)."""
            name = self._discovery.file_path.name
            # 1. Must match facade name pattern
            is_facade_name = name.removesuffix(".py") in self._tier0_modules or (
                name.startswith("_")
                and name.removesuffix(".py")[1:] in self._tier0_modules
            )
            if not is_facade_name:
                return False

            # 2. Must be directly under src/<package_name>/
            parts = self._discovery.file_path.parts
            try:
                src_idx = parts.index("src")
                return len(parts) == src_idx + 3
            except ValueError:
                return True

        def build_analysis(self) -> FlextInfraTransformerTier0ImportFixer.Analysis:
            """Process visited nodes and build violation analysis."""
            package_dir, self._package_name = self._discovery.package_context()
            if not self._package_name:
                return FlextInfraTransformerTier0ImportFixer.Analysis(
                    package_name="",
                    file_path=self._discovery.file_path,
                )

            self._alias_to_module = self._discovery.alias_map(
                package_dir=package_dir,
                package_name=self._package_name,
            )

            analysis = FlextInfraTransformerTier0ImportFixer.Analysis(
                package_name=self._package_name,
                file_path=self._discovery.file_path,
                alias_to_module=self._alias_to_module,
            )

            if self._is_facade_file():
                analysis.category_a.update(self._self_import_aliases)
                return analysis

            aggregator = self._detect_aggregator_module()

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
            parts = self._discovery.file_path.parts
            for part in parts:
                if part.startswith("_") and not part.startswith("__"):
                    return part.lstrip("_")
            return ""

        @override
        def visit_Import(self, node: cst.Import) -> None:
            self._import_depth += 1

        @override
        def leave_Import(self, original_node: cst.Import) -> None:
            self._import_depth = max(0, self._import_depth - 1)

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
            self._import_depth += 1
            if not self._package_name or node.module is None or node.relative:
                return
            if u.Infra.cst_module_name(node.module) != self._package_name:
                return
            if isinstance(node.names, cst.ImportStar):
                return
            for item in node.names:
                bound = u.Infra.cst_asname_to_local(item.asname) or (
                    item.name.value if isinstance(item.name, cst.Name) else ""
                )
                if len(bound) == 1 and bound.islower() and bound.isalpha():
                    self._self_import_aliases.add(bound)

        @override
        def leave_ImportFrom(self, original_node: cst.ImportFrom) -> None:
            self._import_depth = max(0, self._import_depth - 1)

        @override
        def visit_Annotation(self, node: cst.Annotation) -> None:
            self._annotation_depth += 1

        @override
        def leave_Annotation(self, original_node: cst.Annotation) -> None:
            self._annotation_depth = max(0, self._annotation_depth - 1)

        @override
        def visit_TypeAlias(self, node: cst.TypeAlias) -> None:
            self._type_alias_depth += 1

        @override
        def leave_TypeAlias(self, original_node: cst.TypeAlias) -> None:
            self._type_alias_depth = max(0, self._type_alias_depth - 1)

        @override
        def visit_If(self, node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(node.test):
                self._type_checking_depth += 1

        @override
        def leave_If(self, original_node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(original_node.test):
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

    class Transformer(cst.CSTTransformer):
        """Rewrite Tier 0 imports to remove circularity and enforce order."""

        _CLASS_IMPORTS_MAP = {
            "FlextRuntime": "flext_core.runtime",
            "FlextUtilitiesGuardsTypeCore": "flext_core._utilities.guards_type_core",
            "FlextUtilitiesGuards": "flext_core._utilities.guards",
            "FlextUtilitiesGuardsType": "flext_core._utilities.guards_type",
            "FlextUtilitiesCache": "flext_core._utilities.cache",
            "FlextUtilitiesMapper": "flext_core._utilities.mapper",
            "FlextUtilitiesModel": "flext_core._utilities.model",
            "EnumT": "flext_core._typings.generics",
            "T": "flext_core._typings.generics",
            "U": "flext_core._typings.generics",
            "T_Model": "flext_core._typings.generics",
        }

        def __init__(
            self,
            *,
            analysis: FlextInfraTransformerTier0ImportFixer.Analysis,
            alias_to_submodule: dict[str, str],
            core_package: str,
        ) -> None:
            """Initialize fixer state from analysis."""
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
            self._missing_classes: set[str] = set()

        @property
        def changes(self) -> list[str]:
            return self._changes

        @override
        def visit_Module(self, node: cst.Module) -> None:
            source = node.code
            for name in self._CLASS_IMPORTS_MAP:
                if name in source and f"import {name}" not in source:
                    self._missing_classes.add(name)

        @override
        def visit_If(self, node: cst.If) -> None:
            if u.Infra.cst_is_type_checking_test(node.test):
                self._type_checking_depth += 1

        @override
        def leave_If(
            self, original_node: cst.If, updated_node: cst.If
        ) -> cst.BaseStatement:
            if not u.Infra.cst_is_type_checking_test(original_node.test):
                return updated_node
            self._type_checking_depth = max(0, self._type_checking_depth - 1)
            return self._merge_type_checking_imports(updated_node)

        @override
        def leave_ImportFrom(
            self,
            original_node: cst.ImportFrom,
            updated_node: cst.ImportFrom,
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            module_name = u.Infra.cst_module_name(updated_node.module)
            if module_name == "typing" and (
                "TYPE_CHECKING" in u.Infra.cst_collect_bound_names(updated_node)
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
            statements = list(updated_node.body)
            if not self._type_checking_import_present and self._type_checking_pending:
                insert_idx = self._index_after_import_block(statements)
                statements.insert(
                    insert_idx,
                    u.Infra.cst_import_line("typing", ["TYPE_CHECKING"]),
                )
                self._type_checking_import_present = True
                self._changes.append("Added 'from typing import TYPE_CHECKING'")

            additions = self._build_top_level_imports()
            if additions:
                insert_idx = self._index_after_import_block(statements)
                statements[insert_idx:insert_idx] = additions

            if self._type_checking_pending:
                tc_import = u.Infra.cst_import_line(
                    self._package_name, list(self._type_checking_pending)
                )
                tc_block = cst.If(
                    test=cst.Name("TYPE_CHECKING"),
                    body=cst.IndentedBlock(body=[tc_import]),
                )
                insert_idx = self._index_after_import_block(statements)
                statements.insert(insert_idx, tc_block)
                self._changes.append(
                    f"Added TYPE_CHECKING block with imports from {self._package_name}: {', '.join(sorted(self._type_checking_pending))}"
                )
                self._type_checking_pending.clear()

            return updated_node.with_changes(body=tuple(statements))

        def _rewrite_root_self_import(
            self, node: cst.ImportFrom
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            if isinstance(node.names, cst.ImportStar):
                return node
            remaining = []
            for item in node.names:
                bound = u.Infra.cst_asname_to_local(item.asname) or (
                    item.name.value if isinstance(item.name, cst.Name) else ""
                )
                if bound in self._root_remove:
                    self._changes.append(
                        f"Removing '{bound}' from {self._package_name} import"
                    )
                    continue
                remaining.append(item)
            if not remaining:
                return cst.RemovalSentinel.REMOVE
            return node.with_changes(names=tuple(remaining))

        def _merge_into_import(
            self, node: cst.ImportFrom, pending: set[str]
        ) -> cst.ImportFrom:
            if not pending or isinstance(node.names, cst.ImportStar):
                return node
            existing = u.Infra.cst_collect_bound_names(node)
            to_add = [
                cst.ImportAlias(name=cst.Name(a)) for a in sorted(pending - existing)
            ]
            if not to_add:
                return node
            pending.clear()
            return node.with_changes(names=tuple(list(node.names) + to_add))

        def _merge_type_checking_imports(self, node: cst.If) -> cst.BaseStatement:
            if not self._type_checking_pending:
                return node
            statements = list(node.body.body)
            for i, stmt in enumerate(statements):
                if (
                    isinstance(stmt, cst.SimpleStatementLine)
                    and len(stmt.body) == 1
                    and isinstance(stmt.body[0], cst.ImportFrom)
                ) and u.Infra.cst_module_name(stmt.body[0]) == self._package_name:
                    statements[i] = self._merge_into_import(
                        stmt.body[0], self._type_checking_pending
                    )
                    self._changes.append(
                        f"Merged TYPE_CHECKING imports from {self._package_name}"
                    )
                    break
            else:
                aliases = sorted(self._type_checking_pending)
                statements.append(u.Infra.cst_import_line(self._package_name, aliases))
                self._changes.append(
                    f"Added TYPE_CHECKING imports from {self._package_name}: {', '.join(aliases)}",
                )
                self._type_checking_pending.clear()
            return node.with_changes(
                body=node.body.with_changes(body=tuple(statements))
            )

        def _build_top_level_imports(self) -> list[cst.BaseStatement]:
            additions: list[cst.BaseStatement] = []
            if self._core_pending:
                aliases = sorted(self._core_pending)
                additions.append(u.Infra.cst_import_line(self._core_package, aliases))
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
                additions.append(u.Infra.cst_import_line(module_name, aliases))
                self._changes.append(
                    f"Added direct submodule imports from {module_name}: {', '.join(aliases)}",
                )
                pending.clear()

            for name in sorted(self._missing_classes):
                module_path = self._CLASS_IMPORTS_MAP[name]
                additions.append(u.Infra.cst_import_line(module_path, [name]))
                self._changes.append(
                    f"Added missing class import: from {module_path} import {name}"
                )

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


__all__ = ["FlextInfraTransformerTier0ImportFixer"]
