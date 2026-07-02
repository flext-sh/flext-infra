"""Census per-module rule dispatch — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, p, t


class FlextInfraRefactorCensusRulesDispatchMixin:
    """Run every selected alias/MRO rule for one module and collect outcomes.

    Parent of FlextInfraRefactorCensusCollectMixin (its ``_scan_module`` calls
    ``_module_rules``); borrows the symbol-index, rule-selection filter, and
    the four per-rule detectors from sibling mixins via MRO.
    """

    if TYPE_CHECKING:

        @classmethod
        def _lightweight_symbol_index(
            cls,
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
        ) -> dict[str, tuple[str, int]]: ...
        @staticmethod
        def _include_rule(
            rule: str,
            *,
            rule_names: t.StrSequence | None,
            selected_rules: frozenset[str] | None = None,
        ) -> bool: ...
        def _rule_runtime_alias(
            self,
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            project_name: str,
            objects: tuple[m.Infra.Census.Object, ...] | None,
            applied: frozenset[str],
            selected_kinds: frozenset[str],
            symbol_index: dict[str, tuple[str, int]],
            convention: m.Infra.RopeModuleConvention,
        ) -> tuple[list[m.Infra.Census.Violation], list[m.Infra.Census.Fix]]: ...
        def _rule_manual_typing_alias(
            self,
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            project_name: str,
            objects: tuple[m.Infra.Census.Object, ...] | None,
            applied: frozenset[str],
            selected_kinds: frozenset[str],
            convention: m.Infra.RopeModuleConvention,
        ) -> tuple[list[m.Infra.Census.Violation], list[m.Infra.Census.Fix]]: ...
        def _rule_compatibility_alias(
            self,
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            project_name: str,
            objects: tuple[m.Infra.Census.Object, ...] | None,
            applied: frozenset[str],
            selected_kinds: frozenset[str],
            symbol_index: dict[str, tuple[str, int]],
            convention: m.Infra.RopeModuleConvention,
        ) -> tuple[list[m.Infra.Census.Violation], list[m.Infra.Census.Fix]]: ...
        def _rule_mro_completeness(
            self,
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            project_name: str,
            objects: tuple[m.Infra.Census.Object, ...] | None,
            applied: frozenset[str],
            selected_kinds: frozenset[str],
            symbol_index: dict[str, tuple[str, int]],
            convention: m.Infra.RopeModuleConvention,
        ) -> tuple[list[m.Infra.Census.Violation], list[m.Infra.Census.Fix]]: ...

    def _module_rules(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        objects: tuple[m.Infra.Census.Object, ...] | None,
        project_name: str,
        applied: frozenset[str],
        kind_names: t.StrSequence | None,
        rule_names: t.StrSequence | None,
        selected_kinds: frozenset[str] | None = None,
        selected_rules: frozenset[str] | None = None,
        convention: m.Infra.RopeModuleConvention | None = None,
    ) -> tuple[tuple[m.Infra.Census.Violation, ...], tuple[m.Infra.Census.Fix, ...]]:
        """Run every selected alias/MRO rule for one module and collect outcomes."""
        resolved_convention = convention or rope.convention(file_path)
        resolved_kinds = (
            selected_kinds
            if selected_kinds is not None
            else (frozenset(kind_names) if kind_names else frozenset())
        )
        symbol_index = self._lightweight_symbol_index(rope, file_path)
        violations: list[m.Infra.Census.Violation] = []
        fixes: list[m.Infra.Census.Fix] = []

        def selected(rule_name: str) -> bool:
            return self._include_rule(
                rule_name, rule_names=rule_names, selected_rules=selected_rules
            )

        if selected("runtime_alias"):
            v, f = self._rule_runtime_alias(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("manual_typing_alias"):
            v, f = self._rule_manual_typing_alias(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("class_placement"):
            v, f = self._rule_class_placement(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("compatibility_alias"):
            v, f = self._rule_compatibility_alias(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("mro_completeness"):
            v, f = self._rule_mro_completeness(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        return (tuple(violations), tuple(fixes))


__all__: list[str] = ["FlextInfraRefactorCensusRulesDispatchMixin"]
