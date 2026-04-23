"""Workspace-wide Rope-only census orchestration."""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Annotated, ClassVar, override

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


class FlextInfraRefactorCensus(
    FlextInfraProjectSelectionServiceBase[m.Infra.Census.WorkspaceReport],
):
    """Generalized Rope-only census service for Python objects across the workspace."""

    _MIN_DUPLICATE_DEFINITIONS: ClassVar[int] = 2

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
        m.Field(description="Optional object-kind filters; repeat --kinds NAME"),
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
        return u.Infra.normalize_optional_path(self.json_output)

    @property
    def impact_map_output_path(self) -> Path | None:
        """Return the resolved impact-map export path when provided."""
        return u.Infra.normalize_optional_path(self.impact_map_output)

    @property
    def kind_names(self) -> t.StrSequence | None:
        """Return normalized object-kind filters."""
        return u.Infra.normalize_sequence_values(self.kinds)

    @property
    def rule_names(self) -> t.StrSequence | None:
        """Return normalized violation-rule filters."""
        return u.Infra.normalize_sequence_values(self.rules)

    @property
    def family_names(self) -> t.StrSequence | None:
        """Return normalized family filters."""
        return u.Infra.normalize_sequence_values(self.families)

    @staticmethod
    def render_text(report: m.Infra.Census.WorkspaceReport) -> str:
        """Render the canonical workspace census report."""
        return u.Infra.render_census_report(report)

    @override
    def execute(self) -> p.Result[m.Infra.Census.WorkspaceReport]:
        """Execute the census with one shared Rope session."""
        started = time.monotonic()
        applied = frozenset[str]()
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
            if self.apply_changes:
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
        report = report.model_copy(
            update={"scan_duration_seconds": time.monotonic() - started}
        )
        cli.display_text(self.render_text(report))
        if self.json_output_path is not None:
            u.Infra.export_pydantic_json(report, self.json_output_path)
            u.Cli.info(f"JSON report exported to: {self.json_output_path}")
        if self.impact_map_output_path is not None:
            impact_result = u.Infra.write_impact_map(
                self._impact_map_results(report),
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
        selected_families = self._selected_families(family_names)
        project_objects: dict[str, list[m.Infra.Census.Object]] = defaultdict(list)
        project_violations: dict[str, list[m.Infra.Census.Violation]] = defaultdict(
            list
        )
        project_fixes: dict[str, list[m.Infra.Census.Fix]] = defaultdict(list)
        for module in rope.modules(project_names=project_names):
            objects = tuple(
                item
                for item in rope.objects(
                    module.file_path,
                    include_local_scopes=include_local_scopes,
                )
                if self._include_object(
                    item,
                    kind_names=kind_names,
                    selected_families=selected_families,
                )
            )
            if not objects:
                continue
            project = objects[0].project
            project_objects[project].extend(objects)
            violations, fixes = self._module_rules(
                rope,
                module.file_path,
                objects=objects,
                applied=applied,
            )
            project_violations[project].extend(
                violation
                for violation in violations
                if self._include_rule(violation.kind, rule_names=rule_names)
            )
            project_fixes[project].extend(
                fix
                for fix in fixes
                if self._include_rule("runtime_alias", rule_names=rule_names)
            )
        duplicates = self._duplicate_groups(tuple(project_objects.values()))
        duplicate_keys = frozenset(
            self._object_key(item)
            for group in duplicates
            for item in group.definitions[1:]
        )
        project_reports = tuple(
            self._project_report(
                project,
                objects=tuple(project_objects[project]),
                seed_violations=tuple(project_violations[project]),
                fixes=tuple(project_fixes[project]),
                duplicate_keys=duplicate_keys,
                rule_names=rule_names,
            )
            for project in sorted(project_objects)
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

    def _project_report(
        self,
        project: str,
        *,
        objects: tuple[m.Infra.Census.Object, ...],
        seed_violations: tuple[m.Infra.Census.Violation, ...],
        fixes: tuple[m.Infra.Census.Fix, ...],
        duplicate_keys: frozenset[str],
        rule_names: t.StrSequence | None,
    ) -> m.Infra.Census.ProjectReport:
        violations = list(seed_violations)
        include_unused = self._include_rule("unused", rule_names=rule_names)
        include_test_only = self._include_rule("test_only", rule_names=rule_names)
        unused_count = 0
        test_only_count = 0
        removal_candidates: list[m.Infra.Census.RemovalCandidate] = []
        for item in objects:
            is_unused = self._is_unused(item)
            is_test_only = self._is_test_only(item)
            if self._object_key(item) in duplicate_keys and self._include_rule(
                "duplicate", rule_names=rule_names
            ):
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
                item.expected_tier
                and item.actual_tier
                and item.expected_tier != item.actual_tier
                and self._include_rule("wrong_tier", rule_names=rule_names)
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

    def _module_rules(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        objects: tuple[m.Infra.Census.Object, ...],
        applied: frozenset[str],
    ) -> tuple[tuple[m.Infra.Census.Violation, ...], tuple[m.Infra.Census.Fix, ...]]:
        convention = rope.convention(file_path)
        layout = convention.project_layout
        alias = convention.module_policy.expected_alias or ""
        family = convention.module_policy.expected_family or ""
        if layout is None or not alias or not family:
            return (), ()
        target_name = f"{layout.class_stem}{family}"
        target = next(
            (item for item in objects if item.scope_path == target_name), None
        )
        if target is None or f"{alias} = {target_name}" in rope.source(file_path):
            return (), ()
        fix = m.Infra.Census.Fix(
            object_name=target_name,
            action="ensure_runtime_alias",
            source_file=str(file_path),
            files_changed=1,
            applied=self._fix_key(file_path, target_name) in applied,
        )
        return (
            (
                self._violation(
                    target,
                    kind="runtime_alias",
                    description=f"Missing runtime alias '{alias}' for governed facade",
                    fixable=True,
                    fix_action="ensure_runtime_alias",
                ),
            ),
            (fix,),
        )

    def _apply_supported_fixes(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        report: m.Infra.Census.WorkspaceReport,
    ) -> frozenset[str]:
        applied: set[str] = set()
        removal_ranges_by_file: dict[Path, list[t.Infra.IntPair]] = defaultdict(list)
        removal_candidate_keys: set[str] = set()
        for project in report.projects:
            for fix in project.fixes:
                file_path = Path(fix.source_file)
                convention = rope.convention(file_path)
                alias = convention.module_policy.expected_alias or ""
                if fix.action != "ensure_runtime_alias" or not alias:
                    continue
                source = rope.source(file_path)
                updated = u.Infra.ensure_runtime_alias(
                    source,
                    alias=alias,
                    target_name=fix.object_name,
                )
                if updated == source:
                    continue
                resource = rope.resource(file_path)
                if resource is None:
                    continue
                resource.write(updated)
                applied.add(self._fix_key(file_path, fix.object_name))
        for candidate in report.removal_candidates:
            edit_plan = u.Infra.plan_simple_removal_edits(rope, candidate)
            if edit_plan is None:
                continue
            for file_path, ranges in edit_plan.items():
                removal_ranges_by_file[file_path].extend(ranges)
            removal_candidate_keys.add(
                self._fix_key(Path(candidate.file_path), candidate.object_name)
            )
        for file_path, ranges in sorted(removal_ranges_by_file.items()):
            merged_ranges = u.Infra.merge_line_ranges(ranges)
            source = rope.source(file_path)
            updated = u.Infra.apply_line_ranges(source, merged_ranges)
            if updated == source:
                continue
            resource = rope.resource(file_path)
            if resource is None:
                continue
            resource.write(updated)
        applied.update(removal_candidate_keys)
        return frozenset(applied)

    @staticmethod
    def _duplicate_groups(
        project_objects: tuple[list[m.Infra.Census.Object], ...],
    ) -> tuple[m.Infra.Census.DuplicateGroup, ...]:
        groups: dict[tuple[str, str, str], list[m.Infra.Census.Object]] = defaultdict(
            list
        )
        for item in (obj for objects in project_objects for obj in objects):
            owner = item.scope_path.rpartition(".")[0]
            groups[item.kind, item.name, owner].append(item)
        duplicates = []
        for (_kind, _name, _owner), definitions in sorted(groups.items()):
            if len(definitions) < FlextInfraRefactorCensus._MIN_DUPLICATE_DEFINITIONS:
                continue
            canonical = min(
                definitions,
                key=lambda item: (item.project, item.file_path, item.line),
            )
            duplicates.append(
                m.Infra.Census.DuplicateGroup(
                    name=definitions[0].name,
                    kind=definitions[0].kind,
                    definitions=tuple(definitions),
                    canonical=canonical.project,
                    value_identical=len({item.fingerprint for item in definitions})
                    == 1,
                )
            )
        return tuple(duplicates)

    @staticmethod
    def _include_object(
        item: m.Infra.Census.Object,
        *,
        kind_names: t.StrSequence | None,
        selected_families: frozenset[str],
    ) -> bool:
        if kind_names and item.kind not in frozenset(kind_names):
            return False
        if not selected_families:
            return True
        return (
            item.actual_tier.lower() in selected_families
            or item.expected_tier.lower() in selected_families
        )

    @staticmethod
    def _include_rule(rule: str, *, rule_names: t.StrSequence | None) -> bool:
        return rule_names is None or rule in frozenset(rule_names)

    @staticmethod
    def _selected_families(family_names: t.StrSequence | None) -> frozenset[str]:
        if not family_names:
            return frozenset()
        resolved = {
            c.Infra.FAMILY_SUFFIXES.get(name, name).lower() for name in family_names
        }
        return frozenset(resolved)

    @staticmethod
    def _violation(
        item: m.Infra.Census.Object,
        *,
        kind: str,
        description: str,
        fixable: bool = False,
        fix_action: str = "",
    ) -> m.Infra.Census.Violation:
        return m.Infra.Census.Violation(
            project=item.project,
            object_name=item.name,
            object_kind=item.kind,
            kind=kind,
            file_path=item.file_path,
            line=item.line,
            fixable=fixable,
            fix_action=fix_action,
            description=description,
        )

    @staticmethod
    def _is_unused(item: m.Infra.Census.Object) -> bool:
        return item.references_count == 0 and not item.name.startswith("_")

    @staticmethod
    def _is_test_only(item: m.Infra.Census.Object) -> bool:
        return (
            item.references_count > 0
            and item.runtime_references_count == 0
            and item.test_references_count == item.references_count
            and not item.name.startswith("_")
        )

    @classmethod
    def _removal_candidate(
        cls,
        item: m.Infra.Census.Object,
        *,
        include_unused: bool,
        include_test_only: bool,
    ) -> m.Infra.Census.RemovalCandidate | None:
        if include_unused and cls._is_unused(item):
            return m.Infra.Census.RemovalCandidate(
                project=item.project,
                object_name=item.name,
                object_kind=item.kind,
                file_path=item.file_path,
                line=item.line,
                scope_path=item.scope_path,
                reason="unused",
                suggested_action="delete_object_definition",
                runtime_reference_sites=item.runtime_reference_sites,
                test_reference_sites=item.test_reference_sites,
                example_reference_sites=item.example_reference_sites,
                script_reference_sites=item.script_reference_sites,
            )
        if include_test_only and cls._is_test_only(item):
            return m.Infra.Census.RemovalCandidate(
                project=item.project,
                object_name=item.name,
                object_kind=item.kind,
                file_path=item.file_path,
                line=item.line,
                scope_path=item.scope_path,
                reason="test_only",
                suggested_action="delete_object_and_test_references",
                runtime_reference_sites=item.runtime_reference_sites,
                test_reference_sites=item.test_reference_sites,
                example_reference_sites=item.example_reference_sites,
                script_reference_sites=item.script_reference_sites,
            )
        return None

    @staticmethod
    def _object_key(item: m.Infra.Census.Object) -> str:
        return f"{item.file_path}:{item.line}:{item.scope_path}:{item.kind}"

    @staticmethod
    def _fix_key(file_path: Path, object_name: str) -> str:
        return f"{file_path.resolve()}::{object_name}"

    @classmethod
    def _impact_map_results(
        cls,
        report: m.Infra.Census.WorkspaceReport,
    ) -> tuple[m.Infra.Result, ...]:
        changes_by_file: dict[Path, list[str]] = defaultdict(list)
        for candidate in report.removal_candidates:
            source_path = Path(candidate.file_path)
            cls._append_impact_change(
                changes_by_file,
                source_path,
                f"{candidate.suggested_action}: {candidate.object_name} ({candidate.reason})",
            )
            for site in cls._reference_sites(candidate):
                cls._append_impact_change(
                    changes_by_file,
                    Path(site.file_path),
                    f"remove reference to {candidate.object_name} at line {site.line} ({site.surface})",
                )
        return tuple(
            m.Infra.Result(
                file_path=file_path,
                success=True,
                modified=True,
                changes=tuple(changes_by_file[file_path]),
            )
            for file_path in sorted(changes_by_file, key=lambda item: item.as_posix())
        )

    @staticmethod
    def _append_impact_change(
        changes_by_file: dict[Path, list[str]],
        file_path: Path,
        change: str,
    ) -> None:
        normalized_path = file_path.resolve()
        if change not in changes_by_file[normalized_path]:
            changes_by_file[normalized_path].append(change)

    @staticmethod
    def _reference_sites(
        candidate: m.Infra.Census.RemovalCandidate,
    ) -> tuple[m.Infra.Census.ReferenceSite, ...]:
        return (
            *candidate.test_reference_sites,
            *candidate.runtime_reference_sites,
            *candidate.example_reference_sites,
            *candidate.script_reference_sites,
        )


__all__: list[str] = ["FlextInfraRefactorCensus"]
