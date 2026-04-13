"""Rope-based refactor engine for flext_infra.refactor.

Orchestrates declarative rules, safety stash, and violation analysis.
File collection via ``u.Infra`` utilities, rule subclasses in ``engine_rules``.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_infra import (
    FlextInfraClassNestingRefactorRule,
    FlextInfraRefactorClassReconstructorRule,
    FlextInfraRefactorEnsureFutureAnnotationsRule,
    FlextInfraRefactorImportModernizerRule,
    FlextInfraRefactorLegacyRemovalTextRule,
    FlextInfraRefactorMROClassMigrationTextRule,
    FlextInfraRefactorMRORedundancyChecker,
    FlextInfraRefactorPatternCorrectionsTextRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorRuleDefinitionValidator,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorSignaturePropagationRule,
    FlextInfraRefactorSymbolPropagationRule,
    FlextInfraRefactorTier0ImportFixRule,
    FlextInfraRefactorTypingAnnotationFixRule,
    FlextInfraRefactorTypingUnificationRule,
    FlextInfraUtilitiesRefactorRuleLoader,
    c,
    p,
    r,
    t,
    u,
)

from .engine_helpers import FlextInfraRefactorEngineHelpersMixin

type _RuleEntry = tuple[frozenset[str], type[FlextInfraRefactorRule]]


class FlextInfraRefactorEngine(
    FlextInfraRefactorEngineHelpersMixin,
):
    """Rope-based refactor engine orchestrating declarative rules."""

    _RULE_ACTION_REGISTRY: ClassVar[Sequence[_RuleEntry]] = [
        (
            c.Infra.FUTURE_FIX_ACTIONS | c.Infra.FUTURE_CHECKS,
            FlextInfraRefactorEnsureFutureAnnotationsRule,
        ),
        (c.Infra.LEGACY_FIX_ACTIONS, FlextInfraRefactorLegacyRemovalTextRule),
        (c.Infra.IMPORT_FIX_ACTIONS, FlextInfraRefactorImportModernizerRule),
        (c.Infra.CLASS_FIX_ACTIONS, FlextInfraRefactorClassReconstructorRule),
        (c.Infra.PATTERN_FIX_ACTIONS, FlextInfraRefactorPatternCorrectionsTextRule),
        (c.Infra.TYPE_ALIAS_FIX_ACTIONS, FlextInfraRefactorTypingUnificationRule),
        (c.Infra.TYPING_FIX_ACTIONS, FlextInfraRefactorTypingAnnotationFixRule),
        (c.Infra.TIER0_FIX_ACTIONS, FlextInfraRefactorTier0ImportFixRule),
        (
            frozenset({"migrate_to_class_mro"}),
            FlextInfraRefactorMROClassMigrationTextRule,
        ),
        (
            frozenset({"propagate_signature_migrations"}),
            FlextInfraRefactorSignaturePropagationRule,
        ),
        (c.Infra.PROPAGATION_FIX_ACTIONS, FlextInfraRefactorSymbolPropagationRule),
        (c.Infra.MRO_FIX_ACTIONS, FlextInfraRefactorMRORedundancyChecker),
    ]
    _RULE_ID_FALLBACKS: ClassVar[Sequence[_RuleEntry]] = [
        (
            frozenset({"ensure-future", "future-annotations"}),
            FlextInfraRefactorEnsureFutureAnnotationsRule,
        ),
        (
            frozenset({"legacy", "alias", "deprecated", "wrapper", "bypass"}),
            FlextInfraRefactorLegacyRemovalTextRule,
        ),
        (frozenset({"import", "modernize"}), FlextInfraRefactorImportModernizerRule),
        (
            frozenset({"class", "reorder", "method"}),
            FlextInfraRefactorClassReconstructorRule,
        ),
        (
            frozenset({"redundant-cast", "dict-to-mapping", "container-invariance"}),
            FlextInfraRefactorPatternCorrectionsTextRule,
        ),
        (
            frozenset({"migrate-to-class-mro"}),
            FlextInfraRefactorMROClassMigrationTextRule,
        ),
        (frozenset({"mro"}), FlextInfraRefactorMRORedundancyChecker),
        (
            frozenset({"propagate", "symbol-rename", "rename"}),
            FlextInfraRefactorSymbolPropagationRule,
        ),
    ]

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize engine state and settings file path."""
        self.config_path = config_path or Path(__file__).parent / "settings.yml"
        config_map: Mapping[str, t.Infra.InfraValue] = {}
        self.settings: t.Infra.InfraValue = config_map
        self.rules: MutableSequence[FlextInfraRefactorRule] = []
        self.file_rules: MutableSequence[FlextInfraClassNestingRefactorRule] = []
        self.rule_filters: MutableSequence[str] = []
        self.rule_loader = FlextInfraUtilitiesRefactorRuleLoader(self.config_path)
        self.rule_validator = FlextInfraRefactorRuleDefinitionValidator()
        self.safety_manager = FlextInfraRefactorSafetyManager()

    # ── CLI ───────────────────────────────────────────────────────

    @staticmethod
    def main() -> int:
        """Run the refactor CLI entrypoint."""
        parser = argparse.ArgumentParser(
            description="Flext Refactor Engine",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        mode = parser.add_mutually_exclusive_group(required=True)
        _ = mode.add_argument("--project", "-p", type=Path)
        _ = mode.add_argument("--workspace", "-w", type=Path)
        _ = mode.add_argument("--file", "-f", type=Path)
        _ = mode.add_argument("--files", nargs="+", type=Path)
        _ = mode.add_argument("--list-rules", "-l", action="store_true")
        _ = parser.add_argument("--rules", "-r", type=str)
        _ = parser.add_argument("--pattern", default=c.Infra.EXT_PYTHON_GLOB)
        _ = parser.add_argument("--dry-run", "-n", action="store_true")
        _ = parser.add_argument("--show-diff", "-d", action="store_true")
        _ = parser.add_argument("--impact-map-output", type=Path)
        _ = parser.add_argument("--analyze-violations", action="store_true")
        _ = parser.add_argument("--analysis-output", type=Path)
        _ = parser.add_argument("--config", "-c", type=Path)
        args = parser.parse_args()
        engine = FlextInfraRefactorEngine(config_path=args.settings)
        cfg = engine.load_config()
        if not cfg.success:
            u.Infra.refactor_error(f"Config error: {cfg.error}")
            return 1
        if args.rules:
            engine.set_rule_filters([
                s.strip() for s in args.rules.split(",") if s.strip()
            ])
        rules_r = engine.load_rules()
        if not rules_r.success:
            u.Infra.refactor_error(f"Rules error: {rules_r.error}")
            return 1
        if args.list_rules:
            u.Infra.print_rules_table(engine.list_rules())
            return 0
        if args.analyze_violations:
            return engine._run_analyze_violations(args)
        return engine._run_refactor(args)

    # ── Config & rules ────────────────────────────────────────────

    def load_config(self) -> p.Result[Mapping[str, t.Infra.InfraValue]]:
        """Load YAML configuration for this engine instance."""
        result = self.rule_loader.load_config()
        if result.success:
            self.settings = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                dict(result.value)
            )
            u.Infra.refactor_info(f"Loaded settings from {self.config_path}")
        return result

    def load_rules(self) -> p.Result[Sequence[FlextInfraRefactorRule]]:
        """Load and instantiate enabled rules from rules directory."""
        rr = self.rule_loader.load_rules(
            self.rule_filters,
            self.rule_validator,
            self._build_rule,
            self._build_file_rules,
            self._skip_rule_definition,
        )
        if rr.failure:
            return r[Sequence[FlextInfraRefactorRule]].fail(rr.error or "")
        loaded_rules, loaded_file_rules = rr.value
        self.rules, self.file_rules = list(loaded_rules), list(loaded_file_rules)
        u.Infra.refactor_info(f"Loaded {len(self.rules)} rules")
        if self.file_rules:
            u.Infra.refactor_info(f"Loaded {len(self.file_rules)} file rules")
        if self.rule_filters:
            u.Infra.refactor_info(f"Active filters: {', '.join(self.rule_filters)}")
        return r[Sequence[FlextInfraRefactorRule]].ok(loaded_rules)

    def set_rule_filters(self, filters: t.StrSequence) -> None:
        """Set active rule filters using normalized lowercase rule ids."""
        self.rule_filters = [item.lower() for item in filters]

    def list_rules(self) -> Sequence[t.FeatureFlagMapping]:
        """Return loaded rules metadata for listing."""
        return [
            {
                c.Infra.RK_ID: rl.rule_id,
                c.Infra.NAME: rl.name,
                "description": rl.description,
                c.Infra.RK_ENABLED: rl.enabled,
                "severity": rl.severity,
            }
            for rl in self.rules
        ]

    # ── Rule resolution ───────────────────────────────────────────

    def _build_file_rules(self) -> Sequence[FlextInfraClassNestingRefactorRule]:
        return [FlextInfraClassNestingRefactorRule()]

    @staticmethod
    def _skip_rule_definition(
        rule_def: Mapping[str, t.Infra.InfraValue],
    ) -> bool:
        """Skip definitions handled by the dedicated file-rule pipeline."""
        fix_action = u.Infra.get_str_key(
            rule_def,
            c.Infra.RK_FIX_ACTION,
            default=u.Infra.get_str_key(rule_def, c.Infra.RK_ACTION),
            case="lower",
        )
        return fix_action == "nest_classes"

    def _build_rule(
        self, rule_def: Mapping[str, t.Infra.InfraValue]
    ) -> FlextInfraRefactorRule | None:
        fix_action = u.Infra.get_str_key(
            rule_def,
            c.Infra.RK_FIX_ACTION,
            default=u.Infra.get_str_key(rule_def, c.Infra.RK_ACTION),
            case="lower",
        )
        check = u.Infra.get_str_key(rule_def, c.Infra.VERB_CHECK, case="lower")
        for action_set, rule_class in self._RULE_ACTION_REGISTRY:
            if fix_action in action_set or check in action_set:
                return rule_class(rule_def)
        rule_id = str(rule_def.get(c.Infra.RK_ID, c.Infra.DEFAULT_UNKNOWN)).lower()
        if "signature" in rule_id and any(
            kw in rule_id for kw in ("propagate", "rename")
        ):
            return FlextInfraRefactorSignaturePropagationRule(rule_def)
        for keywords, rule_class in self._RULE_ID_FALLBACKS:
            if any(kw in rule_id for kw in keywords):
                return rule_class(rule_def)
        return None


__all__: list[str] = [
    "FlextInfraRefactorEngine",
]
