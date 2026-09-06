"""Class-nesting analysis derived from the public Rope workspace."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class FlextInfraRefactorClassNestingAnalyzer:
    """Report automatic class-nesting plans across project workspaces."""

    @classmethod
    def analyze_files(cls, files: t.SequenceOf[Path]) -> m.Infra.ClassNestingReport:
        """Analyze files and return aggregated class-nesting violations."""
        grouped_targets = cls._group_targets_by_project_root(files)
        if not grouped_targets:
            return m.Infra.ClassNestingReport(
                violations_count=0,
                confidence_counts={},
                violations=(),
                per_file_counts={},
            )
        confidence_counts: Counter[str] = Counter()
        per_file_counts: Counter[str] = Counter()
        violations: t.MutableSequenceOf[m.Infra.ClassNestingViolation] = []
        for project_root, target_files in grouped_targets.items():
            with u.Infra.open_project(project_root) as rope_project:
                for module_path in sorted(target_files):
                    file_path = (
                        project_root / c.Infra.DEFAULT_SRC_DIR / module_path
                    ).resolve()
                    resource = u.Infra.get_resource_from_path(rope_project, file_path)
                    if resource is None:
                        raise FileNotFoundError(file_path)
                    for plan in u.Infra.class_nesting_plans(
                        project_root, file_path, rope_project, resource
                    ):
                        violations.append(plan)
                        confidence_counts[plan.confidence] += 1
                        per_file_counts[plan.file] += 1
        return m.Infra.ClassNestingReport(
            violations_count=len(violations),
            confidence_counts=dict(confidence_counts),
            violations=tuple(violations),
            per_file_counts=dict(per_file_counts),
        )

    @staticmethod
    def _group_targets_by_project_root(
        files: t.SequenceOf[Path],
    ) -> t.MappingKV[Path, set[str]]:
        """Group resolved targets by their canonical project root."""
        grouped: MutableMapping[Path, set[str]] = {}
        for file_path in files:
            resolved_file = file_path.resolve()
            project_root = u.Infra.resolve_project_root(resolved_file)
            if project_root is None:
                msg = f"class-nesting target has no project root: {file_path}"
                raise ValueError(msg)
            module_path = file_path.resolve().relative_to(
                (project_root / c.Infra.DEFAULT_SRC_DIR).resolve()
            )
            grouped.setdefault(project_root, set()).add(module_path.as_posix())
        return grouped


__all__: list[str] = ["FlextInfraRefactorClassNestingAnalyzer"]
