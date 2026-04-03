"""Orchestration mixin — project/workspace refactoring and safety.

Provides ``refactor_project``, ``refactor_workspace``, file collection,
violation analysis, and safety stash/rollback coordination.
"""

from __future__ import annotations

import argparse
from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorRuleLoader,
    FlextInfraRefactorSafetyManager,
    FlextInfraRefactorViolationAnalyzer,
    c,
    m,
    t,
    u,
)


class FlextInfraRefactorEngineOrchestrationMixin:
    """Mixin providing project/workspace orchestration and safety."""

    config: t.Infra.InfraValue
    rule_loader: FlextInfraRefactorRuleLoader
    safety_manager: FlextInfraRefactorSafetyManager

    # -- Provided by FlextInfraRefactorEnginePipelineMixin --

    @staticmethod
    def _error_result(fp: Path, error: str) -> m.Infra.Result: ...

    def refactor_file(
        self, file_path: Path, *, dry_run: bool = False
    ) -> m.Infra.Result: ...

    def refactor_files(
        self, file_paths: Sequence[Path], *, dry_run: bool = False
    ) -> Sequence[m.Infra.Result]: ...

    # ── Violation analysis ────────────────────────────────────────

    def _run_analyze_violations(self, args: argparse.Namespace) -> int:
        files = self._collect_files(args)
        if files is None:
            return 1
        analysis = FlextInfraRefactorViolationAnalyzer.analyze_files(files)
        u.print_violation_summary(analysis)
        if args.analysis_output is not None:
            _ = u.write_json(
                args.analysis_output,
                analysis.model_dump(mode="json"),
                ensure_ascii=True,
            )
            u.refactor_info(f"Analysis report written: {args.analysis_output}")
        return 0

    # ── File collection ──────────────────────────────────────────

    def _collect_files(self, args: argparse.Namespace) -> MutableSequence[Path] | None:
        if args.project:
            return u.collect_engine_project_files(
                self.rule_loader, self.config, args.project, pattern=args.pattern
            )
        if args.workspace:
            return list(
                u.collect_engine_workspace_files(
                    self.rule_loader,
                    self.config,
                    args.workspace,
                    pattern=args.pattern,
                )
            )
        if args.file:
            if not args.file.exists():
                u.refactor_error(f"File not found: {args.file}")
                return None
            return [args.file]
        if args.files:
            return [p for p in args.files if p.exists()]
        return []

    # ── Refactoring dispatch ─────────────────────────────────────

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
                u.refactor_error(f"File not found: {args.file}")
                return 1
            original = args.file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            result = self.refactor_file(args.file, dry_run=args.dry_run)
            if args.show_diff and result.modified:
                u.print_diff(original, result.refactored_code or original, args.file)
            results = [result]
        elif args.files:
            existing = [p for p in args.files if p.exists()]
            for p in args.files:
                if not p.exists():
                    u.refactor_error(f"File not found: {p}")
            results = list(self.refactor_files(existing, dry_run=args.dry_run))
        else:
            results = list[m.Infra.Result]()
        u.print_summary(results, dry_run=args.dry_run)
        if args.impact_map_output is not None:
            _ = u.write_impact_map(results, args.impact_map_output)
        return 0 if u.count(results, lambda item: not item.success) == 0 else 1

    # ── Safety ───────────────────────────────────────────────────

    def _try_safety_stash(
        self, target: Path, *, apply_safety: bool, dry_run: bool
    ) -> t.Infra.Pair[str, Sequence[m.Infra.Result] | None]:
        if not apply_safety or dry_run:
            return "", None
        stash = self.safety_manager.create_pre_transformation_stash(target)
        if stash.is_failure:
            msg = stash.error or "pre-transformation stash failed"
            u.refactor_error(msg)
            return "", [self._error_result(target, msg)]
        return stash.value, None

    def _finalize_safety(
        self,
        *,
        target: Path,
        stash_ref: str,
        results: MutableSequence[m.Infra.Result],
    ) -> None:
        val = self.safety_manager.run_semantic_validation(target)
        if val.is_failure:
            msg = val.error or "semantic validation failed"
            self.safety_manager.request_emergency_stop(msg)
            u.refactor_error(msg)
            rb = self.safety_manager.rollback(target, stash_ref)
            if rb.is_failure:
                u.refactor_error(rb.error or "rollback failed")
            results.append(self._error_result(target, msg))
            return
        cl = self.safety_manager.clear_checkpoint()
        if cl.is_failure:
            u.refactor_error(cl.error or "checkpoint clear failed")

    # ── Project refactoring ──────────────────────────────────────

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
        collected = u.collect_engine_project_files(
            self.rule_loader, self.config, project_path, pattern=pattern
        )
        if collected is None:
            return [
                self._error_result(
                    project_path,
                    f"File iteration failed for {project_path}",
                )
            ]
        u.refactor_info(f"Found {len(collected)} files to process")
        results: MutableSequence[m.Infra.Result] = list(
            u.run_rope_pre_hooks(project_path, dry_run=dry_run)
        )
        results.extend(self.refactor_files(collected, dry_run=dry_run))
        results.extend(u.run_rope_post_hooks(project_path, dry_run=dry_run))
        if apply_safety and not dry_run:
            cp = self.safety_manager.save_checkpoint_state(
                project_path,
                status="transformed",
                stash_ref=stash_ref,
                processed_targets=[str(f) for f in collected],
            )
            if cp.is_failure:
                u.refactor_error(cp.error or "checkpoint save failed")
            self._finalize_safety(
                target=project_path, stash_ref=stash_ref, results=results
            )
        return results

    # ── Workspace refactoring ────────────────────────────────────

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
            u.refactor_error(f"Invalid workspace root: {workspace_root}")
            return []
        scan_dirs = frozenset(self.rule_loader.extract_project_scan_dirs(self.config))
        projects = u.discover_project_roots(
            workspace_root=root, scan_dirs=scan_dirs or None
        )
        if not projects:
            u.refactor_error(f"No projects discovered under: {workspace_root}")
            return []
        u.refactor_info(f"Discovered {len(projects)} projects in workspace")
        stash_ref, err = self._try_safety_stash(
            root, apply_safety=apply_safety, dry_run=dry_run
        )
        if err is not None:
            return err
        results: MutableSequence[m.Infra.Result] = []
        processed: MutableSequence[str] = []
        results.extend(u.run_rope_pre_hooks(root, dry_run=dry_run))
        for proj in projects:
            if apply_safety and self.safety_manager.is_emergency_stop_requested():
                break
            u.refactor_header(f"Project: {proj}")
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
                cp = self.safety_manager.save_checkpoint_state(
                    root,
                    status="running",
                    stash_ref=stash_ref,
                    processed_targets=list(processed),
                )
                if cp.is_failure:
                    u.refactor_error(cp.error or "checkpoint save failed")
        results.extend(u.run_rope_post_hooks(root, dry_run=dry_run))
        if apply_safety and not dry_run:
            self._finalize_safety(target=root, stash_ref=stash_ref, results=results)
        return results


__all__ = [
    "FlextInfraRefactorEngineOrchestrationMixin",
]
