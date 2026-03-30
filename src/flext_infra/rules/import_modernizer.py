"""Rule that modernizes imports into runtime alias references."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import override

import libcst as cst
from libcst.metadata import MetadataWrapper
from pydantic import TypeAdapter, ValidationError

from flext_infra import (
    CONTAINER_DICT_SEQ_ADAPTER,
    FlextInfraRefactorImportModernizer,
    FlextInfraRefactorLazyImportFixer,
    FlextInfraRefactorRule,
    c,
    m,
    t,
    u,
)

_RULE_CONFIG_SEQ_ADAPTER: TypeAdapter[Sequence[m.Infra.ImportModernizerRuleConfig]] = (
    TypeAdapter(Sequence[m.Infra.ImportModernizerRuleConfig])
)


def _all_param_names(params: cst.Parameters) -> Sequence[str]:
    """Extract all parameter names from a function's Parameters node."""
    names: MutableSequence[str] = [
        param.name.value
        for param in [*params.params, *params.posonly_params, *params.kwonly_params]
    ]
    if isinstance(params.star_arg, cst.Param):
        names.append(params.star_arg.name.value)
    if isinstance(params.star_kwarg, cst.Param):
        names.append(params.star_kwarg.name.value)
    return names


class _FunctionShadowCollector(cst.CSTVisitor):
    """Collect runtime-alias names shadowed inside function bodies."""

    def __init__(
        self,
        runtime_aliases: t.Infra.StrSet,
        shadowed_aliases: t.Infra.StrSet,
    ) -> None:
        self._function_depth = 0
        self._runtime_aliases = runtime_aliases
        self._shadowed = shadowed_aliases

    def _collect_name(self, node: cst.BaseExpression) -> None:
        if isinstance(node, cst.Name) and node.value in self._runtime_aliases:
            self._shadowed.add(node.value)

    @override
    def leave_FunctionDef(self, original_node: cst.FunctionDef) -> None:
        del original_node
        self._function_depth -= 1

    @override
    def visit_AnnAssign(self, node: cst.AnnAssign) -> None:
        if self._function_depth > 0:
            self._collect_name(node.target)

    @override
    def visit_Assign(self, node: cst.Assign) -> None:
        if self._function_depth == 0:
            return
        for assign_target in node.targets:
            self._collect_name(assign_target.target)

    @override
    def visit_For(self, node: cst.For) -> None:
        if self._function_depth > 0:
            self._collect_name(node.target)

    @override
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._function_depth += 1
        for param_name in _all_param_names(node.params):
            if param_name in self._runtime_aliases:
                self._shadowed.add(param_name)


