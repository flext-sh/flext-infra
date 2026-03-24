"""Unify inline typing unions and TypeAlias declarations to canonical forms."""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

import libcst as cst

from flext_infra import c, t, u

_PAIR_LENGTH = 2


class FlextInfraRefactorTypingUnifier(cst.CSTTransformer):
    """Unify inline type unions into canonical t.* alias references via CST rewrite."""

    def __init__(
        self,
        *,
        canonical_map: Mapping[frozenset[str], str],
        file_path: Path | None = None,
    ) -> None:
        """Initialize unifier context and accumulated import/type state."""
        self._scope_depth = 0
        self._typing_import_names: t.Infra.StrSet = set()
        self._typing_import_aliases: MutableSequence[cst.ImportAlias] = []
        self._all_name_usages: t.Infra.StrSet = set()
        self._has_t_import = False
        self._needs_t_import = False
        self._typealias_unconverted = 0
        self._is_definition_file = self._is_typing_definition_file(file_path)
        self._canonical_map = canonical_map
        self.changes: MutableSequence[str] = []

    @override
    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        module_name = u.Infra.cst_module_name(node.module)
        if module_name == "typing":
            names = node.names
            if isinstance(names, cst.ImportStar):
                return False
            for alias in tuple(names):
                if not isinstance(alias.name, cst.Name):
                    continue
                self._typing_import_names.add(self._bound_name(alias))
                self._typing_import_aliases.append(alias)
            return False
        if not isinstance(node.names, cst.ImportStar):
            for alias in tuple(node.names):
                if not isinstance(alias.name, cst.Name):
                    continue
                if self._bound_name(alias) == "t":
                    self._has_t_import = True
        return True

    @override
    def visit_Name(self, node: cst.Name) -> None:
        self._all_name_usages.add(node.value)

    @override
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        del node
        self._scope_depth += 1

    @override
    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        del original_node
        self._scope_depth -= 1
        return updated_node

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        del node
        self._scope_depth += 1

    @override
    def leave_FunctionDef(
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.FunctionDef:
        del original_node
        self._scope_depth -= 1
        return updated_node

    @override
    def leave_ImportFrom(
        self,
        original_node: cst.ImportFrom,
        updated_node: cst.ImportFrom,
    ) -> cst.BaseSmallStatement | cst.RemovalSentinel:
        """Pass through typing imports unchanged — filtering deferred to leave_Module.

        DFS ordering means leave_ImportFrom fires before visit_Name has
        collected usages from the rest of the file. The actual unused-import
        filtering runs in leave_Module where _all_name_usages is complete.
        """
        return updated_node

    @override
    def leave_AnnAssign(
        self,
        original_node: cst.AnnAssign,
        updated_node: cst.AnnAssign,
    ) -> cst.BaseSmallStatement:
        if not isinstance(original_node.target, cst.Name):
            return updated_node
        if original_node.value is None:
            return updated_node
        annotation_name = self._annotation_name(original_node.annotation.annotation)
        if annotation_name not in {"TypeAlias", "typing.TypeAlias"}:
            return updated_node
        if self._scope_depth > 0:
            self._typealias_unconverted += 1
            return updated_node
        alias_value = updated_node.value
        if alias_value is None:
            return updated_node
        alias_name = original_node.target.value
        self.changes.append(f"Converted legacy TypeAlias assignment: {alias_name}")
        return cst.TypeAlias(name=cst.Name(alias_name), value=alias_value)

    @override
    def leave_Annotation(
        self,
        original_node: cst.Annotation,
        updated_node: cst.Annotation,
    ) -> cst.Annotation:
        del original_node
        if self._is_definition_file:
            return updated_node
        union_leaf_names = self._extract_union_leaf_names(updated_node.annotation)
        if union_leaf_names is None:
            return updated_node
        if "None" in union_leaf_names:
            return updated_node
        canonical_target = self._canonical_map.get(frozenset(union_leaf_names))
        if canonical_target is None:
            return updated_node
        replacement = self._build_t_attribute(canonical_target)
        if replacement is None:
            return updated_node
        self._needs_t_import = True
        self.changes.append(
            f"Canonicalized inline union -> {canonical_target}",
        )
        return updated_node.with_changes(annotation=replacement)

    @override
    def leave_Module(
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        del original_node
        result = self._filter_typing_imports(updated_node)
        if self._needs_t_import and not self._has_t_import:
            result = self._inject_t_import(result)
        return result

    def _filter_typing_imports(self, module: cst.Module) -> cst.Module:
        new_body: MutableSequence[cst.BaseStatement] = []
        for stmt in module.body:
            replacement = self._maybe_filter_typing_import_stmt(stmt)
            if replacement is not None:
                new_body.append(replacement)
        return module.with_changes(body=new_body)

    def _maybe_filter_typing_import_stmt(
        self,
        stmt: cst.BaseStatement,
    ) -> cst.BaseStatement | None:
        if not isinstance(stmt, cst.SimpleStatementLine):
            return stmt
        if len(stmt.body) != 1:
            return stmt
        only = stmt.body[0]
        if not isinstance(only, cst.ImportFrom):
            return stmt
        module_name = u.Infra.cst_module_name(only.module)
        if module_name != "typing":
            return stmt
        if isinstance(only.names, cst.ImportStar):
            return stmt
        retained: MutableSequence[cst.ImportAlias] = []
        for alias in tuple(only.names):
            if not isinstance(alias.name, cst.Name):
                retained.append(alias)
                continue
            imported_name = alias.name.value
            bound_name = self._bound_name(alias)
            if imported_name == "TypeAlias":
                if self._typealias_unconverted > 0:
                    retained.append(alias)
                else:
                    self.changes.append("Removed typing import: TypeAlias")
                continue
            if bound_name in self._all_name_usages:
                retained.append(alias)
                continue
            self.changes.append(f"Removed unused typing import: {imported_name}")
        if not retained:
            self.changes.append("Removed empty typing import")
            return None
        updated_import = only.with_changes(names=tuple(retained))
        return stmt.with_changes(body=[updated_import])

    def _inject_t_import(self, module: cst.Module) -> cst.Module:
        import_stmt = cst.SimpleStatementLine(
            body=[
                cst.ImportFrom(
                    module=cst.Name("flext_core"),
                    names=[cst.ImportAlias(name=cst.Name("t"))],
                ),
            ],
        )
        body = list(module.body)
        insert_idx = u.Infra.index_after_docstring_and_future_imports(
            body,
        )
        self.changes.append("Added import: from flext_core import t")
        new_body = body[:insert_idx] + [import_stmt] + body[insert_idx:]
        return module.with_changes(body=new_body)

    @staticmethod
    def _bound_name(alias: cst.ImportAlias) -> str:
        if alias.asname is not None and isinstance(alias.asname.name, cst.Name):
            return alias.asname.name.value
        if isinstance(alias.name, cst.Name):
            return alias.name.value
        return alias.name.attr.value

    @staticmethod
    def _annotation_name(annotation: cst.BaseExpression) -> str:
        if isinstance(annotation, cst.Name):
            return annotation.value
        if isinstance(annotation, cst.Attribute):
            if isinstance(annotation.value, cst.Name):
                return f"{annotation.value.value}.{annotation.attr.value}"
            return annotation.attr.value
        return ""

    @staticmethod
    def _is_typing_definition_file(file_path: Path | None) -> bool:
        if file_path is None:
            return False
        if file_path.name in c.Infra.TYPING_DEFINITION_FILES:
            return True
        return any(part in c.Infra.TYPING_DEFINITION_FILES for part in file_path.parts)

    @staticmethod
    def _union_leaves(expr: cst.BaseExpression) -> Sequence[cst.BaseExpression] | None:
        if not isinstance(expr, cst.BinaryOperation):
            return None
        if not isinstance(expr.operator, cst.BitOr):
            return None
        left = FlextInfraRefactorTypingUnifier._union_leaves(expr.left)
        right = FlextInfraRefactorTypingUnifier._union_leaves(expr.right)
        left_items = left if left is not None else [expr.left]
        right_items = right if right is not None else [expr.right]
        return [*left_items, *right_items]

    @staticmethod
    def _leaf_name(expr: cst.BaseExpression) -> str | None:
        if isinstance(expr, cst.Name):
            return expr.value
        if isinstance(expr, cst.Attribute):
            return expr.attr.value
        return None

    def _extract_union_leaf_names(
        self,
        expr: cst.BaseExpression,
    ) -> frozenset[str] | None:
        leaves = self._union_leaves(expr)
        if leaves is None:
            return None
        normalized: t.Infra.StrSet = set()
        for leaf in leaves:
            leaf_name = self._leaf_name(leaf)
            if leaf_name is None:
                return None
            if leaf_name == "NoneType":
                normalized.add("None")
                continue
            normalized.add(leaf_name)
        return frozenset(normalized)

    @staticmethod
    def _build_t_attribute(target: str) -> cst.BaseExpression | None:
        parts = target.split(".")
        if len(parts) != _PAIR_LENGTH:
            return None
        base_name, contract_name = parts
        if base_name != "t":
            return None
        return cst.Attribute(value=cst.Name(base_name), attr=cst.Name(contract_name))


__all__ = ["FlextInfraRefactorTypingUnifier"]
