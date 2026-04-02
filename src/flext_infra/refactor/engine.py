"""Rope-based refactor engine for flext_infra.refactor.

Orchestrates declarative rules, safety stash, and violation analysis.
File collection via ``u.Infra`` utilities, rule subclasses in ``_engine_rules``.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from pydantic import TypeAdapter

from flext_infra import (
    FlextInfraClassNestingRefactorRule,
    FlextInfraRefactorEnsureFutureAnnotationsRule,
    FlextInfraRefactorImportModernizerRule,
    FlextInfraRefactorLegacyRemovalRule,
    FlextInfraRefactorMROClassMigrationRule,
    FlextInfraRefactorPatternCorrectionsRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorRuleDefinitionValidator,
    FlextInfraRefactorRuleLoader,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorViolationAnalyzer,
    c,
    m,
    r,
    t,
    u,
)
from flext_infra.refactor._engine_rules import (
    FlextInfraRefactorClassReconstructorRule,
    FlextInfraRefactorMRORedundancyChecker,
    FlextInfraRefactorSignaturePropagationRule,
    FlextInfraRefactorSymbolPropagationRule,
    FlextInfraRefactorTier0ImportFixRule,
    FlextInfraRefactorTypingAnnotationFixRule,
    FlextInfraRefactorTypingUnificationRule,
)

type _RuleEntry = tuple[frozenset[str], type[FlextInfraRefactorRule]]


class FlextInfraRefactorEngine:
    """Rope-based refactor engine orchestrating declarative rules."""

    _RULE_ACTION_REGISTRY: ClassVar[Sequence[_RuleEntry]] = [
        (
            c.Infra.FUTURE_FIX_ACTIONS | c.Infra.FUTURE_CHECKS,
            FlextInfraRefactorEnsureFutureAnnotationsRule,
        ),
        (c.Infra.LEGACY_FIX_ACTIONS, FlextInfraRefactorLegacyRemovalRule),
        (c.Infra.IMPORT_FIX_ACTIONS, FlextInfraRefactorImportModernizerRule),
        (c.Infra.CLASS_FIX_ACTIONS, FlextInfraRefactorClassReconstructorRule),
        (c.Infra.PATTERN_FIX_ACTIONS, FlextInfraRefactorPatternCorrectionsRule),
        (c.Infra.TYPE_ALIAS_FIX_ACTIONS, FlextInfraRefactorTypingUnificationRule),
        (c.Infra.TYPING_FIX_ACTIONS, FlextInfraRefactorTypingAnnotationFixRule),
        (c.Infra.TIER0_FIX_ACTIONS, FlextInfraRefactorTier0ImportFixRule),
        (frozenset({"migrate_to_class_mro"}), FlextInfraRefactorMROClassMigrationRule),
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
            FlextInfraRefactorLegacyRemovalRule,
        ),
        (frozenset({"import", "modernize"}), FlextInfraRefactorImportModernizerRule),
        (
            frozenset({"class", "reorder", "method"}),
            FlextInfraRefactorClassReconstructorRule,
        ),
        (
            frozenset({"redundant-cast", "dict-to-mapping", "container-invariance"}),
            FlextInfraRefactorPatternCorrectionsRule,
        ),
        (frozenset({"migrate-to-class-mro"}), FlextInfraRefactorMROClassMigrationRule),
        (frozenset({"mro"}), FlextInfraRefactorMRORedundancyChecker),
        (
            frozenset({"propagate", "symbol-rename", "rename"}),
            FlextInfraRefactorSymbolPropagationRule,
        ),
    ]

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize engine state and config file path."""
        self.config_path = config_path or Path(__file__).parent / "config.yml"
        config_map: Mapping[str, t.Infra.InfraValue] = {}
        self.config: t.Infra.InfraValue = config_map
        self.rules: MutableSequence[FlextInfraRefactorRule] = []
        self.file_rules: MutableSequence[FlextInfraClassNestingRefactorRule] = []
        self.rule_filters: MutableSequence[str] = []
        self.rule_loader = FlextInfraRefactorRuleLoader(self.config_path)
        self.rule_validator = FlextInfraRefactorRuleDefinitionValidator()
        self.safety_manager = FlextInfraRefactorSafetyManager()

    # ── Result helpers ────────────────────────────────────────────

    @staticmethod
    def _error_result(fp: Path, error: str) -> m.Infra.Result:
        """Build a failure result."""
        return m.Infra.Result(
            file_path=fp,
            success=False,
            modified=False,
            error=error,
            changes=[],
            refactored_code=None,
        )

    @staticmethod
    def _skip_result(fp: Path) -> m.Infra.Result:
        """Build a skip result for non-Python files."""
        return m.Infra.Result(
            file_path=fp,
            success=True,
            modified=False,
            changes=["Skipped non-Python file"],
            refactored_code=None,
        )

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
        _ = parser.add_argument("--pattern", default=c.Infra.Extensions.PYTHON_GLOB)
        _ = parser.add_argument("--dry-run", "-n", action="store_true")
        _ = parser.add_argument("--show-diff", "-d", action="store_true")
        _ = parser.add_argument("--impact-map-output", type=Path)
        _ = parser.add_argument("--analyze-violations", action="store_true")
        _ = parser.add_argument("--analysis-output", type=Path)
        _ = parser.add_argument("--config", "-c", type=Path)
        args = parser.parse_args()
        engine = FlextInfraRefactorEngine(config_path=args.config)
        cfg = engine.load_config()
        if not cfg.is_success:
            u.Infra.refactor_error(f"Config error: {cfg.error}")
            return 1
        if args.rules:
            engine.set_rule_filters([
                s.strip() for s in args.rules.split(",") if s.strip()
            ])
        rules_r = engine.load_rules()
        if not rules_r.is_success:
            u.Infra.refactor_error(f"Rules error: {rules_r.error}")
            return 1
        if args.list_rules:
            u.Infra.print_rules_table(engine.list_rules())
            return 0
        if args.analyze_violations:
            return engine._run_analyze_violations(args)
        return engine._run_refactor(args)

    # ── Config & rules ────────────────────────────────────────────

    def load_config(self) -> r[Mapping[str, t.Infra.InfraValue]]:
        """Load YAML configuration for this engine instance."""
        result = self.rule_loader.load_config()
        if result.is_success:
            self.config = TypeAdapter(Mapping[str, t.Infra.InfraValue]).validate_python(
                dict(result.value)
            )
            u.Infra.refactor_info(f"Loaded config from {self.config_path}")
        return result

    def load_rules(self) -> r[Sequence[FlextInfraRefactorRule]]:
        """Load and instantiate enabled rules from rules directory."""
        rr = self.rule_loader.load_rules(
            self.rule_filters,
            self.rule_validator,
            self._build_rule,
            self._build_file_rules,
        )
        if rr.is_failure:
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
                c.Infra.ReportKeys.ID: rl.rule_id,
                c.Infra.NAME: rl.name,
                "description": rl.description,
                c.Infra.ReportKeys.ENABLED: rl.enabled,
                "severity": rl.severity,
            }
            for rl in self.rules
        ]

    # ── Violation analysis ────────────────────────────────────────

    def _run_analyze_violations(self, args: argparse.Namespace) -> int:
        files = self._collect_files(args)
        if files is None:
            return 1
        analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(files)
        u.Infra.print_violation_summary(analysis)
        if args.analysis_output is not None:
            _ = u.Infra.write_json(
                args.analysis_output,
                analysis.model_dump(mode="json"),
                ensure_ascii=True,
            )
            u.Infra.refactor_info(f"Analysis report written: {args.analysis_output}")
        return 0

    # ── File collection ─────────────────────────────────────────────

    def _collect_files(self, args: argparse.Namespace) -> MutableSequence[Path] | None:
        if args.project:
            return u.Infra.collect_engine_project_files(
                self.rule_loader, self.config, args.project, pattern=args.pattern
            )
        if args.workspace:
            return list(
                u.Infra.collect_engine_workspace_files(
                    self.rule_loader, self.config, args.workspace, pattern=args.pattern
                )
            )
        if args.file:
            if not args.file.exists():
                u.Infra.refactor_error(f"File not found: {args.file}")
                return None
            return [args.file]
        if args.files:
            return [p for p in args.files if p.exists()]
        return []

    # ── Refactoring pipeline ──────────────────────────────────────

    def _run_refactor(self, args: argparse.Namespace) -> int:
        if args.project:
            results = list(
                self.refactor_project(
                    args.project, dry_run=args.dry_run, pattern=args.pattern
                )
            )
        elif args.workspace:
            results = list(
                self.refactor_workspace(
                    args.workspace, dry_run=args.dry_run, pattern=args.pattern
                )
            )
        elif args.file:
            if not args.file.exists():
                u.Infra.refactor_error(f"File not found: {args.file}")
                return 1
            original = args.file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            result = self.refactor_file(args.file, dry_run=args.dry_run)
            if args.show_diff and result.modified:
                u.Infra.print_diff(
                    original, result.refactored_code or original, args.file
                )
            results = [result]
        elif args.files:
            existing = [p for p in args.files if p.exists()]
            for p in args.files:
                if not p.exists():
                    u.Infra.refactor_error(f"File not found: {p}")
            results = list(self.refactor_files(existing, dry_run=args.dry_run))
        else:
            results: MutableSequence[m.Infra.Result] = []
        u.Infra.print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = u.Infra.write_impact_map(results, args.impact_map_output)
        return 0 if u.count(results, lambda item: not item.success) == 0 else 1

    def refactor_file(
        self, file_path: Path, *, dry_run: bool = False
    ) -> m.Infra.Result:
        """Refactor one file with currently loaded rules."""
        try:
            if file_path.suffix != c.Infra.Extensions.PYTHON:
                return self._skip_result(file_path)
            original = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            current, all_changes = original, list[str]()
            for fr in self.file_rules:
                res = fr.apply(file_path, dry_run=True)
                if not res.success:
                    return m.Infra.Result(
                        file_path=file_path,
                        success=False,
                        modified=False,
                        error=res.error,
                        changes=res.changes,
                        refactored_code=None,
                    )
                if res.modified and res.refactored_code:
                    current = res.refactored_code
                all_changes.extend(res.changes)
            for rule in self.rules:
                if rule.enabled:
                    current, changes = rule.apply(current, file_path)
                    all_changes.extend(changes)
            modified = current != original
            if not dry_run and modified:
                u.write_file(file_path, current, encoding=c.Infra.Encoding.DEFAULT)
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=all_changes,
                refactored_code=current,
            )
        except Exception as exc:
            return self._error_result(file_path, str(exc))

    def refactor_files(
        self, file_paths: Sequence[Path], *, dry_run: bool = False
    ) -> Sequence[m.Infra.Result]:
        """Refactor many files and collect individual results."""
        results: MutableSequence[m.Infra.Result] = []
        for fp in file_paths:
            result = self.refactor_file(fp, dry_run=dry_run)
            results.append(result)
            if result.success and result.modified:
                u.Infra.refactor_info(
                    f"{'[DRY-RUN] ' if dry_run else ''}Modified: {fp.name}"
                )
                for ch in result.changes:
                    u.Infra.refactor_info(f"  - {ch}")
            elif result.success:
                u.Infra.refactor_debug(f"Unchanged: {fp.name}")
            else:
                u.Infra.refactor_error(f"Failed: {fp.name} - {result.error}")
        return results

    # ── Safety ────────────────────────────────────────────────────

    def _try_safety_stash(
        self, target: Path, *, apply_safety: bool, dry_run: bool
    ) -> t.Infra.Pair[str, Sequence[m.Infra.Result] | None]:
        if not apply_safety or dry_run:
            return "", None
        stash = self.safety_manager.create_pre_transformation_stash(target)
        if stash.is_failure:
            msg = stash.error or "pre-transformation stash failed"
            u.Infra.refactor_error(msg)
            return "", [self._error_result(target, msg)]
        return stash.value, None

    def _finalize_safety(
        self, *, target: Path, stash_ref: str, results: MutableSequence[m.Infra.Result]
    ) -> None:
        val = self.safety_manager.run_semantic_validation(target)
        if val.is_failure:
            msg = val.error or "semantic validation failed"
            self.safety_manager.request_emergency_stop(msg)
            u.Infra.refactor_error(msg)
            rb = self.safety_manager.rollback(target, stash_ref)
            if rb.is_failure:
                u.Infra.refactor_error(rb.error or "rollback failed")
            results.append(self._error_result(target, msg))
            return
        cl = self.safety_manager.clear_checkpoint()
        if cl.is_failure:
            u.Infra.refactor_error(cl.error or "checkpoint clear failed")

    # ── Project / workspace ───────────────────────────────────────

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor files under configured project directories."""
        stash_ref, err = self._try_safety_stash(
            project_path, apply_safety=apply_safety, dry_run=dry_run
        )
        if err is not None:
            return err
        collected = u.Infra.collect_engine_project_files(
            self.rule_loader, self.config, project_path, pattern=pattern
        )
        if collected is None:
            return [
                self._error_result(
                    project_path, f"File iteration failed for {project_path}"
                )
            ]
        u.Infra.refactor_info(f"Found {len(collected)} files to process")
        results: MutableSequence[m.Infra.Result] = list(
            u.Infra.run_rope_pre_hooks(project_path, dry_run=dry_run)
        )
        results.extend(self.refactor_files(collected, dry_run=dry_run))
        results.extend(u.Infra.run_rope_post_hooks(project_path, dry_run=dry_run))
        if apply_safety and not dry_run:
            cp = self.safety_manager.save_checkpoint_state(
                project_path,
                status="transformed",
                stash_ref=stash_ref,
                processed_targets=[str(f) for f in collected],
            )
            if cp.is_failure:
                u.Infra.refactor_error(cp.error or "checkpoint save failed")
            self._finalize_safety(
                target=project_path, stash_ref=stash_ref, results=results
            )
        return results

    def refactor_workspace(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor all discoverable workspace projects."""
        root = workspace_root.resolve()
        if not root.exists() or not root.is_dir():
            u.Infra.refactor_error(f"Invalid workspace root: {workspace_root}")
            return []
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        projects = u.Infra.discover_project_roots(
            workspace_root=root, scan_dirs=scan_dirs or None
        )
        if not projects:
            u.Infra.refactor_error(f"No projects discovered under: {workspace_root}")
            return []
        u.Infra.refactor_info(f"Discovered {len(projects)} projects in workspace")
        stash_ref, err = self._try_safety_stash(
            root, apply_safety=apply_safety, dry_run=dry_run
        )
        if err is not None:
            return err
        results: MutableSequence[m.Infra.Result] = []
        processed: MutableSequence[str] = []
        results.extend(u.Infra.run_rope_pre_hooks(root, dry_run=dry_run))
        for proj in projects:
            if apply_safety and self.safety_manager.is_emergency_stop_requested():
                break
            u.Infra.refactor_header(f"Project: {proj}")
            results.extend(
                self.refactor_project(
                    proj, dry_run=dry_run, pattern=pattern, apply_safety=False
                )
            )
            if apply_safety and not dry_run:
                processed.append(str(proj))
                cp = self.safety_manager.save_checkpoint_state(
                    root,
                    status="running",
                    stash_ref=stash_ref,
                    processed_targets=list(processed),
                )
                if cp.is_failure:
                    u.Infra.refactor_error(cp.error or "checkpoint save failed")
        results.extend(u.Infra.run_rope_post_hooks(root, dry_run=dry_run))
        if apply_safety and not dry_run:
            self._finalize_safety(target=root, stash_ref=stash_ref, results=results)
        return results

    # ── Rule resolution ───────────────────────────────────────────

    def _build_file_rules(self) -> Sequence[FlextInfraClassNestingRefactorRule]:
        return [FlextInfraClassNestingRefactorRule()]

    def _build_rule(
        self, rule_def: Mapping[str, t.Infra.InfraValue]
    ) -> FlextInfraRefactorRule | None:
        fix_action = u.Infra.get_str_key(
            rule_def,
            c.Infra.ReportKeys.FIX_ACTION,
            default=u.Infra.get_str_key(rule_def, c.Infra.ReportKeys.ACTION),
            lower=True,
        )
        check = u.Infra.get_str_key(rule_def, c.Infra.Verbs.CHECK, lower=True)
        for action_set, rule_class in self._RULE_ACTION_REGISTRY:
            if fix_action in action_set or check in action_set:
                return rule_class(rule_def)
        rule_id = str(
            rule_def.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN)
        ).lower()
        if "signature" in rule_id and any(
            kw in rule_id for kw in ("propagate", "rename")
        ):
            return FlextInfraRefactorSignaturePropagationRule(rule_def)
        for keywords, rule_class in self._RULE_ID_FALLBACKS:
            if any(kw in rule_id for kw in keywords):
                return rule_class(rule_def)
        return None


__all__ = [
    "FlextInfraRefactorClassReconstructorRule",
    "FlextInfraRefactorEngine",
    "FlextInfraRefactorMRORedundancyChecker",
    "FlextInfraRefactorSignaturePropagationRule",
    "FlextInfraRefactorSymbolPropagationRule",
    "FlextInfraRefactorTier0ImportFixRule",
    "FlextInfraRefactorTypingAnnotationFixRule",
    "FlextInfraRefactorTypingUnificationRule",
]
