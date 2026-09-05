"""Class-nesting analysis for refactor violation reporting."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, t, u
from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class FlextInfraRefactorClassNestingAnalyzer:
    """Detect class nesting violations and report FLEXT hierarchy issues."""

    @classmethod
    def analyze_files(cls, files: t.SequenceOf[Path]) -> m.Infra.ClassNestingReport:
        """Analyze files and return aggregated class-nesting violations."""
        if not files:
            return m.Infra.ClassNestingReport(
                violations_count=0,
                confidence_counts={},
                violations=(),
                per_file_counts={},
            )
        grouped_targets = cls._group_targets_by_project_root(files)
        if not grouped_targets:
            return m.Infra.ClassNestingReport(
                violations_count=0,
                confidence_counts={},
                violations=(),
                per_file_counts={},
            )
        scanner = FlextInfraRefactorLooseClassScanner()
        confidence_counts: Counter[str] = Counter()
        per_file_counts: Counter[str] = Counter()
        violations: t.MutableSequenceOf[m.Infra.ClassNestingViolation] = []
        for project_root, target_files in grouped_targets.items():
            scan_result = scanner.scan(project_root)
            payload = scan_result.unwrap()
            typed_items = t.Infra.CONTAINER_DICT_SEQ_ADAPTER.validate_python(
                payload[c.Infra.RK_VIOLATIONS]
            )
            parsed_violations: t.SequenceOf[m.Infra.LooseClassViolation] = [
                m.Infra.LooseClassViolation.model_validate(item) for item in typed_items
            ]
            for parsed_violation in parsed_violations:
                normalized_file = u.Infra.normalize_module_path(parsed_violation.file)
                if target_files and normalized_file not in target_files:
                    continue
                line = parsed_violation.line if parsed_violation.line > 0 else 1
                confidence = parsed_violation.confidence or c.Infra.SeverityLevel.LOW
                target_namespace = parsed_violation.expected_prefix
                violations.append(
                    m.Infra.ClassNestingViolation(
                        file=normalized_file,
                        line=line,
                        class_name=parsed_violation.class_name,
                        target_namespace=target_namespace,
                        confidence=confidence,
                        rewrite_scope=c.Infra.RK_FILE,
                    )
                )
                confidence_counts[confidence] += 1
                per_file_counts[normalized_file] += 1
        return m.Infra.ClassNestingReport(
            violations_count=len(violations),
            confidence_counts=dict(confidence_counts),
            violations=tuple(violations),
            per_file_counts=dict(per_file_counts),
        )

    @classmethod
    def _group_targets_by_project_root(
        cls, files: t.SequenceOf[Path]
    ) -> t.MappingKV[Path, t.Infra.StrSet]:
        """Group targets by project root."""
        grouped: MutableMapping[Path, t.Infra.StrSet] = {}
        for file_path in files:
            project_root = u.Infra.resolve_project_root(file_path)
            if project_root is None:
                continue
            module_path = cls._module_path_for_file(file_path, project_root)
            if module_path is None:
                continue
            grouped.setdefault(project_root, set()).add(module_path)
        return grouped

    @classmethod
    def _module_path_for_file(cls, file_path: Path, project_root: Path) -> str | None:
        """Return the module path for a file."""
        src_dir = (project_root / c.Infra.DEFAULT_SRC_DIR).resolve()
        resolved = file_path.resolve()
        try:
            relative = resolved.relative_to(src_dir)
        except ValueError:
            return None
        return relative.as_posix()


__all__: list[str] = ["FlextInfraRefactorClassNestingAnalyzer"]
