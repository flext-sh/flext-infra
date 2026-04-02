from __future__ import annotations

import re
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Final, override

import libcst as cst

from flext_infra import (
    FlextInfraUtilitiesCodegenConstantDetection,
    FlextInfraUtilitiesParsing,
    c,
    m,
    t,
)


class FlextInfraUtilitiesCodegenConstantTransformation:
    MIN_ATTRIBUTE_CHAIN: Final[int] = 2
    CANONICAL_ALIASES: Final[frozenset[str]] = frozenset([
        "c",
        "d",
        "e",
        "h",
        "m",
        "p",
        "r",
        "s",
        "t",
        "u",
        "x",
    ])

    class CanonicalValueReplacer(cst.CSTTransformer):
        def __init__(
            self,
            *,
            parent_class: str,
            definitions: Sequence[m.Infra.ConstantDefinition],
        ) -> None:
            super().__init__()
            self._parent_class = parent_class
            self._lookup = {
                (
                    item.name,
                    item.value_repr,
                ): FlextInfraUtilitiesCodegenConstantDetection.canonical_reference_for(
                    item.name,
                    item.value_repr,
                )
                for item in definitions
            }
            self.changes: MutableSequence[str] = []
            self.replacements = 0

        @override
        def leave_AnnAssign(
            self,
            original_node: cst.AnnAssign,
            updated_node: cst.AnnAssign,
        ) -> cst.BaseSmallStatement:
            if (
                not isinstance(original_node.target, cst.Name)
                or original_node.value is None
            ):
                return updated_node
            value_repr = cst.parse_module("").code_for_node(original_node.value)
            canonical_ref = self._lookup.get(
                (original_node.target.value, value_repr),
                "",
            )
            if not canonical_ref:
                return updated_node
            self.replacements += 1
            self.changes.append(
                f"replaced {original_node.target.value} -> {canonical_ref}",
            )
            return updated_node.with_changes(
                value=cst.parse_expression(f"{self._parent_class}.{canonical_ref}"),
            )

    class UnusedConstantRemover(cst.CSTTransformer):
        def __init__(self, *, unused_names: t.Infra.StrSet) -> None:
            super().__init__()
            self._unused_names = unused_names
            self._class_stack: MutableSequence[str] = []
            self.changes: MutableSequence[str] = []
            self.removals = 0

        @override
        def visit_ClassDef(self, node: cst.ClassDef) -> None:
            self._class_stack.append(node.name.value)

        @override
        def leave_ClassDef(
            self,
            original_node: cst.ClassDef,
            updated_node: cst.ClassDef,
        ) -> cst.BaseStatement | cst.RemovalSentinel:
            del original_node
            if self._class_stack:
                self._class_stack.pop()
            if updated_node.body.body:
                return updated_node
            self.removals += 1
            self.changes.append("removed empty class")
            return cst.RemovalSentinel.REMOVE

        @override
        def leave_AnnAssign(
            self,
            original_node: cst.AnnAssign,
            updated_node: cst.AnnAssign,
        ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
            del updated_node
            if not isinstance(original_node.target, cst.Name):
                return original_node
            if original_node.target.value not in self._unused_names:
                return original_node
            self.removals += 1
            self.changes.append(
                f"removed {'.'.join(self._class_stack)}.{original_node.target.value}",
            )
            return cst.RemovalSentinel.REMOVE

    class DirectRefAliasNormalizer(cst.CSTTransformer):
        def __init__(self, *, project_import: str, target_class: str) -> None:
            super().__init__()
            self._project_import = project_import
            self._target_class = target_class
            self._has_c_import = False
            self._replaced_classes: t.Infra.StrSet = set()
            self.changes: MutableSequence[str] = []
            self.replacements = 0

        @override
        def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
            if isinstance(node.names, cst.ImportStar):
                return False
            for alias in node.names:
                imported_name = (
                    alias.name.value if isinstance(alias.name, cst.Name) else ""
                )
                local_name = imported_name
                if alias.asname is not None and isinstance(alias.asname.name, cst.Name):
                    local_name = alias.asname.name.value
                if local_name == "c":
                    self._has_c_import = True
            return False

        @override
        def leave_Attribute(
            self,
            original_node: cst.Attribute,
            updated_node: cst.Attribute,
        ) -> cst.BaseExpression:
            del original_node
            chain = FlextInfraUtilitiesCodegenConstantDetection.attribute_chain(
                updated_node,
            )
            if (
                len(chain)
                < FlextInfraUtilitiesCodegenConstantTransformation.MIN_ATTRIBUTE_CHAIN
            ):
                return updated_node
            if chain[0] != self._target_class:
                return updated_node
            self._replaced_classes.add(chain[0])
            rewritten = ".".join(["c", *chain[1:]])
            self.replacements += 1
            self.changes.append(f"{'.'.join(chain)} -> {rewritten}")
            return cst.parse_expression(rewritten)

        def _filter_import_stmt(
            self,
            stmt: cst.SimpleStatementLine,
        ) -> cst.SimpleStatementLine | None:
            """Filter replaced-class imports from a single import statement.

            Returns the updated statement, or None if the import should be removed entirely.
            """
            import_node = stmt.body[0]
            if not isinstance(import_node, cst.ImportFrom) or isinstance(
                import_node.names,
                cst.ImportStar,
            ):
                return stmt
            remaining = [
                alias
                for alias in import_node.names
                if not (
                    isinstance(alias.name, cst.Name)
                    and alias.name.value in self._replaced_classes
                )
            ]
            removed_count = len(import_node.names) - len(remaining)
            if removed_count > 0:
                self.changes.append(f"removed {removed_count} unused import(s)")
            if not remaining:
                return None
            if removed_count > 0:
                cleaned = [
                    a.with_changes(comma=cst.MaybeSentinel.DEFAULT)
                    if i == len(remaining) - 1
                    else a
                    for i, a in enumerate(remaining)
                ]
                return stmt.with_changes(
                    body=[import_node.with_changes(names=cleaned)],
                )
            return stmt

        @override
        def leave_Module(
            self,
            original_node: cst.Module,
            updated_node: cst.Module,
        ) -> cst.Module:
            del original_node
            t = FlextInfraUtilitiesCodegenConstantTransformation
            if self.replacements == 0:
                return updated_node
            new_body: MutableSequence[
                cst.BaseCompoundStatement | cst.SimpleStatementLine
            ] = []
            for stmt in updated_node.body:
                if (
                    isinstance(stmt, cst.SimpleStatementLine)
                    and len(stmt.body) == 1
                    and isinstance(stmt.body[0], cst.ImportFrom)
                    and not isinstance(stmt.body[0].names, cst.ImportStar)
                ):
                    filtered = self._filter_import_stmt(stmt)
                    if filtered is not None:
                        new_body.append(filtered)
                    continue
                new_body.append(stmt)
            if not self._has_c_import:
                new_body.insert(
                    t.import_insert_index(new_body),
                    cst.parse_statement(f"{self._project_import}\n"),
                )
                self.changes.append("added c import")
            return updated_node.with_changes(body=new_body)

    @staticmethod
    def derive_constants_class(
        package_name: str,
        pkg_dir: Path | None = None,
    ) -> str:
        """``flext_dbt_oracle_wms`` -> ``FlextDbtOracleWmsConstants``."""
        if pkg_dir is not None:
            constants_file = pkg_dir / "constants.py"
            if constants_file.is_file():
                tree = FlextInfraUtilitiesParsing.parse_module_cst(constants_file)
                if tree is not None:
                    for stmt in tree.body:
                        if isinstance(stmt, cst.ClassDef):
                            return stmt.name.value
        return (
            "".join(part.capitalize() for part in package_name.split("_")) + "Constants"
        )

    @staticmethod
    def replace_canonical_values(
        file_path: Path,
        parent_class: str,
        definitions: Sequence[m.Infra.ConstantDefinition],
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        t = FlextInfraUtilitiesCodegenConstantTransformation
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if tree is None:
            return False, []
        transformer = t.CanonicalValueReplacer(
            parent_class=parent_class,
            definitions=definitions,
        )
        new_tree = tree.visit(transformer)
        if transformer.replacements > 0:
            file_path.write_text(new_tree.code, encoding=c.Infra.Encoding.DEFAULT)
        return transformer.replacements > 0, transformer.changes

    @staticmethod
    def remove_unused_constants(
        file_path: Path,
        unused: Sequence[m.Infra.UnusedConstant],
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        t = FlextInfraUtilitiesCodegenConstantTransformation
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if tree is None:
            return False, []
        transformer = t.UnusedConstantRemover(
            unused_names={item.name for item in unused},
        )
        new_tree = tree.visit(transformer)
        if transformer.removals > 0:
            file_path.write_text(new_tree.code, encoding=c.Infra.Encoding.DEFAULT)
        return transformer.removals > 0, transformer.changes

    @staticmethod
    def normalize_constant_aliases(
        file_path: Path,
        project_import: str,
        pkg_dir: Path | None = None,
    ) -> t.Infra.Pair[bool, t.StrSequence]:
        t = FlextInfraUtilitiesCodegenConstantTransformation
        parts = project_import.replace("from ", "").split(" import ")
        package_name = parts[0].strip() if parts else ""
        resolved_pkg_dir = pkg_dir
        if resolved_pkg_dir is None and package_name:
            for parent in file_path.parents:
                if parent.name == package_name:
                    resolved_pkg_dir = parent
                    break
        target_class = t.derive_constants_class(package_name, resolved_pkg_dir)
        tree = FlextInfraUtilitiesParsing.parse_module_cst(file_path)
        if tree is None:
            return False, []
        transformer = t.DirectRefAliasNormalizer(
            project_import=project_import,
            target_class=target_class,
        )
        new_tree = tree.visit(transformer)
        if transformer.replacements > 0:
            file_path.write_text(new_tree.code, encoding=c.Infra.Encoding.DEFAULT)
        return transformer.replacements > 0, transformer.changes

    @staticmethod
    def import_insert_index(
        body: Sequence[cst.SimpleStatementLine | cst.BaseCompoundStatement],
    ) -> int:
        index = 0
        if (
            body
            and isinstance(body[0], cst.SimpleStatementLine)
            and len(body[0].body) == 1
            and isinstance(body[0].body[0], cst.Expr)
            and isinstance(body[0].body[0].value, cst.SimpleString)
        ):
            index = 1
        while index < len(body):
            stmt = body[index]
            if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
                break
            import_stmt = stmt.body[0]
            if (
                not isinstance(import_stmt, cst.ImportFrom)
                or import_stmt.module is None
            ):
                break
            if not (
                isinstance(import_stmt.module, cst.Name)
                and import_stmt.module.value == "__future__"
            ):
                break
            index += 1
        return index

    @staticmethod
    def parse_lazy_imports(init_file: Path) -> t.StrMapping:
        """Parse ``__init__.py`` lazy-loading map: alias -> module stem."""
        if not init_file.is_file():
            return {}
        source = init_file.read_text(c.Infra.Encoding.DEFAULT)
        mapping: t.MutableStrMapping = {}
        for match in re.finditer(
            r'"(\w+)":\s*\("([\w.]+)",\s*"(\w+)"\)',
            source,
        ):
            alias, module_path, _export = match.groups()
            mapping[alias] = module_path.rsplit(".", 1)[-1]
        return mapping

    @staticmethod
    def build_self_import_graph(
        pkg_dir: Path,
        package_name: str,
        lazy_map: t.StrMapping,
    ) -> Mapping[str, t.Infra.StrSet]:
        """Build a dependency graph among modules within the same package."""
        graph: MutableMapping[str, t.Infra.StrSet] = {}
        for py_file in pkg_dir.glob("*.py"):
            if py_file.name == c.Infra.Files.INIT_PY:
                continue
            stem = py_file.stem
            tree = FlextInfraUtilitiesParsing.parse_module_cst(py_file)
            if tree is None:
                continue
            deps = FlextInfraUtilitiesCodegenConstantTransformation.collect_module_deps(
                tree,
                stem,
                package_name,
                lazy_map,
            )
            if deps:
                graph[stem] = deps
        return graph

    @staticmethod
    def _deps_from_import(
        imp: cst.ImportFrom,
        tree: cst.Module,
        stem: str,
        package_name: str,
        lazy_map: t.StrMapping,
    ) -> t.Infra.StrSet:
        """Extract intra-package deps from a single ``from X import ...`` node."""
        if isinstance(imp.names, cst.ImportStar):
            return set()
        mod = tree.code_for_node(imp.module) if imp.module else ""
        if mod != package_name:
            return set()
        deps: t.Infra.StrSet = set()
        for alias in imp.names:
            name = alias.name.value if isinstance(alias.name, cst.Name) else ""
            target = lazy_map.get(name)
            if target and target != stem:
                deps.add(target)
        return deps

    @staticmethod
    def collect_module_deps(
        tree: cst.Module,
        stem: str,
        package_name: str,
        lazy_map: t.StrMapping,
    ) -> t.Infra.StrSet:
        """Collect intra-package dependencies for a single parsed module."""
        deps: t.Infra.StrSet = set()
        for stmt in tree.body:
            if not isinstance(stmt, cst.SimpleStatementLine):
                continue
            for small in stmt.body:
                if isinstance(small, cst.ImportFrom):
                    deps.update(
                        FlextInfraUtilitiesCodegenConstantTransformation._deps_from_import(
                            small,
                            tree,
                            stem,
                            package_name,
                            lazy_map,
                        ),
                    )
        return deps

    @staticmethod
    def find_import_cycles(
        graph: Mapping[str, t.Infra.StrSet],
    ) -> Sequence[t.StrSequence]:
        """Detect all cycles in the import graph via DFS."""
        cycles: MutableSequence[t.StrSequence] = []
        visited: t.Infra.StrSet = set()
        path: MutableSequence[str] = []
        path_set: t.Infra.StrSet = set()

        def dfs(node: str) -> None:
            if node in path_set:
                idx = path.index(node)
                cycles.append([*path[idx:], node])
                return
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            path_set.add(node)
            for neighbor in graph.get(node, set()):
                dfs(neighbor)
            path.pop()
            path_set.remove(node)

        for start in graph:
            dfs(start)
        return cycles

    @staticmethod
    def collect_cycle_edges(
        cycles: Sequence[t.StrSequence],
    ) -> t.Infra.StrPairSet:
        """Extract directed edges from detected cycles."""
        cycle_edges: t.Infra.StrPairSet = set()
        for cycle in cycles:
            edges = [(cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)]
            cycle_edges.update(edges)
        return cycle_edges

    @staticmethod
    def resolve_target_aliases(
        lazy_map: t.StrMapping,
        target_mod: str,
    ) -> t.StrSequence:
        """Return canonical aliases that resolve to *target_mod* in the lazy map."""
        return [
            alias
            for alias, mod_stem in lazy_map.items()
            if mod_stem == target_mod
            and alias
            in FlextInfraUtilitiesCodegenConstantTransformation.CANONICAL_ALIASES
        ]

    @staticmethod
    def _split_cycle_imports(
        imp: cst.ImportFrom,
        target_set: frozenset[str],
    ) -> t.Infra.Pair[t.StrSequence, t.StrSequence]:
        """Split imported names into cycle aliases and keepers."""
        names = imp.names
        if isinstance(names, cst.ImportStar):
            return [], []
        imported = [
            alias.name.value for alias in names if isinstance(alias.name, cst.Name)
        ]
        cycle_aliases = [a for a in imported if a in target_set]
        keep_aliases = [a for a in imported if a not in target_set]
        return cycle_aliases, keep_aliases

    @staticmethod
    def rewrite_module_imports(
        tree: cst.Module,
        package_name: str,
        parent_pkg: str,
        target_aliases: t.StrSequence,
    ) -> t.Infra.Pair[
        MutableSequence[cst.BaseCompoundStatement | cst.SimpleStatementLine],
        MutableSequence[str],
    ]:
        """Rewrite imports in a single module, redirecting cycle aliases to parent.

        Returns the new body statements and a list of change descriptions.
        """
        cls = FlextInfraUtilitiesCodegenConstantTransformation
        new_body: MutableSequence[
            cst.BaseCompoundStatement | cst.SimpleStatementLine
        ] = []
        changes: MutableSequence[str] = []
        target_set = frozenset(target_aliases)

        for stmt in tree.body:
            if not (
                isinstance(stmt, cst.SimpleStatementLine)
                and len(stmt.body) == 1
                and isinstance(stmt.body[0], cst.ImportFrom)
                and not isinstance(stmt.body[0].names, cst.ImportStar)
            ):
                new_body.append(stmt)
                continue
            imp = stmt.body[0]
            if not isinstance(imp, cst.ImportFrom):
                new_body.append(stmt)
                continue
            mod = tree.code_for_node(imp.module) if imp.module else ""
            if mod != package_name:
                new_body.append(stmt)
                continue
            cycle_aliases, keep_aliases = cls._split_cycle_imports(imp, target_set)
            if not cycle_aliases:
                new_body.append(stmt)
                continue
            if keep_aliases:
                new_body.append(
                    cst.parse_statement(
                        f"from {package_name} import {', '.join(keep_aliases)}\n",
                    ),
                )
            new_body.append(
                cst.parse_statement(
                    f"from {parent_pkg} import {', '.join(cycle_aliases)}\n",
                ),
            )
            changes.append(
                f"from {package_name} import {', '.join(cycle_aliases)}"
                f" → from {parent_pkg} import {', '.join(cycle_aliases)}",
            )
        return new_body, changes

    @staticmethod
    def break_import_cycles(pkg_dir: Path) -> t.Infra.Pair[bool, t.StrSequence]:
        """Detect and break intra-package import cycles by redirecting to parent."""
        cls = FlextInfraUtilitiesCodegenConstantTransformation
        lazy_map = cls.parse_lazy_imports(pkg_dir / c.Infra.Files.INIT_PY)
        if not lazy_map:
            return False, []

        package_name = pkg_dir.name
        graph = cls.build_self_import_graph(pkg_dir, package_name, lazy_map)
        cycles = cls.find_import_cycles(graph)
        if not cycles:
            return False, []

        parent_pkg = FlextInfraUtilitiesCodegenConstantDetection.resolve_parent_package(
            pkg_dir,
        )
        if parent_pkg.startswith(f"{package_name}.") or parent_pkg == package_name:
            return False, []

        cycle_edges = cls.collect_cycle_edges(cycles)
        all_changes: MutableSequence[str] = []
        any_modified = False

        for source_mod, target_mod in cycle_edges:
            source_file = pkg_dir / f"{source_mod}.py"
            if not source_file.is_file():
                continue
            tree = FlextInfraUtilitiesParsing.parse_module_cst(source_file)
            if tree is None:
                continue
            target_aliases = cls.resolve_target_aliases(lazy_map, target_mod)
            if not target_aliases:
                continue
            new_body, changes = cls.rewrite_module_imports(
                tree,
                package_name,
                parent_pkg,
                target_aliases,
            )
            if changes:
                new_tree = tree.with_changes(body=new_body)
                source_file.write_text(new_tree.code, encoding=c.Infra.Encoding.DEFAULT)
                any_modified = True
                all_changes.extend(f"{source_mod}.py: {change}" for change in changes)

        return any_modified, all_changes


__all__ = ["FlextInfraUtilitiesCodegenConstantTransformation"]
