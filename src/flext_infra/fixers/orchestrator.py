"""Catalog-driven enforcement fix orchestrator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
from collections import defaultdict
from types import SimpleNamespace
from typing import TYPE_CHECKING, Annotated, ClassVar, override

from flext_core import FlextUtilitiesEnforcement, r
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.constants import c
from flext_infra.fixers.gate_fixer import FlextInfraGateFixerAdapter
from flext_infra.fixers.manual_fixer import FlextInfraManualFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.fixers.rope_fixer import FlextInfraRopeFixerAdapter
from flext_infra.fixers.transformer_fixer import FlextInfraTransformerFixerAdapter
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor.declarative_enforcement import (
    FlextInfraRefactorDeclarativeEnforcement,
)
from flext_infra.typings import t
from flext_infra.utilities import u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_core._models.enforcement import FlextModelsEnforcement as me
    from flext_infra.fixers.base import FlextInfraFixerAdapter


class FlextInfraEnforcementFixerOrchestrator(
    FlextInfraProjectSelectionServiceBase[str],
):
    """Apply automatic fixes for enforcement-catalog rules across workspace projects.

    The orchestrator reads the canonical enforcement catalog from flext-core,
    keeps only rules that declare a ``fix_action``, collects violations for
    those rules using the same validators/detectors that the pytest dispatcher
    uses, and routes each violation to the appropriate adapter.
    """

    _ADAPTER_CLASSES: ClassVar[tuple[type[FlextInfraFixerAdapter], ...]] = (
        FlextInfraGateFixerAdapter,
        FlextInfraManualFixerAdapter,
        FlextInfraRopeFixerAdapter,
        FlextInfraTransformerFixerAdapter,
    )

    apply: Annotated[
        bool,
        m.Field(description="Apply fixes instead of dry-run preview"),
    ] = False
    rules: Annotated[
        tuple[str, ...],
        m.Field(description="Enforcement rule IDs to fix"),
    ] = ()
    safe_only: Annotated[
        bool,
        m.Field(description="Only apply fixes marked safe in the catalog"),
    ] = True
    check_after: Annotated[
        bool,
        m.Field(description="Re-run the corresponding check after fixing"),
    ] = True

    @classmethod
    @override
    def execute_command(
        cls,
        params: m.Infra.FixEnforcementCommand,
    ) -> p.Result[str]:
        """Execute enforcement fixes from the canonical CLI payload."""
        instance = cls.model_validate(
            {
                "workspace_root": params.workspace_path,
                "selected_projects": params.projects,
                "apply": params.apply,
                "rules": params.rules,
                "safe_only": params.safe_only,
                "check_after": params.check_after,
                "fail_fast": params.fail_fast,
            },
        )
        return instance.execute()

    @override
    def execute(self) -> p.Result[str]:
        """Run the enforcement fix pipeline and return a human-readable report."""
        catalog = FlextUtilitiesEnforcement.build_canonical_catalog()
        try:
            selected_rules = self._selected_rules(catalog)
        except ValueError as exc:
            return r[str].fail(str(exc))
        if not selected_rules:
            return r[str].ok("No fixable enforcement rules selected.")
        projects = self._resolve_projects()
        if projects.failure:
            return r[str].fail(projects.error or "unable to resolve projects")
        all_results: list[fr.ProjectFixResult] = []
        for project in projects.value:
            project_result = self._fix_project(project, selected_rules)
            all_results.extend(project_result)
        report = self._render_report(all_results)
        if any(result.failed for result in all_results):
            return r[str].fail(report)
        return r[str].ok(report)

    def _selected_rules(
        self,
        catalog: me.EnforcementCatalog,
    ) -> tuple[me.EnforcementRuleSpec, ...]:
        """Return enabled rules with fix actions matching the CLI filter.

        In the default mode (no explicit ``--rules``), adapterless fix actions
        stay selected so the routing phase emits a failed fix instead of
        silently hiding an unsupported catalog contract. When ``--rules`` is
        used, every requested rule must be enabled, declare a fix action, and
        have an available adapter; otherwise a ``ValueError`` is raised so the
        caller can surface a clear failure.
        """
        wanted = frozenset(self.rules) if self.rules else frozenset()
        candidates: list[me.EnforcementRuleSpec] = []
        for rule in catalog.enabled_rules():
            if not rule.fix_action:
                continue
            if wanted and rule.id not in wanted:
                continue
            candidates.append(rule)

        if wanted:
            requested_ids = {rule.id for rule in candidates}
            unrequestable = wanted - requested_ids
            if unrequestable:
                unrequestable_msg = (
                    "Requested rules are not enabled or have no fix action: "
                    f"{', '.join(sorted(unrequestable))}"
                )
                raise ValueError(unrequestable_msg)
            if self.safe_only:
                unsafe = {
                    rule.id
                    for rule in candidates
                    if rule.fix_action is not None and not rule.fix_action.safe
                }
                if unsafe:
                    unsafe_msg = (
                        "Requested rules are unsafe under --safe-only: "
                        f"{', '.join(sorted(unsafe))}"
                    )
                    raise ValueError(unsafe_msg)
            adapterless = {
                rule.id for rule in candidates if not self._has_adapter(rule)
            }
            if adapterless:
                adapterless_msg = (
                    "Requested rules have no available fixer adapter: "
                    f"{', '.join(sorted(adapterless))}"
                )
                raise ValueError(adapterless_msg)

        results: list[me.EnforcementRuleSpec] = []
        for rule in candidates:
            fix_action = rule.fix_action
            if fix_action is None:
                continue
            if self.safe_only and not fix_action.safe:
                continue
            results.append(rule)
        return tuple(results)

    def _has_adapter(self, rule: me.EnforcementRuleSpec) -> bool:
        """Return whether ``rule`` has a registered fixer adapter."""
        fix_action = rule.fix_action
        if fix_action is None:
            return False
        return self._adapter_for(fix_action) is not None

    def _resolve_projects(
        self,
    ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
        """Resolve the project list from CLI selection or workspace discovery."""
        projects_result = u.Infra.projects(self.workspace_root)
        if projects_result.failure:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].fail(
                projects_result.error or "workspace discovery failed",
            )
        discovered = tuple(projects_result.unwrap())
        scope = frozenset(self.project_names or ())
        available_names = {
            name
            for project in discovered
            for name in (project.name, project.path.name)
            if name
        }
        missing = scope - available_names
        if missing:
            return r[t.SequenceOf[p.Infra.ProjectInfo]].fail(
                f"Requested projects were not discovered: {', '.join(sorted(missing))}",
            )
        selected = (
            tuple(p for p in discovered if p.name in scope or p.path.name in scope)
            if scope
            else discovered
        )
        return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(selected)

    def _fix_project(
        self,
        project: p.Infra.ProjectInfo,
        rules: t.SequenceOf[me.EnforcementRuleSpec],
    ) -> t.SequenceOf[fr.ProjectFixResult]:
        """Collect violations and apply fixes for one project."""
        project_dir = project.path
        results: list[fr.ProjectFixResult] = []
        by_adapter, unhandled = self._group_by_adapter(rules)
        if unhandled:
            results.append(
                fr.ProjectFixResult(
                    project=project_dir.name,
                    failed=tuple(
                        self._collection_failure(
                            project_dir,
                            rule,
                            "no registered fixer adapter for "
                            f"{rule.fix_action.kind if rule.fix_action else 'none'}:"
                            f"{rule.fix_action.target if rule.fix_action else 'none'}",
                        )
                        for rule in unhandled
                    ),
                ),
            )
            if self.fail_fast:
                return tuple(results)
        for adapter_cls, adapter_rules in by_adapter.items():
            adapter = self._instantiate_adapter(adapter_cls)
            violations, failures = self._collect_violations(
                project_dir=project_dir,
                rules=adapter_rules,
            )
            if failures:
                results.append(
                    fr.ProjectFixResult(
                        project=project_dir.name,
                        failed=tuple(failures),
                    ),
                )
                if self.fail_fast:
                    return tuple(results)
            if not violations:
                continue
            try:
                result = adapter.fix_project(
                    project_dir,
                    violations,
                    self._command_ctx(),
                )
            except c.EXC_BROAD_RUNTIME as exc:
                rule_id = violations[0][0].id
                results.append(
                    fr.ProjectFixResult(
                        project=project_dir.name,
                        failed=(
                            fr.FailedFix(
                                rule_id=rule_id,
                                file_path=str(project_dir),
                                error=(
                                    f"{adapter_cls.__name__} failed: "
                                    f"{type(exc).__name__}: {exc}"
                                ),
                            ),
                        ),
                    ),
                )
                if self.fail_fast:
                    return tuple(results)
                continue
            results.append(result)
            if result.failed and self.fail_fast:
                return tuple(results)
        return tuple(results)

    def _group_by_adapter(
        self,
        rules: t.SequenceOf[me.EnforcementRuleSpec],
    ) -> tuple[
        dict[type[FlextInfraFixerAdapter], list[me.EnforcementRuleSpec]],
        tuple[me.EnforcementRuleSpec, ...],
    ]:
        """Group rules by the adapter that can handle their fix_action."""
        grouped: dict[type[FlextInfraFixerAdapter], list[me.EnforcementRuleSpec]] = (
            defaultdict(list)
        )
        unhandled: list[me.EnforcementRuleSpec] = []
        for rule in rules:
            fix_action = rule.fix_action
            if fix_action is None:
                unhandled.append(rule)
                continue
            adapter_cls = self._adapter_for(fix_action)
            if adapter_cls is not None:
                grouped[adapter_cls].append(rule)
                continue
            unhandled.append(rule)
        return grouped, tuple(unhandled)

    def _adapter_for(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> type[FlextInfraFixerAdapter] | None:
        """Return the first adapter class that accepts ``fix_action``."""
        for adapter_cls in self._ADAPTER_CLASSES:
            adapter = adapter_cls.__new__(adapter_cls)
            if adapter.can_fix(fix_action):
                return adapter_cls
        return None

    def _instantiate_adapter(
        self,
        adapter_cls: type[FlextInfraFixerAdapter],
    ) -> FlextInfraFixerAdapter:
        """Create an adapter instance, injecting workspace root."""
        return adapter_cls(self.workspace_root)

    def _collect_violations(
        self,
        project_dir: Path,
        rules: t.SequenceOf[me.EnforcementRuleSpec],
    ) -> tuple[
        list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        list[fr.FailedFix],
    ]:
        """Collect violations for ``rules`` inside ``project_dir``.

        For ``flext_tests_validator`` rules this delegates to
        ``FlextTestsValidator``. Gate-backed sources get a project-level probe.
        Runtime detector sources get one probe per Python file so the adapter
        can decide deterministically whether a rewrite applies.
        """
        violations: list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]] = []
        failures: list[fr.FailedFix] = []
        declarative_rules: list[me.EnforcementRuleSpec] = []
        for rule in rules:
            source = rule.source
            if source.kind == "flext_tests_validator":
                collected, errors = self._collect_tests_validator_violations(
                    project_dir,
                    rule,
                )
                violations.extend(collected)
                failures.extend(errors)
            elif FlextInfraRefactorDeclarativeEnforcement.supports(rule):
                declarative_rules.append(rule)
            elif source.kind in {"flext_infra_detector", "beartype"}:
                collected, errors = self._collect_python_file_violations(
                    project_dir,
                    rule,
                )
                violations.extend(collected)
                failures.extend(errors)
            elif source.kind in {"ruff", "code_smell"}:
                violations.extend(
                    self._collect_project_violations(project_dir, rule),
                )
            else:
                failures.append(
                    self._collection_failure(
                        project_dir,
                        rule,
                        f"unsupported enforcement source kind {source.kind!r}",
                    ),
                )
        if declarative_rules:
            collected, errors = self._collect_declarative_violations(
                project_dir,
                declarative_rules,
            )
            violations.extend(collected)
            failures.extend(errors)
        return violations, failures

    def _collect_tests_validator_violations(
        self,
        project_dir: Path,
        rule: me.EnforcementRuleSpec,
    ) -> tuple[
        list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        list[fr.FailedFix],
    ]:
        """Run the flext-tests validator method for ``rule``."""
        source = rule.source
        if source.kind != "flext_tests_validator":
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rule,
                        f"invalid validator source kind {source.kind!r}",
                    ),
                ],
            )
        try:
            tv_mod = importlib.import_module("flext_tests.validator")
            validator_cls = getattr(tv_mod, "FlextTestsValidator", None)
            if validator_cls is None:
                return (
                    [],
                    [
                        self._collection_failure(
                            project_dir,
                            rule,
                            "flext_tests.validator missing FlextTestsValidator",
                        ),
                    ],
                )
        except ImportError as exc:
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rule,
                        f"unable to import flext_tests.validator: {exc}",
                    ),
                ],
            )
        method = getattr(validator_cls, source.method, None)
        if method is None or not callable(method):
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rule,
                        f"flext_tests validator method {source.method!r} missing",
                    ),
                ],
            )
        try:
            result = method(project_dir)
        except c.EXC_BROAD_RUNTIME as exc:
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rule,
                        f"flext_tests validator method {source.method!r} failed: {exc}",
                    ),
                ],
            )
        if getattr(result, "failure", False):
            error = getattr(result, "error", "") or "validator returned failure"
            return (
                [],
                [self._collection_failure(project_dir, rule, str(error))],
            )
        scan = getattr(result, "value", None)
        if scan is None:
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rule,
                        "validator returned empty scan payload",
                    ),
                ],
            )
        wanted_ids = frozenset(source.rule_ids)
        out: list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]] = []
        for violation in getattr(scan, "violations", ()):
            if wanted_ids and getattr(violation, "rule_id", "") not in wanted_ids:
                continue
            out.append((rule, violation))
        return out, []

    def _collect_python_file_violations(
        self,
        project_dir: Path,
        rule: me.EnforcementRuleSpec,
    ) -> tuple[
        list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        list[fr.FailedFix],
    ]:
        """Return one probe per Python file for transformer-backed detector rules.

        Runtime detector rules backed by a deterministic source
        transformer are applied project-wide; the transformer itself decides
        whether each file needs a change. This keeps the orchestrator from
        silently skipping rules whose detectors do not emit per-file probes.
        """
        files_result = u.Infra.iter_python_files(
            workspace_root=self.workspace_root,
            project_roots=[project_dir],
            include_tests=True,
            include_examples=False,
            include_scripts=False,
            include_dynamic_dirs=False,
        )
        if files_result.failure:
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rule,
                        files_result.error or "unable to enumerate Python files",
                    ),
                ],
            )
        return (
            [(rule, self._probe_for_path(path)) for path in files_result.value],
            [],
        )

    def _collect_declarative_violations(
        self,
        project_dir: Path,
        rules: t.SequenceOf[me.EnforcementRuleSpec],
    ) -> tuple[
        list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        list[fr.FailedFix],
    ]:
        """Return concrete probes by running the declarative engine per file.

        Unlike the generic per-file probe, this asks the declarative engine
        to actually inspect each file and emit violation probes with line
        numbers and metadata. All ``rules`` are evaluated inside a single rope
        project to avoid repeated project open/close overhead.
        """
        files_result = u.Infra.iter_python_files(
            workspace_root=self.workspace_root,
            project_roots=[project_dir],
            include_tests=True,
            include_examples=False,
            include_scripts=False,
            include_dynamic_dirs=False,
        )
        if files_result.failure:
            return (
                [],
                [
                    self._collection_failure(
                        project_dir,
                        rules[0],
                        files_result.error or "unable to enumerate Python files",
                    ),
                ],
            )
        file_paths = list(files_result.value)
        if any(
            getattr(rule.source, "violation_field", "") == "stub_file_violations"
            for rule in rules
        ):
            file_paths.extend(self._stub_file_paths(project_dir))
        probes: list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]] = []
        failures: list[fr.FailedFix] = []
        with u.Infra.open_project(self.workspace_root) as rope_project:
            for file_path in file_paths:
                ctx = m.Infra.DetectorContext(
                    file_path=file_path,
                    rope_project=rope_project,
                    project_name=project_dir.name,
                    project_root=project_dir,
                )
                for rule in rules:
                    try:
                        detected = FlextInfraRefactorDeclarativeEnforcement.detect(
                            rule,
                            ctx,
                        )
                    except c.EXC_BROAD_RUNTIME as exc:
                        failures.append(
                            self._collection_failure(
                                project_dir,
                                rule,
                                f"declarative engine failed: {exc}",
                            ),
                        )
                        continue
                    probes.extend((rule, probe) for probe in detected)
        return probes, failures

    @staticmethod
    def _stub_file_paths(project_dir: Path) -> tuple[Path, ...]:
        """Return source stub files while respecting canonical excluded dirs."""
        paths: set[Path] = set()
        for path in project_dir.rglob("*.pyi"):
            if not path.is_file():
                continue
            relative_parts = path.relative_to(project_dir).parts
            if any(part in c.Infra.ITERATION_EXCLUDED_PARTS for part in relative_parts):
                continue
            paths.add(path.resolve())
        return tuple(sorted(paths))

    def _collect_project_violations(
        self,
        project_dir: Path,
        rule: me.EnforcementRuleSpec,
    ) -> list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]]:
        """Return one project-level probe for gate-backed fixes."""
        return [(rule, self._probe_for_path(project_dir))]

    @staticmethod
    def _probe_for_path(path: Path) -> p.AttributeProbe:
        """Build the minimal structural probe consumed by fixer adapters."""
        return SimpleNamespace(file_path=str(path))

    @staticmethod
    def _collection_failure(
        project_dir: Path,
        rule: me.EnforcementRuleSpec,
        message: str,
    ) -> fr.FailedFix:
        """Build a failed-fix record for collection/routing errors."""
        return fr.FailedFix(
            rule_id=rule.id,
            file_path=str(project_dir),
            error=message,
        )

    def _command_ctx(self) -> m.Infra.FixEnforcementCommand:
        """Build a command context for adapters from the service fields.

        Dry-run (``apply=False``) must never trigger post-fix checks, because
        check-after gates may rewrite files in place and restore originals.
        Forcing ``check_after=False`` keeps the run 100% read-only regardless
        of the CLI default or any future check-after implementation.
        """
        return m.Infra.FixEnforcementCommand(
            workspace=str(self.workspace_root),
            projects=self.project_names,
            apply=self.apply,
            rules=self.rules,
            safe_only=self.safe_only,
            check_after=self.check_after and self.apply,
            fail_fast=self.fail_fast,
        )

    @staticmethod
    def _render_report(
        results: t.SequenceOf[fr.ProjectFixResult],
    ) -> str:
        """Render a concise text report from all project results."""
        total_fixed = sum(len(r.fixed) for r in results)
        total_previewed = sum(len(r.previewed) for r in results)
        total_skipped = sum(len(r.skipped) for r in results)
        total_failed = sum(len(r.failed) for r in results)
        project_count = len({r.project for r in results})
        lines = [
            "Enforcement fix report:",
            f"  projects: {project_count}",
            f"  fixed: {total_fixed}",
            f"  previewed: {total_previewed}",
            f"  skipped: {total_skipped}",
            f"  failed: {total_failed}",
        ]
        for result in results:
            if not (
                result.fixed or result.previewed or result.skipped or result.failed
            ):
                continue
            interesting_skipped = [
                skipped
                for skipped in result.skipped
                if skipped.reason != "no changes produced"
            ]
            lines.append(f"  {result.project}:")
            lines.extend(
                f"    + {fixed.rule_id}: {fixed.file_path}" for fixed in result.fixed
            )
            lines.extend(
                f"    ? {preview.rule_id}: {preview.file_path}"
                for preview in result.previewed
            )
            lines.extend(
                f"    ~ {skipped.rule_id}: {skipped.reason}"
                for skipped in interesting_skipped
            )
            lines.extend(
                f"    ! {failed.rule_id}: {failed.error}" for failed in result.failed
            )
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraEnforcementFixerOrchestrator"]
