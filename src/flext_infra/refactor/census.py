"""Workspace-wide Rope-only census orchestration."""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Annotated, override

from rope.base.exceptions import RopeError

from flext_cli import cli
from flext_infra import (
    FlextInfraProjectSelectionServiceBase,
    FlextInfraRopeWorkspace,
    c,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra.refactor._census_apply import (
    FlextInfraRefactorCensusApplyMixin,
)
from flext_infra.refactor._census_collect_helpers import (
    FlextInfraRefactorCensusCollectHelpersMixin,
)
from flext_infra.refactor._census_filters import (
    FlextInfraRefactorCensusFiltersMixin,
)
from flext_infra.refactor._census_inventory import (
    FlextInfraRefactorCensusInventoryMixin,
)
from flext_infra.refactor._census_objects import (
    FlextInfraRefactorCensusObjectsMixin,
)
from flext_infra.refactor._census_render import (
    FlextInfraRefactorCensusRenderMixin,
)
from flext_infra.refactor._census_rules_alias import (
    FlextInfraRefactorCensusRulesAliasMixin,
)
from flext_infra.refactor._census_rules_struct import (
    FlextInfraRefactorCensusRulesStructMixin,
)
from flext_infra.refactor._census_symbols import (
    FlextInfraRefactorCensusSymbolsMixin,
)

_log = u.fetch_logger(__name__)

_ROPE_SAFE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    *FlextInfraUtilitiesRopeCore.RUNTIME_ERRORS,
    RopeError,
    RecursionError,
    SyntaxError,
    ValueError,
    RuntimeError,
)


