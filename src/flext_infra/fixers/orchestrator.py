"""Catalog-driven enforcement fix orchestrator.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
from collections import defaultdict
from pathlib import Path
from typing import Annotated, ClassVar, override

from flext_core import r
from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_core.utilities import FlextUtilitiesEnforcement
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.constants import c
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.gate_fixer import FlextInfraGateFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.fixers.transformer_fixer import FlextInfraTransformerFixerAdapter
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t
from flext_infra.utilities import u


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
        instance = cls(
            workspace_root=params.workspace_path,
            selected_projects=params.project_names,
            apply=params.apply,
            rules=params.rules,
            safe_only=params.safe_only,
            check_after=params.check_after,
            fail_fast=params.fail_fast,
        )
        return instance.execute()

    @override
    def execute(self) -> p.Result[str]:
        """Run the enforcement fix pipeline and return a human-readable report."""
        catalog = FlextUtilitiesEnforcement.build_canonical_catalog()
        selected_rules = self._selected_rules(catalog)
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
        return r[str].ok(report)

    def _selected_rules(
        self,
        catalog: me.EnforcementCatalog,
    ) -> tuple[me.EnforcementRuleSpec, ...]:
        """Return enabled rules with fix actions matching the CLI filter."""
        wanted = frozenset(self.rules) if self.rules else frozenset()
        results: list[me.EnforcementRuleSpec] = []
        for rule in catalog.enabled_rules():
            if not rule.fix_action:
                continue
            if wanted and rule.id not in wanted:
                continue
            if self.safe_only and not rule.fix_action.safe:
                continue
            results.append(rule)
        return tuple(results)

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
        selected = (
            tuple(p for p in discovered if p.path.name in scope)
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
        by_adapter = self._group_by_adapter(rules)
        for adapter_cls, adapter_rules in by_adapter.items():
            adapter = self._instantiate_adapter(adapter_cls)
            violations = self._collect_violations(
                project_dir=project_dir,
                rules=adapter_rules,
            )
            if not violations:
                continue
            result = adapter.fix_project(project_dir, violations, self._command_ctx())
            results.append(result)
        return tuple(results)

    def _group_by_adapter(
        self,
        rules: t.SequenceOf[me.EnforcementRuleSpec],
    ) -> dict[type[FlextInfraFixerAdapter], list[me.EnforcementRuleSpec]]:
        """Group rules by the adapter that can handle their fix_action."""
        grouped: dict[type[FlextInfraFixerAdapter], list[me.EnforcementRuleSpec]] = (
            defaultdict(list)
        )
        for rule in rules:
            fix_action = rule.fix_action
            if fix_action is None:
                continue
            adapter_cls = self._adapter_for(fix_action)
            if adapter_cls is not None:
                grouped[adapter_cls].append(rule)
        return grouped

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
    ) -> list[tuple[me.EnforcementRuleSpec, t.AttributeProbe]]:
        """Collect violations for ``rules`` inside ``project_dir``.

        For ``flext_tests_validator`` rules this delegates to
        ``FlextTestsValidator``. Other source kinds currently return empty and
        are expected to be wired as adapters mature.
        """
        violations: list[tuple[me.EnforcementRuleSpec, t.AttributeProbe]] = []
        for rule in rules:
            source = rule.source
            if source.kind == "flext_tests_validator":
                violations.extend(
                    self._collect_tests_validator_violations(project_dir, rule),
                )
            elif source.kind == "ruff":
                violations.extend(
                    self._collect_ruff_violations(project_dir, rule),
                )
            elif source.kind == "beartype":
                # Beartype/runtime warnings are detected at import time; we do
                # not collect them here. Future work can wire a rope scanner.
                pass
        return violations

    def _collect_tests_validator_violations(
        self,
        project_dir: Path,
        rule: me.EnforcementRuleSpec,
    ) -> list[tuple[me.EnforcementRuleSpec, t.AttributeProbe]]:
        """Run the flext-tests validator method for ``rule``."""
        source = rule.source
        if source.kind != "flext_tests_validator":
            return []
        try:
            tv_mod = importlib.import_module("flext_tests.validator")
            validator_cls = getattr(tv_mod, "FlextTestsValidator", None)
            if validator_cls is None:
                return []
        except ImportError:
            return []
        method = getattr(validator_cls, source.method, None)
        if method is None or not callable(method):
            return []
        try:
            result = method(project_dir)
        except c.EXC_BROAD_RUNTIME:
            return []
        if getattr(result, "failure", False):
            return []
        scan = getattr(result, "value", None)
        if scan is None:
            return []
        wanted_ids = frozenset(source.rule_ids)
        out: list[tuple[me.EnforcementRuleSpec, t.AttributeProbe]] = []
        for violation in getattr(scan, "violations", ()):
            if wanted_ids and getattr(violation, "rule_id", "") not in wanted_ids:
                continue
            out.append((rule, violation))
        return out

    def _collect_ruff_violations(
        self,
        project_dir: Path,
        rule: me.EnforcementRuleSpec,
    ) -> list[tuple[me.EnforcementRuleSpec, t.AttributeProbe]]:
        """Ruff violations are handled gate-side; no per-violation collection."""
        _ = project_dir, rule
        return []

    def _command_ctx(self) -> m.Infra.FixEnforcementCommand:
        """Build a command context for adapters from the service fields."""
        return m.Infra.FixEnforcementCommand(
            workspace=str(self.workspace_root),
            projects=self.project_names,
            apply=self.apply,
            rules=self.rules,
            safe_only=self.safe_only,
            check_after=self.check_after,
            fail_fast=self.fail_fast,
        )

    @staticmethod
    def _render_report(
        results: t.SequenceOf[fr.ProjectFixResult],
    ) -> str:
        """Render a concise text report from all project results."""
        total_fixed = sum(len(r.fixed) for r in results)
        total_skipped = sum(len(r.skipped) for r in results)
        total_failed = sum(len(r.failed) for r in results)
        lines = [
            "Enforcement fix report:",
            f"  projects: {len(results)}",
            f"  fixed: {total_fixed}",
            f"  skipped: {total_skipped}",
            f"  failed: {total_failed}",
        ]
        for result in results:
            if not (result.fixed or result.skipped or result.failed):
                continue
            lines.append(f"  {result.project}:")
            lines.extend(
                f"    + {fixed.rule_id}: {fixed.file_path}" for fixed in result.fixed
            )
            lines.extend(
                f"    ~ {skipped.rule_id}: {skipped.reason}"
                for skipped in result.skipped
            )
            lines.extend(
                f"    ! {failed.rule_id}: {failed.error}" for failed in result.failed
            )
        return "\n".join(lines)


__all__: list[str] = ["FlextInfraEnforcementFixerOrchestrator"]
