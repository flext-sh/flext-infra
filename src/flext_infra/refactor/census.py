"""Workspace-wide Rope-only census orchestration."""

from __future__ import annotations

import contextlib
import time
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_cli import cli
from rope.base.exceptions import RopeError

from flext_infra import (
    FlextInfraCodegenLazyInit,
    FlextInfraProjectSelectionServiceBase,
    FlextInfraRopeWorkspace,
    c,
    m,
    p,
    r,
    t,
    u,
)

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
    def render_text(report: m.Infra.Census.WorkspaceReport) -> str:
        """Render the canonical workspace census report."""
        data = report.model_dump(mode="json")
        if "total_objects" in data:
            projects = data.get("projects", [])
            duplicates = data.get("duplicates", [])
            candidates = data.get("removal_candidates", [])
            lines = [
                "Workspace Census Report",
                f"Objects: {int(data.get('total_objects', 0))}",
                f"Violations: {int(data.get('total_violations', 0))}",
                f"Fixable: {int(data.get('total_fixable', 0))}",
                f"Fixes: {int(data.get('fixes_total', 0))}",
                f"Unused: {int(data.get('unused_count', 0))}",
                f"Test-only: {int(data.get('test_only_count', 0))}",
                f"Removal candidates: {int(data.get('removal_candidate_count', 0))}",
                f"Duplicate groups: {len(duplicates) if isinstance(duplicates, list) else 0}",
                f"Duration: {float(data.get('scan_duration_seconds', 0.0)):.2f}s",
                "",
            ]
            if isinstance(projects, list):
                for project in projects:
                    if not isinstance(project, Mapping):
                        continue
                    project_name = str(project.get("project", ""))
                    if not project_name:
                        continue
                    lines.append(
                        "- "
                        f"{project_name}: "
                        f"objects={int(project.get('objects_total', 0))} "
                        f"violations={int(project.get('violations_total', 0))} "
                        f"unused={int(project.get('unused_count', 0))} "
                        f"test-only={int(project.get('test_only_count', 0))} "
                        f"candidates={int(project.get('removal_candidate_count', 0))}"
                    )
            if isinstance(candidates, list) and candidates:
                lines.extend(("", "Candidate preview:"))
                for candidate in candidates[:10]:
                    if not isinstance(candidate, Mapping):
                        continue
                    reference_groups = (
                        candidate.get("test_reference_sites", []),
                        candidate.get("runtime_reference_sites", []),
                        candidate.get("example_reference_sites", []),
                        candidate.get("script_reference_sites", []),
                    )
                    reference_preview = ""
                    for group in reference_groups:
                        if not isinstance(group, list) or not group:
                            continue
                        preview_sites: list[str] = []
                        for site in group[:3]:
                            if not isinstance(site, Mapping):
                                continue
                            site_path = str(site.get("file_path", ""))
                            site_line = int(site.get("line", 0))
                            preview_sites.append(f"{site_path}:{site_line}")
                        if preview_sites:
                            reference_preview = ", ".join(preview_sites)
                            break
                    lines.append(
                        "- "
                        f"{candidate.get('reason', 'candidate')!s} "
                        f"{candidate.get('object_name', '')!s} "
                        f"@ {candidate.get('file_path', '')!s}:{int(candidate.get('line', 0))}"
                        + (f" refs={reference_preview}" if reference_preview else "")
                    )
            return "\n".join(lines)
        totals = {
            "classes": data.get("total_classes", 0),
            "methods": data.get("total_methods", 0),
            "usages": data.get("total_usages", 0),
            "unused": data.get("total_unused", 0),
            "files_scanned": data.get("files_scanned", 0),
            "parse_errors": data.get("parse_errors", 0),
        }
        lines = [
            "Utilities Census Report",
            f"Classes: {totals['classes']}",
            f"Methods: {totals['methods']}",
            f"Usages: {totals['usages']}",
            f"Unused: {totals['unused']}",
            f"Files scanned: {totals['files_scanned']}",
            f"Parse errors: {totals['parse_errors']}",
            "",
        ]
        projects = data.get("projects", [])
        if isinstance(projects, list):
            for project in projects:
                if isinstance(project, Mapping):
                    project_name = str(
                        project.get("project", project.get("project_name", ""))
                    )
                    total = int(project.get("total", 0))
                    if project_name:
                        lines.append(f"- {project_name}: {total}")
        return "\n".join(lines)

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
            objects = tuple(
                item
                for item in module_objects
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
            try:
                violations, fixes = self._module_rules(
                    rope,
                    module.file_path,
                    objects=objects,
                    applied=applied,
                )
            except _ROPE_SAFE_EXCEPTIONS:
                continue
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
                )
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
        touched_paths: set[Path] = set()
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
                touched_paths.add(file_path.resolve())
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
        duplicates = []
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

    @staticmethod
    def _is_flext_owned(value: object) -> bool:
        """Return True iff `value`'s defining module is in the flext package tree.

        Used to filter the parent inventory so that builtin attributes
        inherited by str/int/dict/list constants do not pollute collision
        candidates with names like `count`, `index`, `replace`, etc.
        """
        module_name = getattr(value, "__module__", None)
        if not isinstance(module_name, str):
            return False
        return module_name.startswith("flext_")

    @classmethod
    def _build_parent_inventory(
        cls,
        workspace_root: Path,
    ) -> Mapping[str, t.StrSequence]:
        """Inventory governed-package alias top-level facade names.

        Discovers governed projects via ``u.Infra.projects(workspace_root)``
        (canonical workspace project discovery — SSOT). For each project
        whose hyphenated name converts to a Python package, imports the
        package and walks ``c.FACADE_ALIAS_NAMES`` aliases at depth 1
        (top-level facade attributes — e.g. ``flext_core.c.Result``).

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
            for alias_name in c.FACADE_ALIAS_NAMES:
                alias = getattr(module, alias_name, None)
                if alias is None:
                    continue
                for attr in dir(alias):
                    if attr.startswith("_"):
                        continue
                    nested = getattr(alias, attr, None)
                    if nested is None or not cls._is_flext_owned(nested):
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

        Returns ``(object, parent_paths)`` pairs where the consumer's
        public symbol name appears on at least one governed parent
        package's facade alias (``c/m/p/t/u`` per
        ``c.FACADE_ALIAS_NAMES``). Sorted descending by the number of
        matching parent paths (broadest collision surface first).

        Self-references are filtered: an object in project ``flext-core``
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
            Tuple of ``(object, parent_paths)`` pairs. Empty tuple if
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
