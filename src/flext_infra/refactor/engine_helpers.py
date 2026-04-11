"""Engine helper mixins — pipeline execution and orchestration.

Provides file-level refactoring pipeline (``refactor_file``, ``refactor_files``)
and project/workspace orchestration with safety stash/rollback coordination.
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_core import FlextLogger
from flext_infra import (
    FlextInfraClassNestingRefactorRule,
    FlextInfraRefactorRule,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorViolationAnalyzer,
    FlextInfraUtilitiesProtectedEdit,
    FlextInfraUtilitiesRefactorRuleLoader,
    c,
    m,
    t,
    u,
)

_log = FlextLogger.create_module_logger(__name__)


class FlextInfraRefactorEngineHelpersMixin:
    """Mixin providing file-level pipeline and project/workspace orchestration."""

    config: t.Infra.InfraValue
    rules: MutableSequence[FlextInfraRefactorRule]
    file_rules: MutableSequence[FlextInfraClassNestingRefactorRule]
    rule_loader: FlextInfraUtilitiesRefactorRuleLoader
    safety_manager: FlextInfraRefactorSafetyManager

    # ── Result helpers ─────────────────────────────────────────────

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

    # ── Single-file pipeline ──────────────────────────────────────

    def refactor_file(
        self, file_path: Path, *, dry_run: bool = False
    ) -> m.Infra.Result:
        """Refactor one file with currently loaded rules."""
        try:
            if file_path.suffix != c.Infra.EXT_PYTHON:
                return self._skip_result(file_path)
            workspace_root = (
                u.Infra.discover_project_root_from_file(file_path) or file_path.parent
            )
            original = file_path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            current, all_changes = original, list[str]()
            if self.file_rules:
                rope_project = u.Infra.init_rope_project(workspace_root)
                try:
                    resource = u.Infra.get_resource_from_path(rope_project, file_path)
                    if resource is None:
                        return self._error_result(
                            file_path,
                            f"Could not resolve rope resource for {file_path}",
                        )
                    for fr in self.file_rules:
                        res = fr.apply(rope_project, resource, dry_run=True)
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
                finally:
                    rope_project.close()
            for rule in self.rules:
                if rule.enabled:
                    current, changes = rule.apply(current, file_path)
                    all_changes.extend(changes)
            modified = current != original
            if not dry_run and modified:
                ok, report = FlextInfraUtilitiesProtectedEdit.protected_source_write(
                    file_path,
                    workspace=workspace_root,
                    updated_source=current,
                    keep_backup=True,
                )
                all_changes.extend(report)
                if not ok:
                    return m.Infra.Result(
                        file_path=file_path,
                        success=False,
                        modified=False,
                        error="Protected refactor validation failed",
                        changes=all_changes,
                        refactored_code=original,
                    )
            return m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=modified,
                changes=all_changes,
                refactored_code=current,
            )
        except Exception as exc:
            return self._error_result(file_path, str(exc))

    # ── Multi-file pipeline ───────────────────────────────────────

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
                _log.debug(
                    "refactor_noop",
                    file=str(result.file_path),
                )
                u.Infra.refactor_debug(f"Unchanged: {fp.name}")
            else:
                u.Infra.refactor_error(f"Failed: {fp.name} - {result.error}")
        return results

    # ── Violation analysis ─────────────────────────────────────────

    def _run_analyze_violations(self, args: t.Infra.CliNamespace) -> int:
        files = self._collect_files(args)
        if files is None:
            return 1
        analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(files)
        u.Infra.print_violation_summary(analysis)
        if args.analysis_output is not None:
            _ = u.Cli.json_write(
                args.analysis_output,
                analysis.model_dump(mode="json"),
            )
            u.Infra.refactor_info(f"Analysis report written: {args.analysis_output}")
        return 0

    # ── File collection ────────────────────────────────────────────

    def _collect_files(
        self, args: t.Infra.CliNamespace
    ) -> MutableSequence[Path] | None:
        if args.project:
            return u.Infra.collect_engine_project_files(
                self.rule_loader, self.config, args.project, pattern=args.pattern
            )
        if args.workspace:
            return list(
                u.Infra.collect_engine_workspace_files(
                    self.rule_loader,
                    self.config,
                    args.workspace,
                    pattern=args.pattern,
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

    # ── Refactoring dispatch ───────────────────────────────────────

    def _run_refactor(self, args: t.Infra.CliNamespace) -> int:
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
            original = args.file.read_text(encoding=c.Infra.ENCODING_DEFAULT)
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
            results = list[m.Infra.Result]()
        u.Infra.print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = u.Infra.write_impact_map(results, args.impact_map_output)
        return 0 if u.count(results, lambda item: not item.success) == 0 else 1

    # ── Safety ─────────────────────────────────────────────────────

    def _try_safety_stash(
        self, target: Path, *, apply_safety: bool, dry_run: bool
    ) -> t.Infra.Pair[str, Sequence[m.Infra.Result] | None]:
        if not apply_safety or dry_run:
            return "", None
        stash = self.safety_manager.create_pre_transformation_stash(target)
        if stash.failure:
            msg = stash.error or "pre-transformation stash failed"
            u.Infra.refactor_error(msg)
            return "", [self._error_result(target, msg)]
        return stash.value, None

    def _finalize_safety(
        self,
        *,
        target: Path,
        stash_ref: str,
        processed_targets: Sequence[str],
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
            u.Infra.refactor_error(msg)
            rb = self.safety_manager.rollback(target, stash_ref)
            if rb.failure:
                u.Infra.refactor_error(rb.error or "rollback failed")
            results.append(self._error_result(target, msg))
            return
        val = self.safety_manager.run_semantic_validation(target)
        if val.failure:
            msg = val.error or "semantic validation failed"
            self.safety_manager.request_emergency_stop(msg)
            u.Infra.refactor_error(msg)
            rb = self.safety_manager.rollback(target, stash_ref)
            if rb.failure:
                u.Infra.refactor_error(rb.error or "rollback failed")
            results.append(self._error_result(target, msg))
            return
        cl = self.safety_manager.clear_checkpoint(
            keep=[
                result.file_path
                for result in results
                if result.success and result.modified
            ],
        )
        if cl.failure:
            u.Infra.refactor_error(cl.error or "checkpoint clear failed")

    # ── Project refactoring ────────────────────────────────────────

    def refactor_project(
        self,
        project_path: Path,
        *,
        dry_run: bool = False,
        pattern: str = c.Infra.EXT_PYTHON_GLOB,
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
                    project_path,
                    f"File iteration failed for {project_path}",
                )
            ]
        u.Infra.refactor_info(f"Found {len(collected)} files to process")
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

    # ── Workspace refactoring ──────────────────────────────────────

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
        for proj in projects:
            if apply_safety and self.safety_manager.is_emergency_stop_requested():
                break
            u.Infra.refactor_header(f"Project: {proj}")
            results.extend(
                self.refactor_project(
                    proj,
                    dry_run=dry_run,
                    pattern=pattern,
                    apply_safety=False,
                )
            )
            if apply_safety and not dry_run:
                processed.append(str(proj))
        results.extend(u.Infra.run_rope_post_hooks(root, dry_run=dry_run))
        if apply_safety and not dry_run:
            self._finalize_safety(
                target=root,
                stash_ref=stash_ref,
                processed_targets=processed,
                results=results,
            )
        return results


__all__ = [
    "FlextInfraRefactorEngineHelpersMixin",
]
