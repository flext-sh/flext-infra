"""Violation analysis and helper classification for refactor reports.

Uses rope-based analysis and regex source scanning instead of CST visitors.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from collections.abc import MutableMapping, MutableSequence, Sequence
from operator import itemgetter
from pathlib import Path

from flext_infra import (
    FlextInfraRefactorClassNestingAnalyzer,
    FlextInfraViolationCensusVisitor,
    c,
    m,
    t,
)


class FlextInfraRefactorViolationAnalyzer:
    """Analyzer for refactor violation metrics across source files."""

    _IMPORT_RE = re.compile(
        r"^(?:from\s+([\w.]+)\s+import\s+(.+)|import\s+(.+))$",
        re.MULTILINE,
    )
    _FUNCTION_DEF_RE = re.compile(
        r"^def\s+(\w+)\s*\(",
        re.MULTILINE,
    )

    @classmethod
    def analyze_files(
        cls,
        files: Sequence[Path],
    ) -> m.Infra.ViolationAnalysisReport:
        """Analyze files and return aggregated violation and helper metrics."""
        totals: Counter[str] = Counter()
        per_file: MutableMapping[str, t.MutableIntMapping] = {}
        helper_suggestions: MutableSequence[m.Infra.HelperClassification] = []
        helper_totals: Counter[str] = Counter()
        helper_manual_review: MutableSequence[m.Infra.HelperClassification] = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            helper_analysis = cls._analyze_file_helpers(
                file_path=file_path,
                content=content,
            )
            helper_suggestions.extend(helper_analysis.suggestions)
            helper_totals.update(helper_analysis.totals)
            helper_manual_review.extend(helper_analysis.manual_review)
            file_counts: t.MutableIntMapping = {}
            violation_visitor = FlextInfraViolationCensusVisitor(file_path=file_path)
            violation_visitor.scan_source(content)
            for record in violation_visitor.records:
                kind = str(record.get("kind", ""))
                if kind:
                    totals[kind] += 1
                    file_counts[kind] = file_counts.get(kind, 0) + 1
            if file_counts:
                per_file[str(file_path)] = file_counts
        class_nesting = FlextInfraRefactorClassNestingAnalyzer.analyze_files(files)
        class_nesting_count = class_nesting.violations_count
        if class_nesting_count > 0:
            totals[c.Infra.ReportKeys.CLASS_NESTING] += class_nesting_count
        for raw_file, raw_count in class_nesting.per_file_counts.items():
            counts = per_file.setdefault(raw_file, {})
            counts[c.Infra.ReportKeys.CLASS_NESTING] = raw_count
        ranked_files: Sequence[t.Infra.Triple[str, int, t.IntMapping]] = [
            (file_name, sum(counts.values()), counts)
            for file_name, counts in per_file.items()
        ]
        ranked_sorted = sorted(ranked_files, key=itemgetter(1), reverse=True)
        hottest_files = [
            m.Infra.ViolationTopFileSection(
                file=file_name,
                total=total,
                counts={**counts},
            )
            for file_name, total, counts in ranked_sorted[:25]
        ]
        helper_report = m.Infra.HelperClassificationReport(
            totals=dict(helper_totals),
            suggestions=tuple(helper_suggestions),
            manual_review=tuple(helper_manual_review),
        )
        return m.Infra.ViolationAnalysisReport(
            totals=dict(totals),
            files={k: {**v} for k, v in per_file.items()},
            top_files=tuple(hottest_files),
            files_scanned=len(files),
            helper_classification=helper_report,
            class_nesting=class_nesting,
        )

    @classmethod
    def _analyze_file_helpers(
        cls,
        *,
        file_path: Path,
        content: str,
    ) -> m.Infra.HelperFileAnalysis:
        suggestions: MutableSequence[m.Infra.HelperClassification] = []
        totals: Counter[str] = Counter()
        manual_review: MutableSequence[m.Infra.HelperClassification] = []
        local_to_import = cls._extract_local_to_import(content)
        for match in cls._FUNCTION_DEF_RE.finditer(content):
            func_name = match.group(1)
            func_body = cls._extract_function_body(content, match.start())
            classification = cls._classify_helper_function(
                file_path=file_path,
                func_name=func_name,
                func_body=func_body,
                local_to_import=local_to_import,
            )
            suggestions.append(classification)
            category = classification.category
            totals[category] += 1
            if classification.manual_review:
                manual_review.append(classification)
        return m.Infra.HelperFileAnalysis(
            suggestions=tuple(suggestions),
            totals=dict(totals),
            manual_review=tuple(manual_review),
        )

    @classmethod
    def _classify_helper_function(
        cls,
        *,
        file_path: Path,
        func_name: str,
        func_body: str,
        local_to_import: t.StrMapping,
    ) -> m.Infra.HelperClassification:
        used_names = set(re.findall(r"\b([A-Za-z_]\w*)\b", func_body))
        dependencies: t.Infra.StrSet = set()
        for name in used_names:
            imported = local_to_import.get(name)
            if imported is not None:
                dependencies.add(imported)
        has_decorators = bool(re.search(r"@\w+", func_body))
        matched_categories = cls._match_categories(
            dependencies=dependencies,
            has_decorators=has_decorators,
        )
        category, manual, reason = cls._resolve_category(
            dependencies=dependencies,
            matched_categories=matched_categories,
        )
        namespace_root = c.Infra.NAMESPACE_PREFIXES[category]
        return m.Infra.HelperClassification(
            file=str(file_path),
            function=func_name,
            category=category,
            target_namespace=f"{namespace_root}.{func_name}",
            dependencies=sorted(dependencies),
            manual_review=manual,
            review_reason=reason,
        )

    @classmethod
    def _match_categories(
        cls,
        *,
        dependencies: t.Infra.StrSet,
        has_decorators: bool,
    ) -> t.Infra.StrSet:
        matched: t.Infra.StrSet = set()
        for dependency in dependencies:
            lowered = dependency.lower()
            if any(token in lowered for token in c.Infra.MODEL_TOKENS):
                matched.add("models")
            if any(token in lowered for token in c.Infra.DECORATOR_TOKENS):
                matched.add("decorators")
            if any(token in lowered for token in c.Infra.DISPATCHER_TOKENS):
                matched.add("dispatcher")
        if has_decorators:
            matched.add("decorators")
        return matched

    @classmethod
    def _resolve_category(
        cls,
        *,
        dependencies: t.Infra.StrSet,
        matched_categories: t.Infra.StrSet,
    ) -> t.Infra.Triple[str, bool, str]:
        if len(matched_categories) > 1:
            ordered = [
                category
                for category in c.Infra.CLASSIFICATION_PRIORITY
                if category in matched_categories
            ]
            cats = ", ".join(sorted(matched_categories))
            return (ordered[0], True, f"Cross-cutting concerns detected: {cats}")
        if len(matched_categories) == 1:
            category = next(iter(matched_categories))
            return (category, False, "")
        if cls._is_pure_utility_dependencies(dependencies):
            return ("utility", False, "")
        return (
            "utility",
            True,
            "External dependencies outside helper taxonomy; manual review required",
        )

    @classmethod
    def _is_pure_utility_dependencies(cls, dependencies: t.Infra.StrSet) -> bool:
        if not dependencies:
            return True
        for dependency in dependencies:
            root = dependency.split(".", maxsplit=1)[0]
            if root in sys.stdlib_module_names:
                continue
            if root in {"typing", "collections", "dataclasses", "pathlib"}:
                continue
            if root == "builtins":
                continue
            return False
        return True

    @staticmethod
    def _extract_local_to_import(content: str) -> t.StrMapping:
        """Extract local-name -> fully-qualified-name mapping from imports."""
        result: t.MutableStrMapping = {}
        import_re = re.compile(
            r"^(?:from\s+([\w.]+)\s+import\s+(.+)|import\s+([\w.]+)(?:\s+as\s+(\w+))?)$",
            re.MULTILINE,
        )
        for match in import_re.finditer(content):
            if match.group(1) is not None:
                module_name = match.group(1)
                names_part = match.group(2).strip().rstrip("\\")
                for name_entry in names_part.split(","):
                    name_entry = name_entry.strip()
                    if not name_entry or name_entry == "(":
                        continue
                    parts = re.split(r"\s+as\s+", name_entry, maxsplit=1)
                    imported_name = parts[0].strip().rstrip(")")
                    local = parts[1].strip() if len(parts) > 1 else imported_name
                    if local and imported_name:
                        result[local] = f"{module_name}.{imported_name}"
            elif match.group(3) is not None:
                imported = match.group(3)
                local = match.group(4) or imported.split(".", maxsplit=1)[0]
                result[local] = imported
        return result

    @staticmethod
    def _extract_function_body(content: str, start: int) -> str:
        """Extract function body text from content starting at def position."""
        lines = content[start:].splitlines()
        if not lines:
            return ""
        body_lines: MutableSequence[str] = [lines[0]]
        for line in lines[1:]:
            if not line.strip():
                body_lines.append(line)
                continue
            indent = len(line) - len(line.lstrip())
            if indent > 0:
                body_lines.append(line)
            else:
                break
        return "\n".join(body_lines)


__all__ = ["FlextInfraRefactorViolationAnalyzer"]
