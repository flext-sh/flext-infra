"""Workspace-wide Rope-only census orchestration."""

from __future__ import annotations

import contextlib
import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Annotated, ClassVar, override

from rope.base.exceptions import RopeError

from flext_cli import cli
from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraCompatibilityAliasDetector,
    FlextInfraManualTypingAliasDetector,
    FlextInfraMROCompletenessDetector,
    FlextInfraProjectSelectionServiceBase,
    FlextInfraRopeWorkspace,
    FlextInfraRuntimeAliasDetector,
    c,
    m,
    p,
    r,
    t,
    u,
)
from flext_infra._models.census import FlextInfraModelsCensus

_ROPE_SAFE_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RecursionError,
    SyntaxError,
    ValueError,
    RuntimeError,
    RopeError,
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

    @staticmethod
    def _render_workspace_report(report: m.Infra.Census.WorkspaceReport) -> str:
        """Render workspace census report from typed model fields."""
        lines = [
            "Workspace Census Report",
            f"Objects: {report.total_objects}",
            f"Violations: {report.total_violations}",
            f"Fixable: {report.total_fixable}",
            f"Fixes: {report.fixes_total}",
            f"Unused: {report.unused_count}",
            f"Test-only: {report.test_only_count}",
            f"Removal candidates: {report.removal_candidate_count}",
            f"Duplicate groups: {len(report.duplicates)}",
            f"Duration: {report.scan_duration_seconds:.2f}s",
            "",
        ]
        lines.extend(
            "- "
            f"{project.project}: "
            f"objects={project.objects_total} "
            f"violations={project.violations_total} "
            f"unused={project.unused_count} "
            f"test-only={project.test_only_count} "
            f"candidates={project.removal_candidate_count}"
            for project in report.projects
        )
        if report.removal_candidates:
            lines.extend(("", "Candidate preview:"))
            for candidate in report.removal_candidates[:10]:
                reference_groups = (
                    candidate.test_reference_sites,
                    candidate.runtime_reference_sites,
                    candidate.example_reference_sites,
                    candidate.script_reference_sites,
                )
                reference_preview = next(
                    (
                        ", ".join(f"{site.file_path}:{site.line}" for site in group[:3])
                        for group in reference_groups
                        if group
                    ),
                    "",
                )
                lines.append(
                    "- "
                    f"{candidate.reason} "
                    f"{candidate.object_name} "
                    f"@ {candidate.file_path}:{candidate.line}"
                    + (f" refs={reference_preview}" if reference_preview else "")
                )
        return "\n".join(lines)

    @staticmethod
    def render_text(report: m.Infra.Census.WorkspaceReport) -> str:
        """Render the canonical workspace census report."""
        return FlextInfraRefactorCensus._render_workspace_report(report)

    @override
    def execute(self) -> p.Result[m.Infra.Census.WorkspaceReport]:
        """Execute the census with one shared Rope session."""
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
        report = report.model_copy(
            update={"scan_duration_seconds": time.monotonic() - started}
        )
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
        selected_families = self._selected_families(family_names)
        project_objects: dict[str, list[m.Infra.Census.Object]] = defaultdict(list)
        project_violations: dict[str, list[m.Infra.Census.Violation]] = defaultdict(
            list
        )
        project_fixes: dict[str, list[m.Infra.Census.Fix]] = defaultdict(list)
        for module in rope.modules(project_names=project_names):
            try:
                module_objects = tuple(
                    rope.objects(
                        module.file_path,
                        include_local_scopes=include_local_scopes,
                    )
                )
            except _ROPE_SAFE_EXCEPTIONS:
                continue
            project = (
                module_objects[0].project
                if module_objects
                else module.project_root.name
                if module.project_root is not None
                else ""
            )
            if not project:
                continue
            objects = tuple(
                item
                for item in module_objects
                if self._include_object(
                    item,
                    kind_names=kind_names,
                    selected_families=selected_families,
                )
            )
            if objects:
                project_objects[project].extend(objects)
            try:
                violations, fixes = self._module_rules(
                    rope,
                    module.file_path,
                    objects=module_objects,
                    project_name=project,
                    applied=applied,
                    kind_names=kind_names,
                    rule_names=rule_names,
                )
            except _ROPE_SAFE_EXCEPTIONS:
                continue
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
        project_names = tuple(
            sorted(
                set(project_objects) | set(project_violations) | set(project_fixes),
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
            )
            for project in project_names
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

    def _validated_project_reports(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        project_reports: tuple[m.Infra.Census.ProjectReport, ...],
    ) -> tuple[m.Infra.Census.ProjectReport, ...]:
        """Keep only removal candidates that pass the configured dry-run gates."""
        validated_reports: list[m.Infra.Census.ProjectReport] = []
        for report in project_reports:
            if not report.removal_candidates:
                validated_reports.append(report)
                continue
            validated_candidates = tuple(
                candidate
                for candidate in report.removal_candidates
                if u.Infra.preview_simple_removal_candidate(
                    rope,
                    self.root,
                    candidate,
                    gates=self.dry_run_gate_names,
                ).unwrap_or(False)
            )
            validated_reports.append(
                report.model_copy(
                    update={
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
        objects: tuple[m.Infra.Census.Object, ...],
        project_name: str,
        applied: frozenset[str],
        kind_names: t.StrSequence | None,
        rule_names: t.StrSequence | None,
    ) -> tuple[tuple[m.Infra.Census.Violation, ...], tuple[m.Infra.Census.Fix, ...]]:
        convention = rope.convention(file_path)
        ctx = self._detector_context(rope, file_path)
        selected_kinds = frozenset(kind_names) if kind_names else frozenset()
        violations: list[m.Infra.Census.Violation] = []
        fixes: list[m.Infra.Census.Fix] = []

        if self._include_rule("runtime_alias", rule_names=rule_names):
            runtime_target = self._runtime_alias_target(convention, objects)
            for detector_violation in FlextInfraRuntimeAliasDetector.detect_file(ctx):
                object_name = (
                    runtime_target.name
                    if runtime_target is not None
                    else detector_violation.alias
                )
                object_kind = (
                    runtime_target.kind if runtime_target is not None else "assignment"
                )
                if selected_kinds and object_kind not in selected_kinds:
                    continue
                line = detector_violation.line or (
                    runtime_target.line if runtime_target is not None else 0
                )
                fixable = runtime_target is not None
                action = "rewrite_runtime_alias" if fixable else ""
                violations.append(
                    self._raw_violation(
                        project=project_name,
                        object_name=object_name,
                        object_kind=object_kind,
                        kind="runtime_alias",
                        file_path=file_path,
                        line=line,
                        description=detector_violation.detail,
                        fixable=fixable,
                        fix_action=action,
                    )
                )
                if fixable:
                    fixes.append(
                        m.Infra.Census.Fix(
                            object_name=object_name,
                            action=action,
                            source_file=str(file_path),
                            files_changed=1,
                            applied=self._fix_key(file_path, object_name, action)
                            in applied,
                        )
                    )

        if self._include_rule("manual_typing_alias", rule_names=rule_names):
            for detector_violation in FlextInfraManualTypingAliasDetector.detect_file(
                ctx,
            ):
                matched = self._named_object(objects, detector_violation.name)
                object_kind = matched.kind if matched is not None else "assignment"
                if selected_kinds and object_kind not in selected_kinds:
                    continue
                action = (
                    "rewrite_manual_typing_alias"
                    if ctx.project_root is not None
                    else ""
                )
                violations.append(
                    self._raw_violation(
                        project=project_name,
                        object_name=detector_violation.name,
                        object_kind=object_kind,
                        kind="manual_typing_alias",
                        file_path=file_path,
                        line=detector_violation.line,
                        description=detector_violation.detail,
                        fixable=bool(action),
                        fix_action=action,
                    )
                )
                if action:
                    fixes.append(
                        m.Infra.Census.Fix(
                            object_name=detector_violation.name,
                            action=action,
                            source_file=str(file_path),
                            target_file=str(
                                convention.package_dir / c.Infra.TYPINGS_PY
                            ),
                            files_changed=2,
                            applied=self._fix_key(
                                file_path,
                                detector_violation.name,
                                action,
                            )
                            in applied,
                        )
                    )

        if self._include_rule("compatibility_alias", rule_names=rule_names):
            for detector_violation in FlextInfraCompatibilityAliasDetector.detect_file(
                ctx,
            ):
                matched = self._named_object(objects, detector_violation.alias_name)
                object_kind = matched.kind if matched is not None else "assignment"
                if selected_kinds and object_kind not in selected_kinds:
                    continue
                action = "rewrite_compatibility_alias"
                violations.append(
                    self._raw_violation(
                        project=project_name,
                        object_name=detector_violation.alias_name,
                        object_kind=object_kind,
                        kind="compatibility_alias",
                        file_path=file_path,
                        line=detector_violation.line,
                        description=(
                            "Compatibility alias "
                            f"'{detector_violation.alias_name}' should use "
                            f"'{detector_violation.target_name}' directly"
                        ),
                        fixable=True,
                        fix_action=action,
                    )
                )
                fixes.append(
                    m.Infra.Census.Fix(
                        object_name=detector_violation.alias_name,
                        action=action,
                        source_file=str(file_path),
                        files_changed=1,
                        applied=self._fix_key(
                            file_path,
                            detector_violation.alias_name,
                            action,
                        )
                        in applied,
                    )
                )

        if self._include_rule("mro_completeness", rule_names=rule_names):
            parse_failures: list[m.Infra.ParseFailureViolation] = []
            mro_ctx = self._detector_context(
                rope,
                file_path,
                parse_failures=parse_failures,
            )
            for detector_violation in FlextInfraMROCompletenessDetector.detect_file(
                mro_ctx,
            ):
                matched = self._named_object(objects, detector_violation.facade_class)
                object_kind = matched.kind if matched is not None else "class"
                if selected_kinds and object_kind not in selected_kinds:
                    continue
                action = "rewrite_mro_completeness"
                violations.append(
                    self._raw_violation(
                        project=project_name,
                        object_name=detector_violation.facade_class,
                        object_kind=object_kind,
                        kind="mro_completeness",
                        file_path=file_path,
                        line=(
                            matched.line
                            if matched is not None
                            else detector_violation.line
                        ),
                        description=detector_violation.suggestion,
                        fixable=True,
                        fix_action=action,
                    )
                )
                fixes.append(
                    m.Infra.Census.Fix(
                        object_name=detector_violation.facade_class,
                        action=action,
                        source_file=str(file_path),
                        files_changed=1,
                        applied=self._fix_key(
                            file_path,
                            detector_violation.facade_class,
                            action,
                        )
                        in applied,
                    )
                )

        return (tuple(violations), tuple(fixes))

    def _apply_supported_fixes(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        report: m.Infra.Census.WorkspaceReport,
    ) -> frozenset[str]:
        applied: set[str] = set()
        touched_paths: set[Path] = set()
        requested_fixes: dict[tuple[Path, str], set[str]] = defaultdict(set)
        for project in report.projects:
            for fix in project.fixes:
                requested_fixes[Path(fix.source_file), fix.action].add(
                    fix.object_name,
                )
        for (file_path, action), object_names in requested_fixes.items():
            parse_failures: list[m.Infra.ParseFailureViolation] = []
            ctx = self._detector_context(
                rope,
                file_path,
                parse_failures=parse_failures,
            )
            changed = False
            if action == "rewrite_runtime_alias":
                violations = FlextInfraRuntimeAliasDetector.detect_file(ctx)
                if not violations:
                    continue
                u.Infra.rewrite_runtime_alias_violations(py_files=(file_path,))
                changed = True
            elif action == "rewrite_manual_typing_alias":
                if ctx.project_root is None:
                    continue
                violations = tuple(
                    violation
                    for violation in FlextInfraManualTypingAliasDetector.detect_file(
                        ctx,
                    )
                    if violation.name in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_manual_typing_alias_violations(
                    project_root=ctx.project_root,
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_compatibility_alias":
                violations = tuple(
                    violation
                    for violation in FlextInfraCompatibilityAliasDetector.detect_file(
                        ctx,
                    )
                    if violation.alias_name in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_compatibility_alias_violations(
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_mro_completeness":
                violations = tuple(
                    violation
                    for violation in FlextInfraMROCompletenessDetector.detect_file(
                        ctx,
                    )
                    if violation.facade_class in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_mro_completeness_violations(
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            if not changed:
                continue
            touched_paths.add(file_path.resolve())
            applied.update(
                self._fix_key(file_path, object_name, action)
                for object_name in object_names
            )
        for candidate in report.removal_candidates:
            if u.Infra.apply_simple_removal_candidate(
                rope,
                self.root,
                candidate,
                gates=self.dry_run_gate_names,
            ):
                applied.add(
                    self._fix_key(Path(candidate.file_path), candidate.object_name)
                )
                touched_paths.add(Path(candidate.file_path).resolve())
                touched_paths.update(
                    Path(site.file_path).resolve()
                    for site in (
                        *candidate.test_reference_sites,
                        *candidate.example_reference_sites,
                        *candidate.script_reference_sites,
                    )
                )
        if applied:
            self._regenerate_inits_via_codegen()
            self._ruff_fix_touched_files(touched_paths)
            rope.reload()
        return frozenset(applied)

    @staticmethod
    def _ruff_fix_touched_files(paths: Iterable[Path]) -> None:
        """Run ``ruff format`` + ``ruff check --fix`` on cascade/cosmetic rules only.

        Normalises trailing newlines (W391) and import sort (I001) left
        behind after candidate removal. Scope is deliberately narrow:
        ``--select I,W`` — not ``F`` or ``E`` — so that unused-import
        removal does not fight the lazy-init ``TYPE_CHECKING`` re-exports
        produced by ``FlextInfraCodegenLazyInit``. Failures are swallowed
        so apply remains successful even if cosmetic cleanup cannot run.
        """
        existing = sorted({str(path) for path in paths if path.is_file()})
        if not existing:
            return
        with contextlib.suppress(Exception):
            u.Cli.run_raw(
                ["ruff", "check", "--fix", "--select", "I,W", *existing],
                timeout=c.Infra.TIMEOUT_SHORT,
            )
        with contextlib.suppress(Exception):
            u.Cli.run_raw(["ruff", "format", *existing], timeout=c.Infra.TIMEOUT_SHORT)

    def _regenerate_inits_via_codegen(self) -> None:
        """Regenerate every ``__init__.py`` via the canonical lazy-init service."""
        FlextInfraCodegenLazyInit(workspace=self.root).generate_inits(
            check_only=False,
        )

    @staticmethod
    def _regenerate_inits_for_workspace(workspace: Path) -> None:
        """Post-apply hook that regenerates ``__init__.py`` for ``workspace``."""
        FlextInfraCodegenLazyInit(workspace=workspace).generate_inits(
            check_only=False,
        )

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
        duplicates: list[FlextInfraModelsCensus.Census.DuplicateGroup] = []
        for key in sorted(groups):
            definitions = groups[key]
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
    def _named_object(
        objects: tuple[m.Infra.Census.Object, ...],
        name: str,
    ) -> m.Infra.Census.Object | None:
        return next(
            (item for item in objects if name in {item.scope_path, item.name}),
            None,
        )

    @staticmethod
    def _detector_context(
        rope: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
        *,
        parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation]
        | None = None,
    ) -> m.Infra.DetectorContext:
        convention = rope.convention(file_path)
        layout = convention.project_layout
        module_entry = rope.module(file_path)
        project_root = (
            layout.project_root
            if layout is not None
            else module_entry.project_root
            if module_entry is not None
            else None
        )
        project_name = (
            layout.project_name
            if layout is not None
            else project_root.name
            if project_root is not None
            else ""
        )
        return m.Infra.DetectorContext(
            file_path=file_path,
            rope_project=rope.rope_project,
            parse_failures=parse_failures,
            project_name=project_name,
            project_root=project_root,
        )

    @staticmethod
    def _runtime_alias_target(
        convention: m.Infra.RopeModuleConvention,
        objects: tuple[m.Infra.Census.Object, ...],
    ) -> m.Infra.Census.Object | None:
        layout = convention.project_layout
        family = convention.module_policy.expected_family or ""
        if layout is None or not family:
            return None
        return FlextInfraRefactorCensus._named_object(
            objects,
            f"{layout.class_stem}{family}",
        )

    @staticmethod
    def _raw_violation(
        *,
        project: str,
        object_name: str,
        object_kind: str,
        kind: str,
        file_path: Path,
        line: int,
        description: str,
        fixable: bool = False,
        fix_action: str = "",
    ) -> m.Infra.Census.Violation:
        return m.Infra.Census.Violation(
            project=project,
            object_name=object_name,
            object_kind=object_kind,
            kind=kind,
            file_path=str(file_path),
            line=line,
            fixable=fixable,
            fix_action=fix_action,
            description=description,
        )

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
        return FlextInfraRefactorCensus._raw_violation(
            project=item.project,
            object_name=item.name,
            object_kind=item.kind,
            kind=kind,
            file_path=Path(item.file_path),
            line=item.line,
            description=description,
            fixable=fixable,
            fix_action=fix_action,
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
            reason, suggested_action = "unused", "delete_object_definition"
        elif include_test_only and cls._is_test_only(item):
            reason, suggested_action = (
                "test_only",
                "delete_object_and_test_references",
            )
        else:
            return None
        return m.Infra.Census.RemovalCandidate(
            project=item.project,
            object_name=item.name,
            object_kind=item.kind,
            file_path=item.file_path,
            line=item.line,
            scope_path=item.scope_path,
            reason=reason,
            suggested_action=suggested_action,
            runtime_reference_sites=item.runtime_reference_sites,
            test_reference_sites=item.test_reference_sites,
            example_reference_sites=item.example_reference_sites,
            script_reference_sites=item.script_reference_sites,
        )

    @staticmethod
    def _object_key(item: m.Infra.Census.Object) -> str:
        return f"{item.file_path}:{item.line}:{item.scope_path}:{item.kind}"

    @staticmethod
    def _fix_key(file_path: Path, object_name: str, action: str = "") -> str:
        suffix = f"::{action}" if action else ""
        return f"{file_path.resolve()}::{object_name}{suffix}"

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

    @staticmethod
    def _is_flext_owned(value: p.ModuleOwned) -> bool:
        """Return True iff `value`'s defining module is in the flext package tree.

        Used to filter the parent inventory so that builtin attributes
        inherited by str/int/dict/list constants do not pollute collision
        candidates with names like `count`, `index`, `replace`, etc.
        """
        module_name = getattr(value, "__module__", "")
        if not isinstance(module_name, str):
            return False
        return module_name.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)

    @classmethod
    def _build_parent_inventory(
        cls,
        workspace_root: Path,
    ) -> t.MappingKV[str, t.StrSequence]:
        """Inventory governed-package alias top-level facade names.

        Discovers governed projects via ``u.Infra.projects(workspace_root)``
        (canonical workspace project discovery — SSOT). For each project
        whose hyphenated name converts to a Python package, imports the
        package and walks dynamic facade aliases at depth 1
        (top-level facade attributes such as ``flext_core.c.Result``).

        Returns ``{symbol_name: (parent_path, ...)}`` so a consumer-defined
        symbol with the same name can be cross-referenced against every
        parent that declares it.

        Only ``type`` instances (classes) are inventoried; method names
        inherited from ABCs (``clear``, ``get``, …) are skipped — every
        mapping class shares them, so they are not collision candidates.

        Filters out attributes whose values' ``__module__`` is not in the
        flext package tree.

        Read-only runtime introspection — NO Rope, NO source-tree walking,
        NO subprocess. Skips packages that fail to import (sub-repo
        environments may not have every flext-* installed).
        """
        projects_result = u.Infra.projects(workspace_root)
        if projects_result.failure:
            return {}
        inventory: dict[str, list[str]] = defaultdict(list)
        for project in projects_result.unwrap():
            pkg_name = project.name.replace("-", "_")
            try:
                module = __import__(pkg_name)
            except ImportError:
                continue
            for alias_name in u.read_project_constants(pkg_name).FACADE_ALIAS_NAMES:
                alias = getattr(module, alias_name, None)
                if alias is None:
                    continue
                for attr in dir(alias):
                    if attr.startswith("_"):
                        continue
                    nested = getattr(alias, attr, None)
                    if (
                        nested is None
                        or not isinstance(nested, p.ModuleOwned)
                        or not cls._is_flext_owned(nested)
                    ):
                        continue
                    if not isinstance(nested, type):
                        continue
                    inventory[attr].append(f"{pkg_name}.{alias_name}.{attr}")
        return {name: tuple(paths) for name, paths in inventory.items()}

    @classmethod
    def parent_alias_collisions(
        cls,
        report: m.Infra.Census.WorkspaceReport,
        *,
        workspace_root: Path,
    ) -> tuple[tuple[m.Infra.Census.Object, t.StrSequence], ...]:
        """Cross-reference workspace objects against upstream parent inventory.

        Returns ``(symbol, parent_paths)`` pairs where the consumer's
        public symbol name appears on at least one governed parent
        package's dynamically derived facade aliases. Sorted descending by the number of
        matching parent paths (broadest collision surface first).

        Self-references are filtered: a symbol in project ``flext-core``
        whose name matches a symbol on ``flext_core.<alias>.<name>`` is
        the canonical owner, not a duplicate.

        Args:
            report: A ``WorkspaceReport`` produced by ``execute()`` or
                ``_collect_report(...)``. Reusing the existing report
                avoids a second Rope-walk; the inventory is the only new
                I/O.
            workspace_root: Workspace root used to discover governed
                projects (parent packages).

        Returns:
            Tuple of ``(symbol, parent_paths)`` pairs. Empty tuple if
            no collisions are found.

        """
        inventory = cls._build_parent_inventory(workspace_root)
        collisions: list[tuple[m.Infra.Census.Object, t.StrSequence]] = []
        for project_report in report.projects:
            self_pkg_prefix = f"{project_report.project.replace('-', '_')}."
            for obj in project_report.objects:
                if obj.name.startswith("_"):
                    continue
                parent_paths = inventory.get(obj.name)
                if not parent_paths:
                    continue
                foreign_paths = tuple(
                    path
                    for path in parent_paths
                    if not path.startswith(self_pkg_prefix)
                )
                if not foreign_paths:
                    continue
                collisions.append((obj, foreign_paths))
        collisions.sort(key=lambda entry: -len(entry[1]))
        return tuple(collisions)


__all__: list[str] = ["FlextInfraRefactorCensus"]
