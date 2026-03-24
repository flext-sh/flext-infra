"""Refactor engine and CLI for flext_infra.refactor."""

from __future__ import annotations

import argparse
import fnmatch
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import TypeAdapter

from flext_infra import (
    FlextInfraClassNestingRefactorRule,
    FlextInfraRefactorClassReconstructorRule,
    FlextInfraRefactorEnsureFutureAnnotationsRule,
    FlextInfraRefactorImportModernizerRule,
    FlextInfraRefactorLegacyRemovalRule,
    FlextInfraRefactorMROClassMigrationRule,
    FlextInfraRefactorMRORedundancyChecker,
    FlextInfraRefactorPatternCorrectionsRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorRuleDefinitionValidator,
    FlextInfraRefactorRuleLoader,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorSignaturePropagationRule,
    FlextInfraRefactorSymbolPropagationRule,
    FlextInfraRefactorTier0ImportFixRule,
    FlextInfraRefactorTypingAnnotationFixRule,
    FlextInfraRefactorTypingUnificationRule,
    FlextInfraRefactorViolationAnalyzer,
    c,
    m,
    r,
    t,
    u,
)


class FlextInfraRefactorEngine:
    """Engine de refatoracao que orquestra regras declarativas."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize engine state and config file path."""
        self.config_path = config_path or self._default_config_path()
        config_map: Mapping[str, t.Infra.InfraValue] = {}
        self.config: t.Infra.InfraValue = config_map
        self.rules: MutableSequence[FlextInfraRefactorRule] = []
        self.file_rules: MutableSequence[FlextInfraClassNestingRefactorRule] = []
        self.rule_filters: MutableSequence[str] = []
        self.rule_loader = FlextInfraRefactorRuleLoader(self.config_path)
        self.rule_validator = FlextInfraRefactorRuleDefinitionValidator()
        self.safety_manager = self._build_safety_manager()

    @staticmethod
    def _build_safety_manager() -> FlextInfraRefactorSafetyManager:
        return FlextInfraRefactorSafetyManager()

    def _try_safety_stash(
        self,
        target_path: Path,
        *,
        apply_safety: bool,
        dry_run: bool,
    ) -> tuple[str, Sequence[m.Infra.Result] | None]:
        """Attempt to create a safety stash before transformations.

        Returns (stash_ref, None) on success or ("", error_results) on failure.
        """
        if not apply_safety or dry_run:
            return "", None
        stash_ref_result = self._prepare_safety_stash(target_path)
        if stash_ref_result.is_failure:
            error_msg = stash_ref_result.error or "pre-transformation stash failed"
            return "", [
                m.Infra.Result(
                    file_path=target_path,
                    success=False,
                    modified=False,
                    error=error_msg,
                    changes=[],
                    refactored_code=None,
                ),
            ]
        return stash_ref_result.value, None

    @staticmethod
    def build_impact_map(
        results: Sequence[m.Infra.Result],
    ) -> Sequence[t.StrMapping]:
        """Build a normalized impact-map payload from refactor results."""
        return u.Infra.build_impact_map(results)

    @staticmethod
    def write_impact_map(
        results: Sequence[m.Infra.Result],
        output_path: Path,
    ) -> bool:
        """Write the impact-map payload to the target output path."""
        return u.Infra.write_impact_map(results, output_path)

    @staticmethod
    def main() -> int:
        """Run the refactor CLI entrypoint and exit with the status code."""
        parser = argparse.ArgumentParser(
            description="Flext Refactor Engine - Declarative code transformation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        mode_group = parser.add_mutually_exclusive_group(required=True)
        _ = mode_group.add_argument("--project", "-p", type=Path)
        _ = mode_group.add_argument("--workspace", "-w", type=Path)
        _ = mode_group.add_argument("--file", "-f", type=Path)
        _ = mode_group.add_argument("--files", nargs="+", type=Path)
        _ = mode_group.add_argument("--list-rules", "-l", action="store_true")
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
        config_result = engine.load_config()
        if not config_result.is_success:
            u.Infra.refactor_error(f"Config error: {config_result.error}")
            return 1
        if args.rules:
            rule_filters = [
                item.strip() for item in args.rules.split(",") if item.strip()
            ]
            engine.set_rule_filters(rule_filters)
        rules_result = engine.load_rules()
        if not rules_result.is_success:
            u.Infra.refactor_error(f"Rules error: {rules_result.error}")
            return 1
        if args.list_rules:
            u.Infra.print_rules_table(engine.list_rules())
            return 0
        if args.analyze_violations:
            files_to_analyze: MutableSequence[Path] = []
            if args.project:
                scan_dirs = frozenset(
                    engine.rule_loader.extract_project_scan_dirs(engine.config),
                )
                iter_result = u.Infra.iter_python_files(
                    workspace_root=args.project,
                    project_roots=[args.project],
                    include_tests=c.Infra.Directories.TESTS in scan_dirs,
                    include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
                    include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
                    src_dirs=scan_dirs or None,
                )
                if iter_result.is_failure:
                    u.Infra.refactor_error(
                        iter_result.error
                        or f"File iteration failed for project: {args.project}",
                    )
                    return 1
                ignore_items, extension_items = (
                    engine.rule_loader.extract_engine_file_filters(engine.config)
                )
                ignore_patterns = {str(item) for item in ignore_items}
                allowed_extensions = {str(item) for item in extension_items}
                files_to_analyze = [
                    file_path
                    for file_path in iter_result.value
                    if (
                        fnmatch.fnmatch(
                            str(file_path.relative_to(args.project)),
                            args.pattern,
                        )
                        or fnmatch.fnmatch(file_path.name, args.pattern)
                    )
                    and (
                        not allowed_extensions or file_path.suffix in allowed_extensions
                    )
                    and file_path.name not in ignore_patterns
                    and not any(
                        part in ignore_patterns
                        for part in file_path.relative_to(args.project).parts
                    )
                    and not any(
                        fnmatch.fnmatch(
                            str(file_path.relative_to(args.project)),
                            ignore_pattern,
                        )
                        for ignore_pattern in ignore_patterns
                    )
                ]
            elif args.workspace:
                files_to_analyze = list(
                    engine.collect_workspace_files(
                        args.workspace,
                        pattern=args.pattern,
                    ),
                )
            elif args.file:
                if not args.file.exists():
                    u.Infra.refactor_error(f"File not found: {args.file}")
                    return 1
                files_to_analyze = [args.file]
            elif args.files:
                files_to_analyze = [item for item in args.files if item.exists()]
            analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(
                files_to_analyze,
            )
            u.Infra.print_violation_summary(analysis)
            if args.analysis_output is not None:
                _ = u.Infra.write_json(
                    args.analysis_output,
                    analysis.model_dump(mode="json"),
                    ensure_ascii=True,
                )
                u.Infra.refactor_info(
                    f"Analysis report written: {args.analysis_output}",
                )
            return 0
        results: MutableSequence[m.Infra.Result] = []
        if args.project:
            results = list(
                engine.refactor_project(
                    args.project,
                    dry_run=args.dry_run,
                    pattern=args.pattern,
                ),
            )
        elif args.workspace:
            results = list(
                engine.refactor_workspace(
                    args.workspace,
                    dry_run=args.dry_run,
                    pattern=args.pattern,
                ),
            )
        elif args.file:
            if not args.file.exists():
                u.Infra.refactor_error(f"File not found: {args.file}")
                return 1
            original_code = args.file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            result_single = engine.refactor_file(args.file, dry_run=args.dry_run)
            results = [result_single]
            if args.show_diff and result_single.modified:
                refactored_code = result_single.refactored_code or original_code
                u.Infra.print_diff(original_code, refactored_code, args.file)
        elif args.files:
            existing_files = [item for item in args.files if item.exists()]
            missing_files = [item for item in args.files if not item.exists()]
            for file_path in missing_files:
                u.Infra.refactor_error(f"File not found: {file_path}")
            results = list(engine.refactor_files(existing_files, dry_run=args.dry_run))
        u.Infra.print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = u.Infra.write_impact_map(results, args.impact_map_output)
        failed = sum(1 for item in results if not item.success)
        return 0 if failed == 0 else 1

    def collect_workspace_files(
        self,
        workspace_root: Path,
        *,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
    ) -> Sequence[Path]:
        """Collect all candidate files under workspace projects."""
        root = workspace_root.resolve()
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        project_paths = u.Infra.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        ignore_items, extension_items = self.rule_loader.extract_engine_file_filters(
            self.config,
        )
        ignore_patterns = {str(item) for item in ignore_items}
        allowed_extensions = {str(item) for item in extension_items}
        all_files: MutableSequence[Path] = []
        for project in project_paths:
            iter_result = u.Infra.iter_python_files(
                workspace_root=root,
                project_roots=[project],
                include_tests=c.Infra.Directories.TESTS in scan_dirs,
                include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
                include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
                src_dirs=scan_dirs or None,
            )
            if iter_result.is_failure:
                u.Infra.refactor_error(
                    iter_result.error or f"File iteration failed for {project}",
                )
                continue
            for py_file in iter_result.value:
                relative_path = py_file.relative_to(project)
                relative_path_str = str(relative_path)
                if not (
                    fnmatch.fnmatch(relative_path_str, pattern)
                    or fnmatch.fnmatch(py_file.name, pattern)
                ):
                    continue
                if allowed_extensions and py_file.suffix not in allowed_extensions:
                    continue
                if py_file.name in ignore_patterns:
                    continue
                if any(part in ignore_patterns for part in relative_path.parts):
                    continue
                if any(
                    fnmatch.fnmatch(relative_path_str, ignore_pattern)
                    for ignore_pattern in ignore_patterns
                ):
                    continue
                all_files.append(py_file)
        return all_files

    def list_rules(self) -> Sequence[Mapping[str, str | bool]]:
        """Return loaded rules metadata for listing."""
        return [
            {
                c.Infra.ReportKeys.ID: rule.rule_id,
                c.Infra.Toml.NAME: rule.name,
                "description": rule.description,
                c.Infra.ReportKeys.ENABLED: rule.enabled,
                "severity": rule.severity,
            }
            for rule in self.rules
        ]

    def load_config(self) -> r[Mapping[str, t.Infra.InfraValue]]:
        """Load YAML configuration for this engine instance."""
        result = self.rule_loader.load_config()
        if result.is_success:
            config_dict: Mapping[str, t.Infra.InfraValue] = TypeAdapter(
                Mapping[str, t.Infra.InfraValue],
            ).validate_python(dict(result.value.items()))
            self.config = config_dict
            u.Infra.refactor_info(f"Loaded config from {self.config_path}")
        return result

    def load_rules(self) -> r[Sequence[FlextInfraRefactorRule]]:
        """Load and instantiate enabled rules from rules directory."""
        rules_result = self.rule_loader.load_rules(
            self.rule_filters,
            self.rule_validator,
            self._build_rule,
            self._build_file_rules,
        )
        if rules_result.is_failure:
            return r[Sequence[FlextInfraRefactorRule]].fail(rules_result.error or "")
        loaded_rules, loaded_file_rules = rules_result.value
        self.rules = list(loaded_rules)
        self.file_rules = list(loaded_file_rules)
        u.Infra.refactor_info(f"Loaded {len(self.rules)} rules")
        if self.file_rules:
            u.Infra.refactor_info(
                f"Loaded {len(self.file_rules)} file rules",
            )
        if self.rule_filters:
            u.Infra.refactor_info(
                f"Active filters: {', '.join(self.rule_filters)}",
            )
        return r[Sequence[FlextInfraRefactorRule]].ok(loaded_rules)

    def refactor_file(
        self,
        file_path: Path,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Refactor one file with currently loaded rules."""
        try:
            if file_path.suffix != c.Infra.Extensions.PYTHON:
                return m.Infra.Result(
                    file_path=file_path,
                    success=True,
                    modified=False,
                    changes=["Skipped non-Python file"],
                    refactored_code=None,
                )
            original_source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            source = original_source
            all_changes: MutableSequence[str] = []
            file_rule_modified = False
            for file_rule in self.file_rules:
                file_rule_result = file_rule.apply(file_path, dry_run=True)
                if not file_rule_result.success:
                    return m.Infra.Result(
                        file_path=file_path,
                        success=False,
                        modified=False,
                        error=file_rule_result.error,
                        changes=file_rule_result.changes,
                        refactored_code=None,
                    )
                if file_rule_result.modified and file_rule_result.refactored_code:
                    source = file_rule_result.refactored_code
                    file_rule_modified = True
                all_changes.extend(file_rule_result.changes)
            tree = u.Infra.parse_cst_from_source(source)
            if tree is None:
                return m.Infra.Result(
                    file_path=file_path,
                    success=False,
                    modified=False,
                    error="parse_failed",
                    changes=[],
                    refactored_code=None,
                )
            for rule in self.rules:
                if rule.enabled:
                    tree, changes = rule.apply(tree, file_path)
                    all_changes.extend(changes)
            result_code = tree.code
            modified = file_rule_modified or result_code != original_source
            if not dry_run and modified:
                u.write_file(file_path, result_code, encoding=c.Infra.Encoding.DEFAULT)
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=all_changes,
                refactored_code=result_code,
            )
        except Exception as exc:
            return m.Infra.Result(
                file_path=file_path,
                success=False,
                modified=False,
                error=str(exc),
                changes=[],
                refactored_code=None,
            )

    def refactor_files(
        self,
        file_paths: Sequence[Path],
        *,
        dry_run: bool = False,
    ) -> Sequence[m.Infra.Result]:
        """Refactor many files and collect individual results."""
        results: MutableSequence[m.Infra.Result] = []
        for file_path in file_paths:
            if file_path.suffix != c.Infra.Extensions.PYTHON:
                u.Infra.refactor_info(
                    f"Skipped non-Python file: {file_path.name}",
                )
                results.append(
                    m.Infra.Result(
                        file_path=file_path,
                        success=True,
                        modified=False,
                        changes=["Skipped non-Python file"],
                        refactored_code=None,
                    ),
                )
                continue
            result = self.refactor_file(file_path, dry_run=dry_run)
            results.append(result)
            if result.success:
                if result.modified:
                    u.Infra.refactor_info(
                        f"{('[DRY-RUN] ' if dry_run else '')}Modified: {file_path.name}",
                    )
                    for change in result.changes:
                        u.Infra.refactor_info(f"  - {change}")
                else:
                    u.Infra.refactor_debug(f"Unchanged: {file_path.name}")
            else:
                u.Infra.refactor_error(
                    f"Failed: {file_path.name} - {result.error}",
                )
        return results

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.Extensions.PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor files under configured project directories matching the pattern."""
        stash_ref, stash_error = self._try_safety_stash(
            project_path,
            apply_safety=apply_safety,
            dry_run=dry_run,
        )
        if stash_error is not None:
            return stash_error
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        iter_result = u.Infra.iter_python_files(
            workspace_root=project_path,
            project_roots=[project_path],
            include_tests=c.Infra.Directories.TESTS in scan_dirs,
            include_examples=c.Infra.Directories.EXAMPLES in scan_dirs,
            include_scripts=c.Infra.Directories.SCRIPTS in scan_dirs,
            src_dirs=scan_dirs or None,
        )
        if iter_result.is_failure:
            error_msg = iter_result.error or f"File iteration failed for {project_path}"
            u.Infra.refactor_error(error_msg)
            return [
                m.Infra.Result(
                    file_path=project_path,
                    success=False,
                    modified=False,
                    error=error_msg,
                    changes=[],
                    refactored_code=None,
                ),
            ]
        ignore_items, extension_items = self.rule_loader.extract_engine_file_filters(
            self.config,
        )
        ignore_patterns = {str(item) for item in ignore_items}
        allowed_extensions = {str(item) for item in extension_items}
        files = [
            file_path
            for file_path in iter_result.value
            if (
                fnmatch.fnmatch(str(file_path.relative_to(project_path)), pattern)
                or fnmatch.fnmatch(file_path.name, pattern)
            )
            and (not allowed_extensions or file_path.suffix in allowed_extensions)
            and file_path.name not in ignore_patterns
            and not any(
                part in ignore_patterns
                for part in file_path.relative_to(project_path).parts
            )
            and not any(
                fnmatch.fnmatch(
                    str(file_path.relative_to(project_path)),
                    ignore_pattern,
                )
                for ignore_pattern in ignore_patterns
            )
        ]
        u.Infra.refactor_info(f"Found {len(files)} files to process")
        results: MutableSequence[m.Infra.Result] = list(
            self.refactor_files(files, dry_run=dry_run),
        )
        if apply_safety and (not dry_run):
            checkpoint_result = self.safety_manager.save_checkpoint_state(
                project_path,
                status="transformed",
                stash_ref=stash_ref,
                processed_targets=[str(file_path) for file_path in files],
            )
            if checkpoint_result.is_failure:
                u.Infra.refactor_error(
                    checkpoint_result.error or "checkpoint save failed",
                )
            self._run_safety_validation_and_finalize(
                target_path=project_path,
                stash_ref=stash_ref,
                results=results,
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
        """Refactor all discoverable workspace projects with one command."""
        root = workspace_root.resolve()
        if not root.exists() or not root.is_dir():
            u.Infra.refactor_error(
                f"Invalid workspace root: {workspace_root}",
            )
            return []
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        project_paths = u.Infra.discover_project_roots(
            workspace_root=root,
            scan_dirs=scan_dirs or None,
        )
        if not project_paths:
            u.Infra.refactor_error(
                f"No projects discovered under workspace root: {workspace_root}",
            )
            return []
        u.Infra.refactor_info(
            f"Discovered {len(project_paths)} projects in workspace",
        )
        results: MutableSequence[m.Infra.Result] = []
        processed_targets: MutableSequence[str] = []
        stash_ref, stash_error = self._try_safety_stash(
            root,
            apply_safety=apply_safety,
            dry_run=dry_run,
        )
        if stash_error is not None:
            return stash_error
        for project in project_paths:
            if apply_safety and self.safety_manager.is_emergency_stop_requested():
                break
            u.Infra.refactor_header(f"Project: {project}")
            project_results = self.refactor_project(
                project,
                dry_run=dry_run,
                pattern=pattern,
                apply_safety=False,
            )
            results.extend(project_results)
            if apply_safety and (not dry_run):
                processed_targets.append(str(project))
                checkpoint_result = self.safety_manager.save_checkpoint_state(
                    root,
                    status="running",
                    stash_ref=stash_ref,
                    processed_targets=list(processed_targets),
                )
                if checkpoint_result.is_failure:
                    u.Infra.refactor_error(
                        checkpoint_result.error or "checkpoint save failed",
                    )
        if apply_safety and (not dry_run):
            self._run_safety_validation_and_finalize(
                target_path=root,
                stash_ref=stash_ref,
                results=results,
            )
        return results

    def _run_safety_validation_and_finalize(
        self,
        *,
        target_path: Path,
        stash_ref: str,
        results: MutableSequence[m.Infra.Result],
    ) -> None:
        validation_result = self.safety_manager.run_semantic_validation(target_path)
        if validation_result.is_failure:
            error_msg = validation_result.error or "semantic validation failed"
            self.safety_manager.request_emergency_stop(error_msg)
            u.Infra.refactor_error(error_msg)
            rollback_result = self.safety_manager.rollback(target_path, stash_ref)
            if rollback_result.is_failure:
                u.Infra.refactor_error(
                    rollback_result.error or "rollback failed",
                )
            results.append(
                m.Infra.Result(
                    file_path=target_path,
                    success=False,
                    modified=False,
                    error=error_msg,
                    changes=[],
                    refactored_code=None,
                ),
            )
            return

        clear_result = self.safety_manager.clear_checkpoint()
        if clear_result.is_failure:
            u.Infra.refactor_error(
                clear_result.error or "checkpoint clear failed",
            )

    def _prepare_safety_stash(self, target_path: Path) -> r[str]:
        stash_result = self.safety_manager.create_pre_transformation_stash(target_path)
        if stash_result.is_failure:
            error_msg = stash_result.error or "pre-transformation stash failed"
            u.Infra.refactor_error(error_msg)
            return r[str].fail(error_msg)
        return r[str].ok(stash_result.value)

    def set_rule_filters(self, filters: t.StrSequence) -> None:
        """Set active rule filters using normalized lowercase rule ids."""
        self.rule_filters = [item.lower() for item in filters]

    def _build_file_rules(self) -> Sequence[FlextInfraClassNestingRefactorRule]:
        return [FlextInfraClassNestingRefactorRule()]

    def _build_rule(
        self,
        rule_def: Mapping[str, t.Infra.InfraValue],
    ) -> FlextInfraRefactorRule | None:
        rule_id = str(rule_def.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN))
        fix_action = (
            str(
                rule_def.get(
                    c.Infra.ReportKeys.FIX_ACTION,
                    rule_def.get(c.Infra.ReportKeys.ACTION, ""),
                ),
            )
            .strip()
            .lower()
        )
        check = str(rule_def.get(c.Infra.Verbs.CHECK, "")).strip().lower()
        if fix_action in c.Infra.FUTURE_FIX_ACTIONS or check in c.Infra.FUTURE_CHECKS:
            return FlextInfraRefactorEnsureFutureAnnotationsRule(rule_def)
        if fix_action in c.Infra.LEGACY_FIX_ACTIONS:
            return FlextInfraRefactorLegacyRemovalRule(rule_def)
        if fix_action in c.Infra.IMPORT_FIX_ACTIONS:
            return FlextInfraRefactorImportModernizerRule(rule_def)
        if fix_action in c.Infra.CLASS_FIX_ACTIONS:
            return FlextInfraRefactorClassReconstructorRule(rule_def)
        if fix_action in c.Infra.MRO_FIX_ACTIONS:
            if fix_action == "migrate_to_class_mro":
                return FlextInfraRefactorMROClassMigrationRule(rule_def)
            return FlextInfraRefactorMRORedundancyChecker(rule_def)
        if fix_action in c.Infra.PROPAGATION_FIX_ACTIONS:
            if fix_action == "propagate_signature_migrations":
                return FlextInfraRefactorSignaturePropagationRule(rule_def)
            return FlextInfraRefactorSymbolPropagationRule(rule_def)
        if fix_action in c.Infra.PATTERN_FIX_ACTIONS:
            return FlextInfraRefactorPatternCorrectionsRule(rule_def)
        if fix_action in c.Infra.TYPE_ALIAS_FIX_ACTIONS:
            return FlextInfraRefactorTypingUnificationRule(rule_def)
        if fix_action in c.Infra.TYPING_FIX_ACTIONS:
            return FlextInfraRefactorTypingAnnotationFixRule(rule_def)
        if fix_action in c.Infra.TIER0_FIX_ACTIONS:
            return FlextInfraRefactorTier0ImportFixRule(rule_def)
        rule_id_lower = rule_id.lower()
        if "ensure-future" in rule_id_lower or "future-annotations" in rule_id_lower:
            return FlextInfraRefactorEnsureFutureAnnotationsRule(rule_def)
        if any(
            key in rule_id_lower
            for key in ["legacy", "alias", "deprecated", "wrapper", "bypass"]
        ):
            return FlextInfraRefactorLegacyRemovalRule(rule_def)
        if any(key in rule_id_lower for key in ["import", "modernize"]):
            return FlextInfraRefactorImportModernizerRule(rule_def)
        if any(key in rule_id_lower for key in ["class", "reorder", "method"]):
            return FlextInfraRefactorClassReconstructorRule(rule_def)
        if "mro" in rule_id_lower:
            if "migrate-to-class-mro" in rule_id_lower:
                return FlextInfraRefactorMROClassMigrationRule(rule_def)
            return FlextInfraRefactorMRORedundancyChecker(rule_def)
        if any(
            key in rule_id_lower for key in ["propagate", "symbol-rename", "rename"]
        ):
            if "signature" in rule_id_lower:
                return FlextInfraRefactorSignaturePropagationRule(rule_def)
            return FlextInfraRefactorSymbolPropagationRule(rule_def)
        if any(
            key in rule_id_lower
            for key in ["redundant-cast", "dict-to-mapping", "container-invariance"]
        ):
            return FlextInfraRefactorPatternCorrectionsRule(rule_def)
        return None

    def _default_config_path(self) -> Path:
        return Path(__file__).parent / "config.yml"


__all__ = ["FlextInfraRefactorEngine"]
