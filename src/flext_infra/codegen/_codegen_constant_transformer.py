from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c, m
from flext_infra.codegen._codegen_constant_visitor import (
    attribute_chain,
    canonical_reference_for,
)


class CanonicalValueReplacer(cst.CSTTransformer):
    def __init__(
        self,
        *,
        parent_class: str,
        definitions: list[m.Infra.ConstantDefinition],
    ) -> None:
        self._parent_class = parent_class
        self._lookup = {
            (item.name, item.value_repr): canonical_reference_for(
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
        canonical_ref = self._lookup.get((original_node.target.value, value_repr), "")
        if not canonical_ref:
            return updated_node
        self.replacements += 1
        self.changes.append(f"replaced {original_node.target.value} -> {canonical_ref}")
        return updated_node.with_changes(
            value=cst.parse_expression(f"{self._parent_class}.{canonical_ref}"),
        )


class UnusedConstantRemover(cst.CSTTransformer):
    def __init__(self, *, unused_names: set[str]) -> None:
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
    def __init__(self, *, project_import: str) -> None:
        self._project_import = project_import
        self._has_c_import = False
        self.changes: list[str] = []
        self.replacements = 0

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        if isinstance(node.names, cst.ImportStar):
            return
        for alias in tuple(node.names):
            imported_name = alias.name.value if isinstance(alias.name, cst.Name) else ""
            local_name = imported_name
            if alias.asname is not None and isinstance(alias.asname.name, cst.Name):
                local_name = alias.asname.name.value
            if local_name == "c":
                self._has_c_import = True

    @override
    def leave_Attribute(
        self,
        original_node: cst.Attribute,
        updated_node: cst.Attribute,
    ) -> cst.BaseExpression:
        del original_node
        chain = attribute_chain(updated_node)
        if len(chain) < 2:
            return updated_node
        if not re.fullmatch(c.Infra.Dedup.CONSTANTS_CLASS_PATTERN, chain[0]):
            return updated_node
        rewritten = ".".join(["c", *chain[1:]])
        self.replacements += 1
        self.changes.append(f"normalized {'.'.join(chain)} -> {rewritten}")
        return cst.parse_expression(rewritten)

    @override
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        del original_node
        if self.replacements == 0 or self._has_c_import:
            return updated_node
        body = list(updated_node.body)
        body.insert(
            _import_insert_index(body), cst.parse_statement(f"{self._project_import}\n")
        )
        self.changes.append("added c import")
        return updated_node.with_changes(body=body)


def replace_canonical_values(
    file_path: Path,
    parent_class: str,
    definitions: list[m.Infra.ConstantDefinition],
) -> tuple[bool, list[str]]:
    tree = cst.parse_module(file_path.read_text("utf-8"))
    transformer = CanonicalValueReplacer(
        parent_class=parent_class, definitions=definitions
    )
    new_tree = tree.visit(transformer)
    if transformer.replacements > 0:
        file_path.write_text(new_tree.code, encoding="utf-8")
    return transformer.replacements > 0, transformer.changes


def remove_unused_constants(
    file_path: Path,
    unused: list[m.Infra.UnusedConstant],
) -> tuple[bool, list[str]]:
    tree = cst.parse_module(file_path.read_text("utf-8"))
    transformer = UnusedConstantRemover(unused_names={item.name for item in unused})
    new_tree = tree.visit(transformer)
    if transformer.removals > 0:
        file_path.write_text(new_tree.code, encoding="utf-8")
    return transformer.removals > 0, transformer.changes


def normalize_constant_aliases(
    file_path: Path,
    project_import: str,
) -> tuple[bool, list[str]]:
    tree = cst.parse_module(file_path.read_text("utf-8"))
    transformer = DirectRefAliasNormalizer(project_import=project_import)
    new_tree = tree.visit(transformer)
    if transformer.replacements > 0:
        file_path.write_text(new_tree.code, encoding="utf-8")
    return transformer.replacements > 0, transformer.changes


def _import_insert_index(
    body: Sequence[cst.SimpleStatementLine | cst.BaseCompoundStatement],
) -> int:
    index = 0
    if body and isinstance(body[0], cst.SimpleStatementLine):
        if len(body[0].body) == 1 and isinstance(body[0].body[0], cst.Expr):
            if isinstance(body[0].body[0].value, cst.SimpleString):
                index = 1
    while index < len(body):
        stmt = body[index]
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            break
        import_stmt = stmt.body[0]
        if not isinstance(import_stmt, cst.ImportFrom) or import_stmt.module is None:
            break
        if not (
            isinstance(import_stmt.module, cst.Name)
            and import_stmt.module.value == "__future__"
        ):
            break
        index += 1
    return index


__all__ = [
    "CanonicalValueReplacer",
    "UnusedConstantRemover",
    "DirectRefAliasNormalizer",
    "replace_canonical_values",
    "remove_unused_constants",
    "normalize_constant_aliases",
]
