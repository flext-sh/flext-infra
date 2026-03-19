"""Violation analysis and helper classification for refactor reports."""

from __future__ import annotations

import sys
from collections import Counter
from collections.abc import Mapping
from operator import itemgetter
from pathlib import Path

import libcst as cst

from flext_infra import c, m, u
from flext_infra.refactor._function_dependency_collector import (
    FunctionDependencyCollector,
)
from flext_infra.refactor._import_dependency_collector import ImportDependencyCollector
from flext_infra.refactor.class_nesting_analyzer import (
    FlextInfraRefactorClassNestingAnalyzer,
)
from flext_infra.transformers.violation_census_visitor import ViolationCensusVisitor


class FlextInfraRefactorViolationAnalyzer:
    @classmethod
    def analyze_files(
        cls,
        files: list[Path],
    ) -> m.Infra.ViolationAnalysisReport:
        """Analyze files and return aggregated violation and helper metrics."""
        totals: Counter[str] = Counter()
        per_file: dict[str, dict[str, int]] = {}
        helper_suggestions: list[m.Infra.HelperClassification] = []
        helper_totals: Counter[str] = Counter()
        helper_manual_review: list[m.Infra.HelperClassification] = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            except (OSError, UnicodeDecodeError):
                continue
            helper_analysis = cls._analyze_file_helpers(
                file_path=file_path,
            )
            helper_suggestions.extend(helper_analysis.suggestions)
            helper_totals.update(helper_analysis.totals)
            helper_manual_review.extend(helper_analysis.manual_review)
            file_counts: dict[str, int] = {}
            try:
                tree = cst.parse_module(content)
                violation_visitor = ViolationCensusVisitor(file_path=file_path)
                cst.metadata.MetadataWrapper(tree).visit(violation_visitor)
                for record in violation_visitor.records:
                    kind = str(record.get("kind", ""))
                    if kind:
                        totals[kind] += 1
                        file_counts[kind] = file_counts.get(kind, 0) + 1
            except cst.ParserSyntaxError:
                pass
            if file_counts:
                per_file[str(file_path)] = file_counts
        class_nesting = FlextInfraRefactorClassNestingAnalyzer.analyze_files(files)
        class_nesting_count = class_nesting.violations_count
        if class_nesting_count > 0:
            totals[c.Infra.ReportKeys.CLASS_NESTING] += class_nesting_count
        for raw_file, raw_count in class_nesting.per_file_counts.items():
            counts = per_file.setdefault(raw_file, {})
            counts[c.Infra.ReportKeys.CLASS_NESTING] = raw_count
        ranked_files: list[tuple[str, int, dict[str, int]]] = []
        for file_name, counts in per_file.items():
            ranked_files.append((file_name, sum(counts.values()), counts))
        ranked_files.sort(key=itemgetter(1), reverse=True)
        hottest_files = [
            m.Infra.ViolationTopFileSection(
                file=file_name,
                total=total,
                counts=counts,
            )
            for file_name, total, counts in ranked_files[:25]
        ]
        helper_report = m.Infra.HelperClassificationReport(
            totals=dict(helper_totals.items()),
            suggestions=helper_suggestions,
            manual_review=helper_manual_review,
        )
        return m.Infra.ViolationAnalysisReport(
            totals=dict(totals.items()),
            files=per_file,
            top_files=hottest_files,
            files_scanned=len(files),
            helper_classification=helper_report,
            class_nesting=class_nesting,
        )

    @classmethod
    def _analyze_file_helpers(
        cls,
        *,
        file_path: Path,
    ) -> m.Infra.HelperFileAnalysis:
        suggestions: list[m.Infra.HelperClassification] = []
        totals: Counter[str] = Counter()
        manual_review: list[m.Infra.HelperClassification] = []
        module = u.Infra.parse_module_cst(file_path)
        if module is None:
            return m.Infra.HelperFileAnalysis(
                suggestions=suggestions,
                totals=dict(totals.items()),
                manual_review=manual_review,
            )
        import_collector = ImportDependencyCollector()
        _ = module.visit(import_collector)
        for stmt in module.body:
            if not isinstance(stmt, cst.FunctionDef):
                continue
            classification = cls._classify_helper_function(
                file_path=file_path,
                function=stmt,
                local_to_import=import_collector.local_to_import,
            )
            suggestions.append(classification)
            category = classification.category
            totals[category] += 1
            if classification.manual_review:
                manual_review.append(classification)
        return m.Infra.HelperFileAnalysis(
            suggestions=suggestions,
            totals=dict(totals.items()),
            manual_review=manual_review,
        )

    @classmethod
    def _classify_helper_function(
        cls,
        *,
        file_path: Path,
        function: cst.FunctionDef,
        local_to_import: Mapping[str, str],
    ) -> m.Infra.HelperClassification:
        dependency_collector = FunctionDependencyCollector()
        function.visit(dependency_collector)
        dependencies: set[str] = set()
        for name in dependency_collector.names:
            imported = local_to_import.get(name)
            if imported is not None:
                dependencies.add(imported)
        decorator_dependencies: set[str] = set()
        for decorator in function.decorators:
            decorator_root = u.Infra.root_name(decorator.decorator)
            if not decorator_root:
                continue
            imported = local_to_import.get(decorator_root)
            if imported is not None:
                decorator_dependencies.add(imported)
        dependencies.update(decorator_dependencies)
        matched_categories = cls._match_categories(
            dependencies=dependencies,
            has_decorators=bool(function.decorators),
        )
        category, manual, reason = cls._resolve_category(
            dependencies=dependencies,
            matched_categories=matched_categories,
        )
        namespace_root = c.Infra.NAMESPACE_PREFIXES[category]
        return m.Infra.HelperClassification(
            file=str(file_path),
            function=function.name.value,
            category=category,
            target_namespace=f"{namespace_root}.{function.name.value}",
            dependencies=sorted(dependencies),
            manual_review=manual,
            review_reason=reason,
        )

    @classmethod
    def _match_categories(
        cls,
        *,
        dependencies: set[str],
        has_decorators: bool,
    ) -> set[str]:
        matched: set[str] = set()
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
        dependencies: set[str],
        matched_categories: set[str],
    ) -> tuple[str, bool, str]:
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
    def _is_pure_utility_dependencies(cls, dependencies: set[str]) -> bool:
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


__all__ = ["FlextInfraRefactorViolationAnalyzer"]
