"""Refactor orchestration layer for file/project/workspace execution."""

from __future__ import annotations

import difflib
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorViolationAnalyzer,
    c,
    m,
    t,
    u,
)

from .engine_file import (
    FlextInfraClassNestingPostCheckGate,
    FlextInfraRefactorFileExecutor,
)
from .engine_text import FlextInfraRefactorTextExecutor
from .loader import FlextInfraRefactorRuleLoader

_log = u.fetch_logger(__name__)


class FlextInfraRefactorOrchestrator(
    FlextInfraRefactorTextExecutor,
    FlextInfraRefactorFileExecutor,
):
    """Coordinate refactor execution using loaded rule selections and safety flow."""

    def __init__(
        self,
        loader: FlextInfraRefactorRuleLoader,
        *,
        safety_manager: FlextInfraRefactorSafetyManager | None = None,
    ) -> None:
        """Initialize the orchestrator with a loader and optional safety service."""
        self.loader = loader
        self.safety_manager = safety_manager or FlextInfraRefactorSafetyManager()
        self._class_nesting_config: t.Infra.ContainerDict | None = None
        self._class_nesting_policy_by_family: (
            Mapping[str, m.Infra.ClassNestingPolicy] | None
        ) = None
        self._class_nesting_gate: FlextInfraClassNestingPostCheckGate | None = None

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

    @staticmethod
    def _refactor_debug(message: str) -> None:
        """Emit one compact refactor debug line."""
        u.Cli.info(message)

    @staticmethod
    def _refactor_header(message: str) -> None:
        """Emit one refactor section header."""
        u.Cli.header(message)

    @staticmethod
    def _print_violation_summary(analysis: m.Infra.ViolationAnalysisReport) -> None:
        """Print high-level violation analysis summary."""
        u.Cli.header("Violation Analysis")
        u.Cli.info(f"Files scanned: {analysis.files_scanned}")
        for key, value in sorted(analysis.totals.items()):
            u.Cli.info(f"- {key}: {value}")

    @staticmethod
    def _print_diff(original: str, updated: str, file_path: Path) -> None:
        """Print unified diff for one updated file."""
        diff = difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="",
        )
        for line in diff:
            u.Cli.info(line)

    @staticmethod
    def _print_summary(results: Sequence[m.Infra.Result], *, dry_run: bool) -> None:
        """Print refactor execution summary."""
        total = len(results)
        success = sum(1 for item in results if item.success)
        failed = total - success
        modified = sum(1 for item in results if item.modified)
        mode = "[DRY-RUN] " if dry_run else ""
        u.Cli.info(f"{mode}Processed: {total} file(s)")
        u.Cli.info(f"Success: {success}  Failed: {failed}  Modified: {modified}")

    def refactor_file(
        self,
        file_path: Path,
        *,
        dry_run: bool = False,
    ) -> m.Infra.Result:
        """Refactor one file using the loader's current rule selections."""
        result: m.Infra.Result
        try:
            if file_path.suffix != c.Infra.EXT_PYTHON:
                result = self._skip_result(file_path)
            else:
                workspace_root = u.Infra.project_root(file_path) or file_path.parent
                original = file_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
                current, all_changes = original, list[str]()
                error_result: m.Infra.Result | None = None
                if self.loader.file_rules:
                    with u.Infra.open_project(workspace_root) as rope_project:
                        resource = u.Infra.get_resource_from_path(
                            rope_project,
                            file_path,
                        )
                        if resource is None:
                            error_result = self._error_result(
                                file_path,
                                f"Could not resolve rope resource for {file_path}",
                            )
                        else:
                            for kind, settings in self.loader.file_rules:
                                file_rule_result = self._apply_file_rule_selection(
                                    kind,
                                    settings,
                                    rope_project,
                                    resource,
                                    dry_run=True,
                                )
                                if not file_rule_result.success:
                                    error_result = m.Infra.Result(
                                        file_path=file_path,
                                        success=False,
                                        modified=False,
                                        error=file_rule_result.error,
                                        changes=file_rule_result.changes,
                                        refactored_code=None,
                                    )
                                    break
                                if (
                                    file_rule_result.modified
                                    and file_rule_result.refactored_code
                                ):
                                    current = file_rule_result.refactored_code
                                all_changes.extend(file_rule_result.changes)
                if error_result is None:
                    for kind, settings in self.loader.rules:
                        if not bool(settings.get(c.Infra.RK_ENABLED, True)):
                            continue
                        current, changes = self._apply_text_rule_selection(
                            kind,
                            settings,
                            current,
                            file_path,
                        )
                        all_changes.extend(changes)
                    modified = current != original
                    if not dry_run and modified:
                        ok, report = u.Infra.protected_source_write(
                            file_path,
                            workspace=workspace_root,
                            updated_source=current,
                            keep_backup=True,
                        )
                        all_changes.extend(report)
                        if not ok:
                            error_result = m.Infra.Result(
                                file_path=file_path,
                                success=False,
                                modified=False,
                                error="Protected refactor validation failed",
                                changes=all_changes,
                                refactored_code=original,
                            )
                    result = error_result or m.Infra.Result(
                        file_path=file_path,
                        success=True,
                        modified=modified,
                        changes=all_changes,
                        refactored_code=current,
                    )
                else:
                    result = error_result
        except Exception as exc:
            result = self._error_result(file_path, str(exc))
        return result

    def refactor_files(
        self,
        file_paths: Sequence[Path],
        *,
        dry_run: bool = False,
    ) -> Sequence[m.Infra.Result]:
        """Refactor many files and collect individual results."""
        results: MutableSequence[m.Infra.Result] = []
        for file_path in file_paths:
            result = self.refactor_file(file_path, dry_run=dry_run)
            results.append(result)
            if result.success and result.modified:
                u.Cli.info(
                    f"{'[DRY-RUN] ' if dry_run else ''}Modified: {file_path.name}"
                )
                for change in result.changes:
                    u.Cli.info(f"  - {change}")
            elif result.success:
                _log.debug(
                    "refactor_noop",
                    file=str(result.file_path),
                )
                self._refactor_debug(f"Unchanged: {file_path.name}")
            else:
                u.Cli.error(f"Failed: {file_path.name} - {result.error}")
        return results

    def run_analyze_violations(self, args: t.Infra.CliNamespace) -> int:
        """Analyze violations across the selected file set."""
        files = self._collect_files(args)
        if files is None:
            return 1
        analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(files)
        self._print_violation_summary(analysis)
        if args.analysis_output is not None:
            _ = u.Cli.json_write(
                args.analysis_output,
                analysis.model_dump(mode="json"),
            )
            u.Cli.info(f"Analysis report written: {args.analysis_output}")
        return 0

    def _collect_files(
        self, args: t.Infra.CliNamespace
    ) -> MutableSequence[Path] | None:
        if args.project:
            collected = u.Infra.collect_engine_project_files(
                self.loader.settings,
                args.project,
                pattern=args.pattern,
            )
            return None if collected is None else list(collected)
        if args.workspace:
            return list(
                u.Infra.collect_engine_workspace_files(
                    self.loader.settings,
                    args.workspace,
                    pattern=args.pattern,
                )
            )
        if args.file:
            if not args.file.exists():
                u.Cli.error(f"File not found: {args.file}")
                return None
            return [args.file]
        if args.files:
            return [path for path in args.files if path.exists()]
        return []

    def run_refactor(self, args: t.Infra.CliNamespace) -> int:
        """Run refactor CLI dispatch for the selected scope."""
        if args.project:
            results = list(
                self.refactor_project(
                    args.project,
                    dry_run=args.dry_run,
                    pattern=args.pattern,
                )
            )
        elif args.workspace:
            results = list(
                self.refactor_workspace(
                    args.workspace,
                    dry_run=args.dry_run,
                    pattern=args.pattern,
                )
            )
        elif args.file:
            if not args.file.exists():
                u.Cli.error(f"File not found: {args.file}")
                return 1
            original = args.file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            result = self.refactor_file(args.file, dry_run=args.dry_run)
            if args.show_diff and result.modified:
                self._print_diff(
                    original,
                    result.refactored_code or original,
                    args.file,
                )
            results = [result]
        elif args.files:
            existing = [path for path in args.files if path.exists()]
            for path in args.files:
                if not path.exists():
                    u.Cli.error(f"File not found: {path}")
            results = list(self.refactor_files(existing, dry_run=args.dry_run))
        else:
            results = list[m.Infra.Result]()
        self._print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = u.Infra.write_impact_map(
                results,
                args.impact_map_output,
            )
        return 0 if u.count(results, lambda item: not item.success) == 0 else 1

    def _try_safety_stash(
        self,
        target: Path,
        *,
        apply_safety: bool,
        dry_run: bool,
    ) -> t.Pair[str, Sequence[m.Infra.Result] | None]:
        if not apply_safety or dry_run:
            return "", None
        stash = self.safety_manager.create_pre_transformation_stash(target)
        if stash.failure:
            msg = stash.error or "pre-transformation stash failed"
            u.Cli.error(msg)
            return "", [self._error_result(target, msg)]
        return stash.value, None

    def _finalize_safety(
        self,
        *,
        target: Path,
        stash_ref: str,
        processed_targets: t.StrSequence,
        results: MutableSequence[m.Infra.Result],
    ) -> None:
        checkpoint = self.safety_manager.save_checkpoint_state(
            target,
            status="post-transform",
            stash_ref=stash_ref,
            processed_targets=processed_targets,
        )
        if checkpoint.failure:
            msg = checkpoint.error or "checkpoint save failed"
            self.safety_manager.request_emergency_stop(msg)
            u.Cli.error(msg)
            rollback = self.safety_manager.rollback(target, stash_ref)
            if rollback.failure:
                u.Cli.error(rollback.error or "rollback failed")
            results.append(self._error_result(target, msg))
            return
        validation = self.safety_manager.run_semantic_validation(target)
        if validation.failure:
            msg = validation.error or "semantic validation failed"
            self.safety_manager.request_emergency_stop(msg)
            u.Cli.error(msg)
            rollback = self.safety_manager.rollback(target, stash_ref)
            if rollback.failure:
                u.Cli.error(rollback.error or "rollback failed")
            results.append(self._error_result(target, msg))
            return
        cleared = self.safety_manager.clear_checkpoint(
            keep=[
                result.file_path
                for result in results
                if result.success and result.modified
            ],
        )
        if cleared.failure:
            u.Cli.error(cleared.error or "checkpoint clear failed")

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor files under configured project directories."""
        stash_ref, error_results = self._try_safety_stash(
            project_path,
            apply_safety=apply_safety,
            dry_run=dry_run,
        )
        if error_results is not None:
            results_out: Sequence[m.Infra.Result] = error_results
            return results_out
        collected = u.Infra.collect_engine_project_files(
            self.loader.settings,
            project_path,
            pattern=pattern,
        )
        if collected is None:
            return [
                self._error_result(
                    project_path,
                    f"File iteration failed for {project_path}",
                )
            ]
        u.Cli.info(f"Found {len(collected)} files to process")
        results: MutableSequence[m.Infra.Result] = []
        results.extend(self.refactor_files(collected, dry_run=dry_run))
        results.extend(u.Infra.run_rope_post_hooks(project_path, dry_run=dry_run))
        if apply_safety and not dry_run:
            self._finalize_safety(
                target=project_path,
                stash_ref=stash_ref,
                processed_targets=[str(project_path)],
                results=results,
            )
        return results

    def refactor_workspace(
        self,
        workspace_root: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
        apply_safety: bool = True,
    ) -> Sequence[m.Infra.Result]:
        """Refactor all discoverable workspace projects."""
        root = workspace_root.resolve()
        if not root.exists() or not root.is_dir():
            u.Cli.error(f"Invalid workspace root: {workspace_root}")
            return []
        projects = u.Infra.discover_engine_projects(
            self.loader.settings,
            root,
        )
        if not projects:
            u.Cli.error(f"No projects discovered under: {workspace_root}")
            return []
        u.Cli.info(f"Discovered {len(projects)} projects in workspace")
        stash_ref, error_results = self._try_safety_stash(
            root,
            apply_safety=apply_safety,
            dry_run=dry_run,
        )
        if error_results is not None:
            results_out: Sequence[m.Infra.Result] = error_results
            return results_out
        results: MutableSequence[m.Infra.Result] = []
        processed: MutableSequence[str] = []
        for project in projects:
            if apply_safety and self.safety_manager.emergency_stop_requested:
                break
            self._refactor_header(f"Project: {project}")
            results.extend(
                self.refactor_project(
                    project,
                    dry_run=dry_run,
                    pattern=pattern,
                    apply_safety=False,
                )
            )
            if apply_safety and not dry_run:
                processed.append(str(project))
        results.extend(u.Infra.run_rope_post_hooks(root, dry_run=dry_run))
        if apply_safety and not dry_run:
            self._finalize_safety(
                target=root,
                stash_ref=stash_ref,
                processed_targets=processed,
                results=results,
            )
        return results


__all__: list[str] = ["FlextInfraRefactorOrchestrator"]
