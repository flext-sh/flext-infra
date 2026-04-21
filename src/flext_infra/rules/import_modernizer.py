"""Rule that modernizes imports into runtime alias references -- rope-based."""

from __future__ import annotations

from collections.abc import (
    MutableSequence,
)
from pathlib import Path
from typing import override

from flext_infra import (
    FlextInfraRefactorImportModernizer,
    FlextInfraRefactorLazyImportFixer,
    FlextInfraRefactorRule,
    c,
    t,
    u,
)


class FlextInfraRefactorImportModernizerRule(FlextInfraRefactorRule):
    """Modernize forbidden imports and map symbols to runtime aliases."""

    RULE_MATCHERS = (
        (c.Infra.IMPORT_FIX_ACTIONS, frozenset(), frozenset(), frozenset()),
    )

    @override
    def apply(
        self,
        source: str,
        _file_path: Path | None = None,
    ) -> t.Infra.TransformResult:
        """Apply import modernizer or lazy-import hoisting based on fix action."""
        fix_action = u.Cli.json_get_str_key(
            self.settings,
            c.Infra.RK_FIX_ACTION,
            case="lower",
        )
        if "lazy-import" in self.rule_id or fix_action == "hoist_to_module_top":
            fixer = FlextInfraRefactorLazyImportFixer()
            return self._apply_text_transformer(fixer, source)
        runtime_aliases = set(c.Infra.RUNTIME_ALIAS_NAMES)
        blocked = set(u.Infra.collect_blocked_aliases(source, runtime_aliases))
        blocked.update(u.Infra.collect_shadowed_aliases(source, runtime_aliases))
        forbidden = self.settings.get(c.Infra.RK_FORBIDDEN_IMPORTS)
        if forbidden is None:
            forbidden = [self.settings]
        if not forbidden:
            no_changes: list[str] = []
            return (source, no_changes)
        imports_to_remove: MutableSequence[str] = []
        seen_modules: t.Infra.StrSet = set()
        symbols_to_replace: t.MutableStrMapping = {}
        for rule_config in u.Infra.parse_forbidden_rules(forbidden):
            candidates = [rule_config.module]
            if "." in rule_config.module:
                candidates.append(rule_config.module.split(".", 1)[0])
            for mod in candidates:
                if mod in seen_modules:
                    continue
                seen_modules.add(mod)
                imports_to_remove.append(mod)
            symbols_to_replace.update(rule_config.symbol_mapping)
        modernizer = FlextInfraRefactorImportModernizer(
            imports_to_remove=imports_to_remove,
            symbols_to_replace=symbols_to_replace,
            runtime_aliases=runtime_aliases,
            blocked_aliases=blocked,
        )
        new_source, changes = modernizer.apply_to_source(source)
        return (new_source, changes)


__all__: list[str] = ["FlextInfraRefactorImportModernizerRule"]
