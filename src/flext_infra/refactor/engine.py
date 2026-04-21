"""Refactor engine composition root for flext_infra.refactor."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorSafetyManager,
    c,
    m,
    p,
    t,
    u,
)

from .loader import FlextInfraRefactorRuleLoader
from .orchestrator import FlextInfraRefactorOrchestrator


class FlextInfraRefactorEngine:
    """Composition root wiring loader, orchestrator, and safety services."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the composed refactor engine services."""
        self.config_path = config_path or Path(__file__).parent / "settings.yml"
        self.rule_loader = FlextInfraRefactorRuleLoader(self.config_path)
        self.orchestrator = FlextInfraRefactorOrchestrator(
            self.rule_loader,
            safety_manager=FlextInfraRefactorSafetyManager(),
        )

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
            engine.print_rules_table(engine.list_rules())
            return 0
        if args.analyze_violations:
            return engine.run_analyze_violations(args)
        return engine.run_refactor(args)

    @property
    def settings(self) -> Mapping[str, t.Infra.InfraValue]:
        """Expose the loader settings for existing consumers."""
        return self.rule_loader.settings

    @settings.setter
    def settings(self, value: Mapping[str, t.Infra.InfraValue]) -> None:
        self.rule_loader.settings = value

    @property
    def rules(
        self,
    ) -> MutableSequence[t.Infra.RuleSelection[c.Infra.RefactorRuleKind]]:
        """Expose loaded text-rule selections for compatibility."""
        return self.rule_loader.rules

    @rules.setter
    def rules(
        self,
        value: MutableSequence[t.Infra.RuleSelection[c.Infra.RefactorRuleKind]],
    ) -> None:
        self.rule_loader.rules = value

    @property
    def file_rules(
        self,
    ) -> MutableSequence[t.Infra.RuleSelection[c.Infra.RefactorFileRuleKind]]:
        """Expose loaded file-rule selections for compatibility."""
        return self.rule_loader.file_rules

    @file_rules.setter
    def file_rules(
        self,
        value: MutableSequence[t.Infra.RuleSelection[c.Infra.RefactorFileRuleKind]],
    ) -> None:
        self.rule_loader.file_rules = value

    @property
    def rule_filters(self) -> MutableSequence[str]:
        """Expose normalized rule filters for compatibility."""
        return self.rule_loader.rule_filters

    @property
    def safety_manager(self) -> FlextInfraRefactorSafetyManager:
        """Expose the orchestrator safety manager for compatibility."""
        return self.orchestrator.safety_manager

    @safety_manager.setter
    def safety_manager(self, value: FlextInfraRefactorSafetyManager) -> None:
        self.orchestrator.safety_manager = value

    def load_config(self) -> p.Result[Mapping[str, t.Infra.InfraValue]]:
        """Delegate config loading to the dedicated refactor loader."""
        return self.rule_loader.load_config()

    def load_rules(
        self,
    ) -> p.Result[
        t.Infra.LoadedRuleSelections[
            c.Infra.RefactorRuleKind,
            c.Infra.RefactorFileRuleKind,
        ]
    ]:
        """Delegate rule loading to the dedicated refactor loader."""
        return self.rule_loader.load_rules()

    def set_rule_filters(self, filters: t.StrSequence) -> None:
        """Delegate rule-filter normalization to the dedicated loader."""
        self.rule_loader.set_rule_filters(filters)

    def list_rules(self) -> Sequence[t.FeatureFlagMapping]:
        """Delegate rules listing to the dedicated loader."""
        return self.rule_loader.list_rules()

    @staticmethod
    def print_rules_table(rows: Sequence[t.FeatureFlagMapping]) -> None:
        """Delegate table rendering to the dedicated loader."""
        FlextInfraRefactorRuleLoader.print_rules_table(rows)

    def run_analyze_violations(self, args: t.Infra.CliNamespace) -> int:
        """Delegate violation analysis to the dedicated orchestrator."""
        return self.orchestrator.run_analyze_violations(args)

    def run_refactor(self, args: t.Infra.CliNamespace) -> int:
        """Delegate CLI refactor execution to the dedicated orchestrator."""
        return self.orchestrator.run_refactor(args)

    def refactor_file(
        self, file_path: Path, *, dry_run: bool = False
    ) -> m.Infra.Result:
        """Delegate single-file refactoring to the dedicated orchestrator."""
        return self.orchestrator.refactor_file(file_path, dry_run=dry_run)

    def refactor_files(
        self,
        file_paths: Sequence[Path],
        *,
        dry_run: bool = False,
    ) -> Sequence[m.Infra.Result]:
        """Delegate multi-file refactoring to the dedicated orchestrator."""
        return self.orchestrator.refactor_files(file_paths, dry_run=dry_run)

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Delegate project refactoring to the dedicated orchestrator."""
        return self.orchestrator.refactor_project(
            project_path,
            dry_run=dry_run,
            pattern=pattern,
            apply_safety=apply_safety,
        )

    def refactor_workspace(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Delegate workspace refactoring to the dedicated orchestrator."""
        return self.orchestrator.refactor_workspace(
            workspace_root,
            dry_run=dry_run,
            pattern=pattern,
            apply_safety=apply_safety,
        )


__all__: list[str] = ["FlextInfraRefactorEngine"]