class FlextInfraRefactorImportModernizerRule(FlextInfraRefactorRule):
    """Modernize forbidden imports and map symbols to runtime aliases."""

    @override
    def apply(
        self,
        tree: cst.Module,
        _file_path: Path | None = None,
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        """Apply import modernizer or lazy-import hoisting based on fix action."""
        fix_action = (
            str(self.config.get(c.Infra.ReportKeys.FIX_ACTION, "")).strip().lower()
        )
        if "lazy-import" in self.rule_id or fix_action == "hoist_to_module_top":
            return self._fix_lazy_imports(tree)
        runtime_aliases = set(c.Infra.RUNTIME_ALIAS_NAMES)
        blocked_aliases = self._collect_blocked_aliases(tree, runtime_aliases)
        blocked_aliases.update(
            self._collect_function_shadowed_aliases(tree, runtime_aliases),
        )
        forbidden = self.config.get("forbidden_imports")
        if forbidden is None:
            forbidden = [self.config]
        if not forbidden:
            return (tree, [])
        imports_to_remove: MutableSequence[str] = []
        symbols_to_replace: MutableMapping[str, str] = {}
        for rule_config in self._parse_forbidden_rules(forbidden):
            imports_to_remove.append(rule_config.module)
            symbols_to_replace.update(rule_config.symbol_mapping)
        transformer = FlextInfraRefactorImportModernizer(
            imports_to_remove=imports_to_remove,
            symbols_to_replace=symbols_to_replace,
            runtime_aliases=runtime_aliases,
            blocked_aliases=blocked_aliases,
        )
        wrapper = MetadataWrapper(tree)
        return (wrapper.visit(transformer), transformer.changes)

    @staticmethod
    def _parse_forbidden_rules(
        value: t.Infra.InfraValue,
    ) -> Sequence[m.Infra.ImportModernizerRuleConfig]:
        try:
            raw_items: Sequence[t.Infra.ContainerDict] = (
                CONTAINER_DICT_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError:
            return []
        normalized: Sequence[t.Infra.ContainerDict] = [
            {
                "module": item_mapping.get("module", ""),
                "symbol_mapping": item_mapping.get("symbol_mapping", {}),
            }
            for item_mapping in raw_items
        ]
        try:
            return _RULE_CONFIG_SEQ_ADAPTER.validate_python(normalized)
        except ValidationError:
            return []

    def _bound_name_from_import_alias(self, alias: cst.ImportAlias) -> str:
        if alias.asname is not None and isinstance(alias.asname.name, cst.Name):
            return alias.asname.name.value
        if isinstance(alias.name, cst.Name):
            return alias.name.value
        return alias.name.attr.value

    def _blocked_from_compound_stmt(
        self,
        stmt: cst.BaseStatement,
        runtime_aliases: t.Infra.StrSet,
        blocked: t.Infra.StrSet,
    ) -> None:
        """Collect blocked aliases from function/class definitions."""
        if isinstance(stmt, cst.FunctionDef) and stmt.name.value in runtime_aliases:
            blocked.add(stmt.name.value)
        if isinstance(stmt, cst.ClassDef) and stmt.name.value in runtime_aliases:
            blocked.add(stmt.name.value)

    def _blocked_from_import(
        self,
        small_stmt: cst.ImportFrom | cst.Import,
        runtime_aliases: t.Infra.StrSet,
        blocked: t.Infra.StrSet,
    ) -> None:
        """Collect blocked aliases from import statements."""
        if isinstance(small_stmt, cst.ImportFrom):
            module_name = u.Infra.cst_module_name(small_stmt.module)
            if module_name == c.Infra.Packages.CORE_UNDERSCORE:
                return
            if isinstance(small_stmt.names, cst.ImportStar):
                return
            names = small_stmt.names
        else:
            names = small_stmt.names
        for alias in tuple(names):
            bound_name = self._bound_name_from_import_alias(alias)
            if bound_name in runtime_aliases:
                blocked.add(bound_name)

    @staticmethod
    def _blocked_from_assignment(
        small_stmt: cst.Assign | cst.AnnAssign,
        runtime_aliases: t.Infra.StrSet,
        blocked: t.Infra.StrSet,
    ) -> None:
        """Collect blocked aliases from assignment statements."""
        if isinstance(small_stmt, cst.Assign):
            for assign_target in small_stmt.targets:
                target = assign_target.target
                if isinstance(target, cst.Name) and target.value in runtime_aliases:
                    blocked.add(target.value)
        elif isinstance(small_stmt, cst.AnnAssign):
            target = small_stmt.target
            if isinstance(target, cst.Name) and target.value in runtime_aliases:
                blocked.add(target.value)

    def _collect_blocked_aliases(
        self,
        tree: cst.Module,
        runtime_aliases: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        blocked_aliases: t.Infra.StrSet = set()
        for stmt in tree.body:
            if isinstance(stmt, cst.ImportFrom):
                continue
            if not isinstance(stmt, cst.SimpleStatementLine):
                self._blocked_from_compound_stmt(stmt, runtime_aliases, blocked_aliases)
                continue
            for small_stmt in stmt.body:
                if isinstance(small_stmt, (cst.ImportFrom, cst.Import)):
                    self._blocked_from_import(
                        small_stmt, runtime_aliases, blocked_aliases
                    )
                elif isinstance(small_stmt, (cst.Assign, cst.AnnAssign)):
                    self._blocked_from_assignment(
                        small_stmt, runtime_aliases, blocked_aliases
                    )
        return blocked_aliases

    def _collect_function_shadowed_aliases(
        self,
        tree: cst.Module,
        runtime_aliases: t.Infra.StrSet,
    ) -> t.Infra.StrSet:
        shadowed_aliases: t.Infra.StrSet = set()
        tree.visit(
            _FunctionShadowCollector(runtime_aliases, shadowed_aliases),
        )
        return shadowed_aliases

    def _fix_lazy_imports(
        self, tree: cst.Module
    ) -> t.Infra.Pair[cst.Module, t.StrSequence]:
        return self._apply_transformer(FlextInfraRefactorLazyImportFixer(), tree)


__all__ = ["FlextInfraRefactorImportModernizerRule"]
