from __future__ import annotations

from collections import Counter
from pathlib import Path

from flext_core import r
from pydantic import TypeAdapter, ValidationError

from flext_infra import c, m, u
from flext_infra.refactor.scanner import FlextInfraRefactorLooseClassScanner

type _ClassNestingMappingIndex = dict[
    tuple[str, str],
    m.Infra.ClassNestingMapping,
]


class FlextInfraRefactorClassNestingAnalyzer:
    @classmethod
    def analyze_files(cls, files: list[Path]) -> m.Infra.ClassNestingReport:
        if not files:
            return m.Infra.ClassNestingReport(
                violations_count=0,
                confidence_counts={},
                violations=[],
                per_file_counts={},
            )
        grouped_targets = cls._group_targets_by_project_root(files)
        if not grouped_targets:
            return m.Infra.ClassNestingReport(
                violations_count=0,
                confidence_counts={},
                violations=[],
                per_file_counts={},
            )
        scanner = FlextInfraRefactorLooseClassScanner()
        mapping_result = cls._load_mapping_index()
        mapping_index: _ClassNestingMappingIndex = (
            mapping_result.value if mapping_result.is_success else {}
        )
        confidence_counts: Counter[str] = Counter()
        per_file_counts: Counter[str] = Counter()
        violations: list[m.Infra.ClassNestingViolation] = []
        for project_root, target_files in grouped_targets.items():
            scan_result = scanner.scan(project_root)
            if scan_result.is_failure:
                continue
            try:
                parsed_violations: list[m.Infra.LooseClassViolation] = TypeAdapter(
                    list[m.Infra.LooseClassViolation],
                ).validate_python(
                    scan_result.value.get(c.Infra.ReportKeys.VIOLATIONS, []),
                )
            except ValidationError:
                continue
            for parsed_violation in parsed_violations:
                normalized_file = cls._normalize_module_path(parsed_violation.file)
                if target_files and normalized_file not in target_files:
                    continue
                line = parsed_violation.line if parsed_violation.line > 0 else 1
                confidence = parsed_violation.confidence or c.Infra.Severity.LOW
                target_namespace = ""
                rewrite_scope = c.Infra.ReportKeys.FILE
                mapped_entry = mapping_index.get((
                    normalized_file,
                    parsed_violation.class_name,
                ))
                if mapped_entry is not None:
                    target_namespace = mapped_entry.target_namespace
                    confidence = mapped_entry.confidence
                    rewrite_scope = cls._normalize_rewrite_scope(
                        mapped_entry.rewrite_scope,
                    )
                elif parsed_violation.expected_prefix:
                    target_namespace = parsed_violation.expected_prefix
                violations.append(
                    m.Infra.ClassNestingViolation(
                        file=normalized_file,
                        line=line,
                        class_name=parsed_violation.class_name,
                        target_namespace=target_namespace,
                        confidence=confidence,
                        rewrite_scope=rewrite_scope,
                    ),
                )
                confidence_counts[confidence] += 1
                per_file_counts[normalized_file] += 1
        return m.Infra.ClassNestingReport(
            violations_count=len(violations),
            confidence_counts=dict(confidence_counts.items()),
            violations=violations,
            per_file_counts=dict(per_file_counts.items()),
        )

    @classmethod
    def _group_targets_by_project_root(cls, files: list[Path]) -> dict[Path, set[str]]:
        grouped: dict[Path, set[str]] = {}
        for file_path in files:
            project_root = cls._find_project_root(file_path)
            if project_root is None:
                continue
            module_path = cls._module_path_for_file(file_path, project_root)
            if module_path is None:
                continue
            grouped.setdefault(project_root, set()).add(module_path)
        return grouped

    @classmethod
    def _find_project_root(cls, file_path: Path) -> Path | None:
        resolved = file_path.resolve()
        for parent in (resolved.parent, *resolved.parents):
            src_dir = parent / c.Infra.Paths.DEFAULT_SRC_DIR
            if not src_dir.is_dir():
                continue
            try:
                resolved.relative_to(src_dir.resolve())
                return parent
            except ValueError:
                continue
        return None

    @classmethod
    def _module_path_for_file(cls, file_path: Path, project_root: Path) -> str | None:
        src_dir = (project_root / c.Infra.Paths.DEFAULT_SRC_DIR).resolve()
        resolved = file_path.resolve()
        try:
            relative = resolved.relative_to(src_dir)
        except ValueError:
            return None
        return relative.as_posix()

    @classmethod
    def _load_mapping_index(cls) -> r[_ClassNestingMappingIndex]:
        mapping_path = Path(__file__).resolve().parent / c.Infra.MAPPINGS_RELATIVE_PATH
        try:
            typed_doc = u.Infra.safe_load_yaml(mapping_path)
        except (OSError, TypeError) as exc:
            return r[_ClassNestingMappingIndex].fail(str(exc))
        raw_nesting = typed_doc.get(c.Infra.ReportKeys.CLASS_NESTING)
        if not isinstance(raw_nesting, list):
            return r[_ClassNestingMappingIndex].ok({})
        try:
            entries = TypeAdapter(
                list[m.Infra.ClassNestingMapping],
            ).validate_python(raw_nesting)
        except ValidationError as exc:
            return r[_ClassNestingMappingIndex].fail(str(exc))
        index: _ClassNestingMappingIndex = {}
        for entry in entries:
            scope = cls._normalize_rewrite_scope(entry.rewrite_scope)
            norm = cls._normalize_module_path(entry.current_file)
            index[norm, entry.loose_name] = m.Infra.ClassNestingMapping(
                loose_name=entry.loose_name,
                current_file=entry.current_file,
                target_namespace=entry.target_namespace,
                confidence=entry.confidence,
                rewrite_scope=scope,
                target_name=entry.target_name,
                reason=entry.reason,
            )
        return r[_ClassNestingMappingIndex].ok(index)

    @classmethod
    def _normalize_module_path(cls, raw_path: str) -> str:
        normalized = raw_path.replace("\\", "/")
        path = Path(normalized)
        parts = path.parts
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path.as_posix().lstrip("./")

    @classmethod
    def _normalize_rewrite_scope(cls, raw_scope: str | None) -> str:
        if not isinstance(raw_scope, str):
            return c.Infra.ReportKeys.FILE
        candidate = raw_scope.strip().lower()
        if candidate in {
            c.Infra.ReportKeys.FILE,
            c.Infra.Toml.PROJECT,
            c.Infra.ReportKeys.WORKSPACE,
        }:
            return candidate
        return c.Infra.ReportKeys.FILE


__all__ = ["FlextInfraRefactorClassNestingAnalyzer"]
