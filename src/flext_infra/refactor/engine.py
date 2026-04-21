"""Rope-based refactor engine for flext_infra.refactor.

Orchestrates declarative rules, safety stash, and violation analysis.
File collection flows through ``u.Infra`` while rule loading is delegated
directly to the shared ``flext-cli`` rules DSL.
"""

from __future__ import annotations

import argparse
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path

from flext_cli import cli

from flext_infra import (
    FlextInfraRefactorSafetyManager,
    c,
    m,
    p,
    r,
    t,
    u,
)

from .engine_file import (
    FlextInfraRefactorEngineFileMixin,
    _ClassNestingPostCheckGate,
)
from .engine_helpers import FlextInfraRefactorEngineHelpersMixin
from .engine_text import FlextInfraRefactorEngineTextMixin


class FlextInfraRefactorEngine(
    FlextInfraRefactorEngineTextMixin,
    FlextInfraRefactorEngineFileMixin,
    FlextInfraRefactorEngineHelpersMixin,
):
    """Rope-based refactor engine orchestrating declarative rules."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize engine state and settings file path."""
        self.config_path = config_path or Path(__file__).parent / "settings.yml"
        config_map: Mapping[str, t.Infra.InfraValue] = {}
        self.settings: Mapping[str, t.Infra.InfraValue] = config_map
        self.rules: MutableSequence[
            tuple[c.Infra.RefactorRuleKind, t.Cli.RuleDefinition]
        ] = []
        self.file_rules: MutableSequence[
            tuple[c.Infra.RefactorFileRuleKind, t.Cli.RuleDefinition]
        ] = []
        self.rule_filters: MutableSequence[str] = []
        self.safety_manager = FlextInfraRefactorSafetyManager()
        self._class_nesting_config: t.Infra.ContainerDict | None = None
        self._class_nesting_policy_by_family: (
            Mapping[str, m.Infra.ClassNestingPolicy] | None
        ) = None
        self._class_nesting_gate: _ClassNestingPostCheckGate | None = None

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
        engine = FlextInfraRefactorEngine(config_path=args.config)
        cfg = engine.load_config()
        if not cfg.success:
            u.Cli.error(f"Config error: {cfg.error}")
            return 1
        if args.rules:
            engine.set_rule_filters([
                item.strip() for item in args.rules.split(",") if item.strip()
            ])
        rules_r = engine.load_rules()
        if not rules_r.success:
            u.Cli.error(f"Rules error: {rules_r.error}")
            return 1
        if args.list_rules:
            engine._print_rules_table(engine.list_rules())
            return 0
        if args.analyze_violations:
            return engine._run_analyze_violations(args)
        return engine._run_refactor(args)

    def load_config(self) -> p.Result[Mapping[str, t.Infra.InfraValue]]:
        """Load YAML configuration for this engine instance."""
        result = cli.rules_load_scoped_config(
            self.config_path,
            scope_key=c.Infra.RK_REFACTOR_ENGINE,
            allowed_keys=c.Infra.ENGINE_CONFIG_KEYS,
        )
        if result.success:
            self.settings = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                dict(result.value)
            )
            u.Cli.info(f"Loaded settings from {self.config_path}")
        return result

    def load_rules(
        self,
    ) -> p.Result[Sequence[tuple[c.Infra.RefactorRuleKind, t.Cli.RuleDefinition]]]:
        """Load enabled declarative rules from the shared CLI DSL."""
        rr = cli.rules_load_local_definitions(
            self.config_path,
            package_rules_dir=Path(__file__).resolve().parent.parent / c.Infra.RK_RULES,
            rule_filters=self.rule_filters,
            rule_catalog=c.Infra.RULE_MATCHERS_BY_KIND,
            file_rule_catalog=c.Infra.FILE_RULE_MATCHERS_BY_KIND,
            registry_filename=c.Infra.ENGINE_REGISTRY_FILENAME,
            rules_key=c.Infra.RK_RULES,
            rule_id_key=c.Infra.RK_ID,
            enabled_key=c.Infra.RK_ENABLED,
        )
        if rr.failure:
            return r[
                Sequence[tuple[c.Infra.RefactorRuleKind, t.Cli.RuleDefinition]]
            ].fail(rr.error or "")
        loaded_rules, loaded_file_rules = rr.value
        self.rules = list(loaded_rules)
        self.file_rules = list(loaded_file_rules)
        u.Cli.info(f"Loaded {len(self.rules)} rules")
        if self.file_rules:
            u.Cli.info(f"Loaded {len(self.file_rules)} file rules")
        if self.rule_filters:
            u.Cli.info(f"Active filters: {', '.join(self.rule_filters)}")
        return r[Sequence[tuple[c.Infra.RefactorRuleKind, t.Cli.RuleDefinition]]].ok(
            loaded_rules
        )

    @staticmethod
    def _print_rules_table(rows: Sequence[t.FeatureFlagMapping]) -> None:
        """Render and print refactor rules list using CLI table/output families."""
        data_result = u.Cli.tables_normalize_data(rows)
        if data_result.failure:
            u.Cli.error(data_result.error or "failed to normalize rules table")
            return
        settings_result = u.Cli.tables_resolve_config(
            headers=list(c.Infra.RULE_TABLE_HEADERS),
        )
        if settings_result.failure:
            u.Cli.error(settings_result.error or "failed to resolve table settings")
            return
        rendered_result = u.Cli.tables_render(data_result.value, settings_result.value)
        if rendered_result.failure:
            u.Cli.error(rendered_result.error or "failed to render rules table")
            return
        u.Cli.emit_raw(rendered_result.value)

    def set_rule_filters(self, filters: t.StrSequence) -> None:
        """Set active rule filters using normalized lowercase rule ids."""
        self.rule_filters = [item.lower() for item in filters]

    def list_rules(self) -> Sequence[t.FeatureFlagMapping]:
        """Return loaded rules metadata for listing."""
        return [
            {
                c.Infra.RK_ID: str(
                    settings.get(c.Infra.RK_ID, c.Infra.DEFAULT_UNKNOWN)
                ),
                c.Infra.NAME: str(
                    settings.get(
                        c.Infra.NAME,
                        settings.get(c.Infra.RK_ID, c.Infra.DEFAULT_UNKNOWN),
                    )
                ),
                c.Infra.RK_DESCRIPTION: str(settings.get(c.Infra.RK_DESCRIPTION, "")),
                c.Infra.RK_ENABLED: bool(settings.get(c.Infra.RK_ENABLED, True)),
                c.Infra.RK_SEVERITY: str(
                    settings.get(c.Infra.RK_SEVERITY, c.Infra.SeverityLevel.WARNING)
                ),
            }
            for _, settings in self.rules
        ]


__all__: list[str] = ["FlextInfraRefactorEngine"]
