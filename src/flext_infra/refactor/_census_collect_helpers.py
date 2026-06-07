"""Census collection-gate + module-selection helpers — extracted concern."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from flext_infra import c, m, p, t


class FlextInfraRefactorCensusCollectHelpersMixin:
    """Decide what to collect + select modules for the requested rule set.

    Composed into FlextInfraRefactorCensus via inheritance; owns the
    lightweight-rule set and the static/cls collection-gate helpers.
    """

    _LIGHTWEIGHT_MODULE_RULES: ClassVar[frozenset[str]] = frozenset({
        "runtime_alias",
        "manual_typing_alias",
        "compatibility_alias",
        "mro_completeness",
    })

    @staticmethod
    def _should_collect_object_references(
        rule_names: t.StrSequence | None,
    ) -> bool:
        """Should collect object references."""
        if rule_names is None:
            return True
        return bool({"unused", "test_only"} & set(rule_names))

    @classmethod
    def _should_collect_object_inventory(
        cls,
        rule_names: t.StrSequence | None,
        *,
        selected_rules: frozenset[str] | None = None,
    ) -> bool:
        """Should collect full object inventory."""
        if selected_rules is None:
            selected_rules = frozenset(rule_names) if rule_names else None
        if not selected_rules:
            return True
        return not selected_rules <= cls._LIGHTWEIGHT_MODULE_RULES

    @staticmethod
    def _project_name_for_module(
        module: m.Infra.RopeModuleIndexEntry,
        convention: m.Infra.RopeModuleConvention,
    ) -> str:
        """Project name for a module entry."""
        layout = convention.project_layout
        if layout is not None:
            project_name = layout.project_name
            if not isinstance(project_name, str):
                msg = f"invalid layout project name for {module.file_path}"
                raise RuntimeError(msg)
            return project_name
        if module.project_root is not None:
            project_name = module.project_root.name
            if not isinstance(project_name, str):
                msg = f"invalid project root name for {module.file_path}"
                raise RuntimeError(msg)
            return project_name
        return ""

    @staticmethod
    def _mro_facade_module_names(
        selected_families: frozenset[str],
    ) -> frozenset[str]:
        """Mro facade module names."""
        families = selected_families or c.Infra.MRO_FAMILIES
        return frozenset(
            Path(module_path).name
            for family, module_path in c.Infra.MRO_FAMILY_FACADE_MODULES.items()
            if family in families
        )

    def _modules_for_rules(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        *,
        project_names: t.StrSequence | None,
        selected_families: frozenset[str],
        rule_names: t.StrSequence | None,
    ) -> tuple[m.Infra.RopeModuleIndexEntry, ...]:
        """Modules for rules."""
        modules = tuple(rope.modules(project_names=project_names))
        if rule_names is None or set(rule_names) != {"mro_completeness"}:
            return modules
        facade_module_names = self._mro_facade_module_names(selected_families)
        return tuple(
            module
            for module in modules
            if module.module_name
            and module.module_name.count(".") == 1
            and module.file_path.name in facade_module_names
        )


__all__: list[str] = ["FlextInfraRefactorCensusCollectHelpersMixin"]
