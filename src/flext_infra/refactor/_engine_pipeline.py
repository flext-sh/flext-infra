"""Refactor pipeline mixin — file-level refactoring execution.

Provides ``refactor_file`` and ``refactor_files`` methods plus result
helpers used by the orchestration layer.
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraClassNestingRefactorRule,
    FlextInfraRefactorRule,
    c,
    m,
    u,
)


class FlextInfraRefactorEnginePipelineMixin:
    """Mixin providing file-level refactoring pipeline methods."""

    rules: MutableSequence[FlextInfraRefactorRule]
    file_rules: MutableSequence[FlextInfraClassNestingRefactorRule]

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

    # ── Single-file pipeline ─────────────────────────────────────

    def refactor_file(
        self, file_path: Path, *, dry_run: bool = False
    ) -> m.Infra.Result:
        """Refactor one file with currently loaded rules."""
        try:
            if file_path.suffix != c.Infra.Extensions.PYTHON:
                return self._skip_result(file_path)
            original = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            current, all_changes = original, list[str]()
            if self.file_rules:
                workspace_root = (
                    u.discover_project_root_from_file(file_path) or file_path.parent
                )
                rope_project = u.init_rope_project(workspace_root)
                try:
                    resource = u.get_resource_from_path(rope_project, file_path)
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

    # ── Multi-file pipeline ──────────────────────────────────────

    def refactor_files(
        self, file_paths: Sequence[Path], *, dry_run: bool = False
    ) -> Sequence[m.Infra.Result]:
        """Refactor many files and collect individual results."""
        results: MutableSequence[m.Infra.Result] = []
        for fp in file_paths:
            result = self.refactor_file(fp, dry_run=dry_run)
            results.append(result)
            if result.success and result.modified:
                u.refactor_info(f"{'[DRY-RUN] ' if dry_run else ''}Modified: {fp.name}")
                for ch in result.changes:
                    u.refactor_info(f"  - {ch}")
            elif result.success:
                u.refactor_debug(f"Unchanged: {fp.name}")
            else:
                u.refactor_error(f"Failed: {fp.name} - {result.error}")
        return results


__all__ = [
    "FlextInfraRefactorEnginePipelineMixin",
]
