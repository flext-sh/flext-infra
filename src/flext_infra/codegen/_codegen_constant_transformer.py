from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Final, override

import libcst as cst

from flext_infra import (
    FlextInfraCodegenConstantDetection,
)

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraCodegenConstantTransformation:
    MIN_ATTRIBUTE_CHAIN: Final[int] = 2

    class CanonicalValueReplacer(cst.CSTTransformer):
        def __init__(
            self,
            *,
            parent_class: str,
            definitions: list[m.Infra.ConstantDefinition],
        ) -> None:
            super().__init__()
            self._parent_class = parent_class
            self._lookup = {
                (
                    item.name,
                    item.value_repr,
                ): FlextInfraCodegenConstantDetection.canonical_reference_for(
                    item.name,
                    item.value_repr,
                )
                for item in definitions
            }
            self.changes: list[str] = []
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
        def __init__(self, *, unused_names: set[str]) -> None:
            super().__init__()
            self._unused_names = unused_names
            self._class_stack: list[str] = []
            self.changes: list[str] = []
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
            self._replaced_classes: set[str] = set()
            self.changes: list[str] = []
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
            chain = FlextInfraCodegenConstantDetection.attribute_chain(updated_node)
            if len(chain) < FlextInfraCodegenConstantTransformation.MIN_ATTRIBUTE_CHAIN:
                return updated_node
            if chain[0] != self._target_class:
                return updated_node
            self._replaced_classes.add(chain[0])
            rewritten = ".".join(["c", *chain[1:]])
            self.replacements += 1
            self.changes.append(f"{'.'.join(chain)} -> {rewritten}")
            return cst.parse_expression(rewritten)

        @override
        def leave_Module(
            self,
            original_node: cst.Module,
            updated_node: cst.Module,
        ) -> cst.Module:
            del original_node
            t = FlextInfraCodegenConstantTransformation
            if self.replacements == 0:
                return updated_node
            new_body: list[cst.BaseCompoundStatement | cst.SimpleStatementLine] = []
            c_import_present = self._has_c_import
            for stmt in updated_node.body:
                if (
                    isinstance(stmt, cst.SimpleStatementLine)
                    and len(stmt.body) == 1
                    and isinstance(stmt.body[0], cst.ImportFrom)
                    and not isinstance(stmt.body[0].names, cst.ImportStar)
                ):
                    import_node = stmt.body[0]
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
                        self.changes.append(
                            f"removed {removed_count} unused import(s)",
                        )
                    if not remaining:
                        continue
                    if removed_count > 0:
                        cleaned = [
                            a.with_changes(comma=cst.MaybeSentinel.DEFAULT)
                            if i == len(remaining) - 1
                            else a
                            for i, a in enumerate(remaining)
                        ]
                        stmt = stmt.with_changes(
                            body=[import_node.with_changes(names=cleaned)],
                        )
                new_body.append(stmt)
            if not c_import_present:
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
                try:
                    tree = cst.parse_module(constants_file.read_text("utf-8"))
                except (cst.ParserSyntaxError, UnicodeDecodeError):
                    tree = None
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
        definitions: list[m.Infra.ConstantDefinition],
    ) -> tuple[bool, list[str]]:
        t = FlextInfraCodegenConstantTransformation
        tree = cst.parse_module(file_path.read_text("utf-8"))
        transformer = t.CanonicalValueReplacer(
            parent_class=parent_class,
            definitions=definitions,
        )
        new_tree = tree.visit(transformer)
        if transformer.replacements > 0:
            file_path.write_text(new_tree.code, encoding="utf-8")
        return transformer.replacements > 0, transformer.changes

    @staticmethod
    def remove_unused_constants(
        file_path: Path,
        unused: list[m.Infra.UnusedConstant],
    ) -> tuple[bool, list[str]]:
        t = FlextInfraCodegenConstantTransformation
        tree = cst.parse_module(file_path.read_text("utf-8"))
        transformer = t.UnusedConstantRemover(
            unused_names={item.name for item in unused},
        )
        new_tree = tree.visit(transformer)
        if transformer.removals > 0:
            file_path.write_text(new_tree.code, encoding="utf-8")
        return transformer.removals > 0, transformer.changes

    @staticmethod
    def normalize_constant_aliases(
        file_path: Path,
        project_import: str,
        pkg_dir: Path | None = None,
    ) -> tuple[bool, list[str]]:
        t = FlextInfraCodegenConstantTransformation
        parts = project_import.replace("from ", "").split(" import ")
        package_name = parts[0].strip() if parts else ""
        resolved_pkg_dir = pkg_dir
        if resolved_pkg_dir is None and package_name:
            for parent in file_path.parents:
                if parent.name == package_name:
                    resolved_pkg_dir = parent
                    break
        target_class = t.derive_constants_class(package_name, resolved_pkg_dir)
        tree = cst.parse_module(file_path.read_text("utf-8"))
        transformer = t.DirectRefAliasNormalizer(
            project_import=project_import,
            target_class=target_class,
        )
        new_tree = tree.visit(transformer)
        if transformer.replacements > 0:
            file_path.write_text(new_tree.code, encoding="utf-8")
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
    def break_import_cycles(pkg_dir: Path) -> tuple[bool, list[str]]:
        def parse_lazy_imports(init_file: Path) -> dict[str, str]:
            if not init_file.is_file():
                return {}
            source = init_file.read_text("utf-8")
            mapping: dict[str, str] = {}
            for match in re.finditer(
                r'"(\w+)":\s*\("([\w.]+)",\s*"(\w+)"\)',
                source,
            ):
                alias, module_path, _export = match.groups()
                mapping[alias] = module_path.rsplit(".", 1)[-1]
            return mapping

        def build_self_import_graph(
            package_name: str,
            lazy_map: dict[str, str],
        ) -> dict[str, set[str]]:
            graph: dict[str, set[str]] = {}
            for py_file in pkg_dir.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                stem = py_file.stem
                deps: set[str] = set()
                try:
                    source = py_file.read_text("utf-8")
                    tree = cst.parse_module(source)
                except (cst.ParserSyntaxError, UnicodeDecodeError):
                    continue
                for stmt in tree.body:
                    if not isinstance(stmt, cst.SimpleStatementLine):
                        continue
                    for small in stmt.body:
                        if not isinstance(small, cst.ImportFrom):
                            continue
                        if isinstance(small.names, cst.ImportStar):
                            continue
                        mod = tree.code_for_node(small.module) if small.module else ""
                        if mod != package_name:
                            continue
                        for alias in small.names:
                            name = (
                                alias.name.value
                                if isinstance(alias.name, cst.Name)
                                else ""
                            )
                            target = lazy_map.get(name)
                            if target and target != stem:
                                deps.add(target)
                if deps:
                    graph[stem] = deps
            return graph

        def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
            cycles: list[list[str]] = []
            visited: set[str] = set()
            path: list[str] = []
            path_set: set[str] = set()

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

        lazy_map = parse_lazy_imports(pkg_dir / "__init__.py")
        if not lazy_map:
            return False, []
        graph = build_self_import_graph(pkg_dir.name, lazy_map)
        cycles = find_cycles(graph)
        if not cycles:
            return False, []

        package_name = pkg_dir.name
        parent_pkg = FlextInfraCodegenConstantDetection.resolve_parent_package(pkg_dir)
        if parent_pkg.startswith(f"{package_name}.") or parent_pkg == package_name:
            return False, []
        cycle_edges: set[tuple[str, str]] = set()
        for cycle in cycles:
            edges = [(cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)]
            cycle_edges.update(edges)

        all_changes: list[str] = []
        any_modified = False

        for source_mod, target_mod in cycle_edges:
            source_file = pkg_dir / f"{source_mod}.py"
            if not source_file.is_file():
                continue
            source_text = source_file.read_text("utf-8")
            tree = cst.parse_module(source_text)
            new_body: list[cst.BaseCompoundStatement | cst.SimpleStatementLine] = []
            changed = False

            canonical_aliases = frozenset([
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
            target_aliases = [
                alias
                for alias, mod_stem in lazy_map.items()
                if mod_stem == target_mod and alias in canonical_aliases
            ]
            if not target_aliases:
                continue

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
                mod = tree.code_for_node(imp.module) if imp.module else ""
                if mod != package_name:
                    new_body.append(stmt)
                    continue
                names = imp.names
                if isinstance(names, cst.ImportStar):
                    new_body.append(stmt)
                    continue
                imported = [
                    alias.name.value
                    for alias in names
                    if isinstance(alias.name, cst.Name)
                ]
                cycle_aliases = [a for a in imported if a in target_aliases]
                keep_aliases = [a for a in imported if a not in target_aliases]
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
                changed = True
                all_changes.append(
                    f"{source_mod}.py: from {package_name} import {', '.join(cycle_aliases)}"
                    f" → from {parent_pkg} import {', '.join(cycle_aliases)}",
                )

            if changed:
                new_tree = tree.with_changes(body=new_body)
                source_file.write_text(new_tree.code, encoding="utf-8")
                any_modified = True

        return any_modified, all_changes


__all__ = ["FlextInfraCodegenConstantTransformation"]
