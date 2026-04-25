"""Refactor engine composition root for flext_infra.refactor."""

from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorSafetyManager,
    c,
    m,
    p,
    t,
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