class FlextInfraRefactorCensus(
    FlextInfraProjectSelectionServiceBase[m.Infra.Census.WorkspaceReport],
    FlextInfraRefactorCensusApplyMixin,
    FlextInfraRefactorCensusCollectHelpersMixin,
    FlextInfraRefactorCensusFiltersMixin,
    FlextInfraRefactorCensusInventoryMixin,
    FlextInfraRefactorCensusObjectsMixin,
    FlextInfraRefactorCensusRenderMixin,
    FlextInfraRefactorCensusRulesAliasMixin,
    FlextInfraRefactorCensusRulesStructMixin,
    FlextInfraRefactorCensusSymbolsMixin,
):
    """Generalized Rope-only census service for Python objects across the workspace."""

    json_output: Annotated[
        str | None,
        m.Field(description="Path to write JSON report"),
    ] = None
    impact_map_output: Annotated[
        str | None,
        m.Field(description="Path to write dry-run impact map JSON"),
    ] = None
    kinds: Annotated[
        t.StrSequence | None,
        m.Field(description="Optional symbol-kind filters; repeat --kinds NAME"),
    ] = None
    rules: Annotated[
        t.StrSequence | None,
        m.Field(description="Optional violation-rule filters; repeat --rules NAME"),
    ] = None
    families: Annotated[
        t.StrSequence | None,
        m.Field(
            description="Optional namespace-family filters; repeat --families NAME"
        ),
    ] = None
    include_local_scopes: Annotated[
        bool,
        m.Field(description="Include locals, parameters, and nested scopes"),
    ] = True

    @property
    def json_output_path(self) -> Path | None:
        """Return the resolved JSON export path when provided."""
        path: Path | None = u.Infra.normalize_optional_path(self.json_output)
        return path

    @property
    def impact_map_output_path(self) -> Path | None:
        """Return the resolved impact-map export path when provided."""
        path: Path | None = u.Infra.normalize_optional_path(
            self.impact_map_output,
        )
        return path

    @property
    def kind_names(self) -> t.StrSequence | None:
        """Return normalized symbol-kind filters."""
        return u.Infra.normalize_sequence_values(self.kinds)

    @property
    def rule_names(self) -> t.StrSequence | None:
        """Return normalized violation-rule filters."""
        return u.Infra.normalize_sequence_values(self.rules)

    @property
    def family_names(self) -> t.StrSequence | None:
        """Return normalized family filters."""
        return u.Infra.normalize_sequence_values(self.families)

    @property
    @override
    def dry_run_gate_names(self) -> t.StrSequence:
        """Return the per-candidate gate set (``lint`` + ``pyrefly``).

        Mypy and pyright perform transitive module analysis that flags
        ``__init__.py`` lazy-import references to just-removed symbols
        *before* ``FlextInfraCodegenLazyInit`` regenerates them at the
        end of ``_apply_supported_fixes``. That would roll back every
        safe candidate. The per-candidate gate therefore uses the two
        fast tools that validate the actual file being modified
        (``ruff`` E/F + ``pyrefly``); the session-level regen run + a
        final ``ruff format/fix`` on every touched file guarantees
        consistency afterwards.
        """
        return (c.Infra.LINT, c.Infra.PYREFLY)

    def _execution_reports(
        self,
    ) -> tuple[
        m.Infra.Census.WorkspaceReport,
        m.Infra.Census.WorkspaceReport | None,
    ]:
        """Collect the final report and the pre-apply impact-map report."""
        started = time.monotonic()
        applied = frozenset[str]()
        impact_map_report: m.Infra.Census.WorkspaceReport | None = None
        with FlextInfraRopeWorkspace.open_workspace(self.root) as rope:
            report = self._collect_report(
                rope,
                project_names=self.project_names,
                kind_names=self.kind_names,
                family_names=self.family_names,
                rule_names=self.rule_names,
                include_local_scopes=self.include_local_scopes,
                applied=applied,
            )
            impact_map_report = report
            if self.apply_changes and not self.effective_dry_run:
                applied = self._apply_supported_fixes(rope, report)
                if applied:
                    rope.reload()
                    report = self._collect_report(
                        rope,
                        project_names=self.project_names,
                        kind_names=self.kind_names,
                        family_names=self.family_names,
                        rule_names=self.rule_names,
                        include_local_scopes=self.include_local_scopes,
                        applied=applied,
                    )
        finalized_report = report.model_copy(
            update={"scan_duration_seconds": time.monotonic() - started}
        )
        return finalized_report, impact_map_report

    def build_report(self) -> m.Infra.Census.WorkspaceReport:
        """Build the canonical workspace census report without CLI side effects."""
        report, _ = self._execution_reports()
        return report

    @override
    def execute(self) -> p.Result[m.Infra.Census.WorkspaceReport]:
        """Execute the census with one shared Rope session."""
        report, impact_map_report = self._execution_reports()
        cli.display_text(self.render_text(report))
        if self.json_output_path is not None:
            u.Infra.export_pydantic_json(report, self.json_output_path)
            u.Cli.info(f"JSON report exported to: {self.json_output_path}")
        if self.impact_map_output_path is not None:
            impact_result = u.Infra.write_impact_map(
                self._impact_map_results(impact_map_report or report),
                self.impact_map_output_path,
            )
            if impact_result.failure:
                return r[m.Infra.Census.WorkspaceReport].fail(
                    impact_result.error or "impact map write failed"
                )
            u.Cli.info(f"Impact map exported to: {self.impact_map_output_path}")
        return r[m.Infra.Census.WorkspaceReport].ok(report)

    def _collect_report(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        *,
        project_names: t.StrSequence | None,
        kind_names: t.StrSequence | None,
        family_names: t.StrSequence | None,
        rule_names: t.StrSequence | None,
        include_local_scopes: bool,
        applied: frozenset[str],
    ) -> m.Infra.Census.WorkspaceReport:
        """Collect report."""
        selected_families = self._selected_families(family_names)
        selected_kinds: frozenset[str] | None = (
            frozenset(kind_names) if kind_names else None
        )
        selected_rules: frozenset[str] | None = (
            frozenset(rule_names) if rule_names else None
        )
        collect_object_inventory = self._should_collect_object_inventory(
            rule_names,
            selected_rules=selected_rules,
        )
        include_object_references = self._should_collect_object_references(
            rule_names,
        )
        project_objects: dict[str, list[m.Infra.Census.Object]] = defaultdict(list)
        project_violations: dict[str, list[m.Infra.Census.Violation]] = defaultdict(
            list
        )
        project_fixes: dict[str, list[m.Infra.Census.Fix]] = defaultdict(list)
        report_projects: set[str] = set()
        for module in self._modules_for_rules(
            rope,
            project_names=project_names,
            selected_families=selected_families,
            rule_names=rule_names,
        ):
            convention = rope.convention(module.file_path)
            project = self._project_name_for_module(module, convention)
            if not project:
                continue
            module_objects: tuple[m.Infra.Census.Object, ...] | None = None
            objects: tuple[m.Infra.Census.Object, ...] = ()
            if collect_object_inventory:
                try:
                    module_objects = tuple(
                        rope.objects(
                            module.file_path,
                            include_local_scopes=include_local_scopes,
                            include_references=include_object_references,
                        )
                    )
                except _ROPE_SAFE_EXCEPTIONS as exc:
                    self._handle_rope_stage_failure(
                        file_path=module.file_path,
                        stage="inventory",
                        exc=exc,
                    )
                    continue
                objects = tuple(
                    item
                    for item in module_objects
                    if self._include_object(
                        item,
                        kind_names=kind_names,
                        selected_families=selected_families,
                        selected_kinds=selected_kinds,
                    )
                )
                if objects:
                    project_objects[project].extend(objects)
            if objects:
                report_projects.add(project)
            try:
                violations, fixes = self._module_rules(
                    rope,
                    module.file_path,
                    objects=module_objects,
                    project_name=project,
                    applied=applied,
                    kind_names=kind_names,
                    rule_names=rule_names,
                    selected_kinds=selected_kinds,
                    selected_rules=selected_rules,
                    convention=convention,
                )
            except _ROPE_SAFE_EXCEPTIONS as exc:
                self._handle_rope_stage_failure(
                    file_path=module.file_path,
                    stage="rules",
                    exc=exc,
                )
                continue
            report_projects.add(project)
            if not objects and not violations and not fixes:
                continue
            project_violations[project].extend(violations)
            project_fixes[project].extend(fixes)
        duplicates = self._duplicate_groups(tuple(project_objects.values()))
        duplicate_keys = frozenset(
            self._object_key(item)
            for group in duplicates
            for item in group.definitions[1:]
        )
        report_project_names = tuple(
            sorted(
                report_projects
                | set(project_objects)
                | set(project_violations)
                | set(project_fixes),
            )
        )
        project_reports = tuple(
            self._project_report(
                project,
                objects=tuple(project_objects[project]),
                seed_violations=tuple(project_violations[project]),
                fixes=tuple(project_fixes[project]),
                duplicate_keys=duplicate_keys,
                rule_names=rule_names,
                selected_rules=selected_rules,
            )
            for project in report_project_names
        )
        if self.effective_dry_run:
            project_reports = self._validated_project_reports(
                rope,
                project_reports,
            )
        return m.Infra.Census.WorkspaceReport(
            projects=project_reports,
            total_objects=sum(report.objects_total for report in project_reports),
            total_violations=sum(report.violations_total for report in project_reports),
            total_fixable=sum(
                1
                for report in project_reports
                for violation in report.violations
                if violation.fixable
            ),
            fixes_total=sum(len(report.fixes) for report in project_reports),
            duplicates=duplicates,
            unused_count=sum(report.unused_count for report in project_reports),
            test_only_count=sum(report.test_only_count for report in project_reports),
            removal_candidate_count=sum(
                report.removal_candidate_count for report in project_reports
            ),
            removal_candidates=tuple(
                candidate
                for report in project_reports
                for candidate in report.removal_candidates
            ),
        )

    def _handle_rope_stage_failure(
        self,
        *,
        file_path: Path,
        stage: str,
        exc: BaseException,
    ) -> None:
        """Handle rope stage failure."""
        error = f"{type(exc).__name__}: {exc}"
        _log.warning(
            "census_rope_stage_failed",
            stage=stage,
            file_path=str(file_path),
            error=error,
        )
        if self.fail_fast:
            msg = f"census rope {stage} failed for {file_path}: {error}"
            raise RuntimeError(msg) from exc

    def _project_report(
        self,
        project: str,
        *,
        objects: tuple[m.Infra.Census.Object, ...],
        seed_violations: tuple[m.Infra.Census.Violation, ...],
        fixes: tuple[m.Infra.Census.Fix, ...],
        duplicate_keys: frozenset[str],
        rule_names: t.StrSequence | None,
        selected_rules: frozenset[str] | None = None,
    ) -> m.Infra.Census.ProjectReport:
        """Project report."""
        violations = list(seed_violations)
        if selected_rules is None and rule_names:
            selected_rules = frozenset(rule_names)
        include_unused = self._include_rule(
            "unused", rule_names=rule_names, selected_rules=selected_rules
        )
        include_test_only = self._include_rule(
            "test_only", rule_names=rule_names, selected_rules=selected_rules
        )
        include_duplicate = self._include_rule(
            "duplicate", rule_names=rule_names, selected_rules=selected_rules
        )
        include_wrong_tier = self._include_rule(
            "wrong_tier", rule_names=rule_names, selected_rules=selected_rules
        )
        unused_count = 0
        test_only_count = 0
        removal_candidates: list[m.Infra.Census.RemovalCandidate] = []
        for item in objects:
            is_unused = self._is_unused(item)
            is_test_only = self._is_test_only(item)
            if include_duplicate and self._object_key(item) in duplicate_keys:
                violations.append(
                    self._violation(
                        item,
                        kind="duplicate",
                        description="Duplicate definition in workspace",
                    )
                )
            if is_unused and include_unused:
                unused_count += 1
                violations.append(
                    self._violation(
                        item,
                        kind="unused",
                        description="Object has no non-definition references",
                    )
                )
            if is_test_only and include_test_only:
                test_only_count += 1
                violations.append(
                    self._violation(
                        item,
                        kind="test_only",
                        description="Object is referenced only from tests/",
                    )
                )
            if (
                include_wrong_tier
                and item.expected_tier
                and item.actual_tier
                and item.expected_tier != item.actual_tier
            ):
                violations.append(
                    self._violation(
                        item,
                        kind="wrong_tier",
                        description=f"Expected tier '{item.expected_tier}' but found '{item.actual_tier}'",
                    )
                )
            candidate = self._removal_candidate(
                item,
                include_unused=include_unused,
                include_test_only=include_test_only,
            )
            if candidate is not None:
                removal_candidates.append(candidate)
        return m.Infra.Census.ProjectReport(
            project=project,
            objects=objects,
            objects_total=len(objects),
            objects_by_kind=dict(Counter(item.kind for item in objects)),
            violations=tuple(violations),
            fixes=fixes,
            violations_total=len(violations),
            fixes_applied=sum(1 for fix in fixes if fix.applied),
            unused_count=unused_count,
            test_only_count=test_only_count,
            removal_candidate_count=len(removal_candidates),
            removal_candidates=tuple(removal_candidates),
        )

    def _validated_project_reports(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        project_reports: tuple[m.Infra.Census.ProjectReport, ...],
    ) -> tuple[m.Infra.Census.ProjectReport, ...]:
        """Keep only removal candidates that pass the configured dry-run gates.

        Gate rejections are surfaced as explicit ``preview_rejected``
        violations so the census still completes with actionable output
        instead of aborting on the first rejected candidate.
        """
        validated_reports: list[m.Infra.Census.ProjectReport] = []
        # Preview writes are restored before the next candidate, so one shared
        # source cache stays valid for the entire dry-run validation pass.
        source_cache: dict[Path, str] = {}
        for report in project_reports:
            if not report.removal_candidates:
                validated_reports.append(report)
                continue
            validated_candidates_list: list[m.Infra.Census.RemovalCandidate] = []
            validated_violations = list(report.violations)
            for candidate in report.removal_candidates:
                preview_result = u.Infra.preview_simple_removal_candidate(
                    rope,
                    self.root,
                    candidate,
                    gates=self.dry_run_gate_names,
                    source_cache=source_cache,
                )
                if preview_result.failure:
                    msg = preview_result.error or (
                        "simple removal preview failed for "
                        f"{candidate.file_path}:{candidate.line} {candidate.object_name}"
                    )
                    if self.dry_run or self.fail_fast:
                        raise RuntimeError(msg)
                    _log.warning(
                        "census_preview_candidate_rejected",
                        candidate=candidate.file_path,
                        object_name=candidate.object_name,
                        error=msg,
                    )
                    validated_violations.append(
                        self._raw_violation(
                            project=report.project,
                            object_name=candidate.object_name,
                            object_kind=candidate.object_kind,
                            kind="preview_rejected",
                            file_path=Path(candidate.file_path),
                            line=candidate.line,
                            description=msg,
                        )
                    )
                    continue
                if preview_result.unwrap_or(False):
                    validated_candidates_list.append(candidate)
            validated_candidates = tuple(validated_candidates_list)
            validated_reports.append(
                report.model_copy(
                    update={
                        "violations": tuple(validated_violations),
                        "violations_total": len(validated_violations),
                        "removal_candidate_count": len(validated_candidates),
                        "removal_candidates": validated_candidates,
                    }
                )
            )
        return tuple(validated_reports)

    def _module_rules(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        objects: tuple[m.Infra.Census.Object, ...] | None,
        project_name: str,
        applied: frozenset[str],
        kind_names: t.StrSequence | None,
        rule_names: t.StrSequence | None,
        selected_kinds: frozenset[str] | None = None,
        selected_rules: frozenset[str] | None = None,
        convention: m.Infra.RopeModuleConvention | None = None,
    ) -> tuple[tuple[m.Infra.Census.Violation, ...], tuple[m.Infra.Census.Fix, ...]]:
        """Run every selected alias/MRO rule for one module and collect outcomes."""
        resolved_convention = convention or rope.convention(file_path)
        resolved_kinds = (
            selected_kinds
            if selected_kinds is not None
            else (frozenset(kind_names) if kind_names else frozenset())
        )
        symbol_index = self._lightweight_symbol_index(rope, file_path)
        violations: list[m.Infra.Census.Violation] = []
        fixes: list[m.Infra.Census.Fix] = []

        def selected(rule_name: str) -> bool:
            return self._include_rule(
                rule_name, rule_names=rule_names, selected_rules=selected_rules
            )

        if selected("runtime_alias"):
            v, f = self._rule_runtime_alias(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("manual_typing_alias"):
            v, f = self._rule_manual_typing_alias(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("compatibility_alias"):
            v, f = self._rule_compatibility_alias(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        if selected("mro_completeness"):
            v, f = self._rule_mro_completeness(
                rope,
                file_path,
                project_name=project_name,
                objects=objects,
                applied=applied,
                selected_kinds=resolved_kinds,
                symbol_index=symbol_index,
                convention=resolved_convention,
            )
            violations.extend(v)
            fixes.extend(f)
        return (tuple(violations), tuple(fixes))


__all__: list[str] = ["FlextInfraRefactorCensus"]
