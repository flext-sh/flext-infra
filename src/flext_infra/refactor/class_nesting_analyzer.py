"""Class-nesting analysis derived from the public Rope workspace."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, t, u
from flext_infra.api import infra

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class FlextInfraRefactorClassNestingAnalyzer:
    """Report automatic class-nesting plans across project workspaces."""

    @classmethod
    def analyze_files(cls, files: t.SequenceOf[Path]) -> m.Infra.ClassNestingReport:
        """Analyze files and return aggregated class-nesting violations."""
        grouped_targets = cls._group_targets_by_project_root(files)
        confidence_counts: Counter[str] = Counter()
        per_file_counts: Counter[str] = Counter()
        violations: t.MutableSequenceOf[m.Infra.ClassNestingViolation] = []
        for project_root, target_files in grouped_targets.items():
            with infra.rope_workspace(project_root) as rope_workspace:
                for file_path in target_files:
                    for violation in u.Infra.class_nesting_plan(
                        rope_workspace, file_path
                    ).unwrap():
                        violations.append(violation)
                        confidence_counts[violation.confidence] += 1
                        per_file_counts[violation.file] += 1
        return m.Infra.ClassNestingReport(
            violations_count=len(violations),
            confidence_counts=dict(confidence_counts),
            violations=tuple(violations),
            per_file_counts=dict(per_file_counts),
        )

    @staticmethod
    def _group_targets_by_project_root(
        files: t.SequenceOf[Path],
    ) -> t.MappingKV[Path, t.VariadicTuple[Path]]:
        """Group resolved targets by their canonical project root."""
        grouped: MutableMapping[Path, list[Path]] = {}
        for file_path in files:
            resolved_file = file_path.resolve()
            project_root = u.Infra.resolve_project_root(resolved_file)
            if project_root is None:
                msg = f"Could not resolve project root for {resolved_file}"
                raise ValueError(msg)
            grouped.setdefault(project_root, []).append(resolved_file)
        return {root: tuple(paths) for root, paths in grouped.items()}


__all__: list[str] = ["FlextInfraRefactorClassNestingAnalyzer"]
