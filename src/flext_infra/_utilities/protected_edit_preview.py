"""Staged previews and validation reports for protected edit workflows.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, t
from flext_infra._utilities.protected_edit_linting import (
    FlextInfraUtilitiesProtectedEditLinting,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesProtectedEditPreview(FlextInfraUtilitiesProtectedEditLinting):
    """Validate staged source candidates without modifying live destinations."""

    @staticmethod
    def _normalized_source_updates(
        updates: t.MappingKV[Path, str],
    ) -> MutableMapping[Path, str]:
        """Return one update map keyed by resolved path in deterministic order.

        Returns:
            One update map keyed by resolved path in deterministic order.

        """
        return {
            path.resolve(): content
            for path, content in sorted(updates.items(), key=operator.itemgetter(0))
        }

    @staticmethod
    def _preview_write_baselines(
        updates: t.MappingKV[Path, str],
        workspace: Path,
        gates: t.StrSequence | None = None,
    ) -> t.Pair[
        MutableMapping[Path, str | None],
        MutableMapping[Path, t.Infra.LintSnapshot],
    ]:
        """Preview write baselines.

        Returns:
            The resulting ``t.Pair[MutableMapping[Path, str | None],
                MutableMapping[Path, t.Infra.LintSnapshot]]``.

        """
        before_sources: MutableMapping[Path, str | None] = {}
        before_lints: MutableMapping[Path, t.Infra.LintSnapshot] = {}
        existing_paths: list[Path] = []
        for path in updates:
            if path.exists():
                before_sources[path] = path.read_text(encoding=c.DEFAULT_ENCODING)
                existing_paths.append(path)
                continue
            before_sources[path] = None
        if existing_paths:
            before_lints.update(
                FlextInfraUtilitiesProtectedEditPreview.lint_snapshots(
                    tuple(existing_paths),
                    workspace,
                    gates=gates,
                ),
            )
        for path in updates:
            if before_sources[path] is not None:
                continue
            before_lints[path] = {}
        return before_sources, before_lints

    @staticmethod
    def _validation_failure_report_lines(
        path: Path,
        workspace: Path,
        before_source: str,
        new_errors: t.Infra.LintSnapshot,
        pytest_failure: str | None = None,
    ) -> list[str]:
        """Describe the actual source delta and its validation failures.

        Returns:
            The resulting ``list[str]``.

        """
        rel = FlextInfraUtilitiesProtectedEditPreview._relative_path(path, workspace)
        modified = path.read_text(encoding=c.DEFAULT_ENCODING)
        diff = FlextInfraUtilitiesProtectedEditPreview.unified_diff_lines(
            before_source,
            modified,
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
            max_lines=c.Infra.EDIT_DIFF_PREVIEW_MAX_LINES,
        )
        report_lines = [f"  VALIDATION FAILED {rel}:"]
        report_lines.extend(f"    {line.rstrip()}" for line in diff)
        for tool, messages in new_errors.items():
            report_lines.extend((
                f"    NEW {tool} errors:",
                *(f"      {message}" for message in messages),
            ))
        if pytest_failure:
            report_lines.append(f"    pytest failure: {pytest_failure}")
        return report_lines

    @staticmethod
    def _preview_write_reports(
        candidates: t.MappingKV[Path, Path],
        before_sources: t.MappingKV[Path, str | None],
        before_lints: t.MappingKV[Path, t.Infra.LintSnapshot],
        workspace: Path,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.EditResult:
        """Preview write reports.

        Returns:
            The resulting ``t.Infra.EditResult``.

        """
        reports: list[str] = []
        failed = False
        after_lints = FlextInfraUtilitiesProtectedEditPreview.lint_snapshots(
            tuple(candidates.values()),
            workspace,
            gates=gates,
        )
        for path, candidate in candidates.items():
            new_errors = FlextInfraUtilitiesProtectedEditPreview.lint_new_errors(
                before_lints[path],
                after_lints[candidate],
            )
            if not new_errors:
                continue
            failed = True
            reports.extend(
                FlextInfraUtilitiesProtectedEditPreview._validation_failure_report_lines(
                    candidate,
                    workspace,
                    before_sources[path] or "",
                    new_errors,
                ),
            )
        return (not failed, reports)

    @staticmethod
    def preview_source_writes(
        updates: t.MappingKV[Path, str],
        *,
        workspace: Path,
        source_preview: p.Infra.SourcePreview,
        gates: t.StrSequence | None = None,
    ) -> t.Infra.EditResult:
        """Validate a journal-owned source view without writing live destinations.

        Returns:
            The resulting ``t.Infra.EditResult``.

        """
        if not updates:
            return (True, [])

        normalized_updates = (
            FlextInfraUtilitiesProtectedEditPreview._normalized_source_updates(updates)
        )
        before_sources, before_lints = (
            FlextInfraUtilitiesProtectedEditPreview._preview_write_baselines(
                normalized_updates,
                workspace,
                gates=gates,
            )
        )

        def validate(
            view_root: Path,
            candidates: t.MappingKV[Path, Path],
        ) -> t.Infra.EditResult:
            """Run the real configured validators against the staged candidate.

            Args:
                view_root: The root directory of the staged source view.
                candidates: A mapping from original file paths to their staged
                counterparts.

            Returns:
                A result indicating whether the staged changes pass validation and any
                associated reports.
            """
            return FlextInfraUtilitiesProtectedEditPreview._preview_write_reports(
                candidates,
                before_sources,
                before_lints,
                view_root,
                gates=gates,
            )

        return source_preview.preview_sources(
            workspace, normalized_updates, validate
        ).unwrap()

    @staticmethod
    def preview_source_lint(
        py_file: Path,
        workspace: Path,
        *,
        updated_source: str,
        source_preview: p.Infra.SourcePreview,
        gates: t.StrSequence | None = None,
    ) -> t.Pair[t.Infra.LintSnapshot, t.Infra.LintSnapshot]:
        """Compare live and staged lint snapshots without changing live source.

        Args:
            py_file: The Python file to lint.
            workspace: The root of the workspace containing the file.
            updated_source: The updated source code for the file.
            source_preview: The injected staged-source preview collaborator.
            gates: Optional sequence of gate names to apply during linting.

        Returns:
            A pair of lint snapshots, the first for the original source and the second
              for the updated source.
        """
        original_source = py_file.read_text(encoding=c.DEFAULT_ENCODING)
        before = FlextInfraUtilitiesProtectedEditPreview.lint_snapshot(
            py_file, workspace, gates=gates
        )
        if updated_source == original_source:
            return before, before

        path = py_file.resolve()

        def validate(
            view_root: Path,
            candidates: t.MappingKV[Path, Path],
        ) -> t.Infra.LintSnapshot:
            return FlextInfraUtilitiesProtectedEditPreview.lint_snapshot(
                candidates[path], view_root, gates=gates
            )

        after = source_preview.preview_sources(
            workspace, {path: updated_source}, validate
        ).unwrap()
        return before, after


__all__: list[str] = ["FlextInfraUtilitiesProtectedEditPreview"]
