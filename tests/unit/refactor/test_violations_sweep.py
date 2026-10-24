"""Refactor violations-sweep: repair through the canonical verbs, prove reduction.

Cases drive the public ``refactor violations-sweep`` CLI or service over the real
mod-workspace fixture with a recording Makefile standing in for the repair
verbs, so the sweep's own scans, receipt, and always-reducing verdict are the
behavior under test.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, m, tm, u
from tests.unit.refactor.violations_sweep_support import (
    TestsFlextInfraRefactorViolationsSweepSupport,
)


@pytest.mark.slow
class TestsFlextInfraRefactorViolationsSweep(
    TestsFlextInfraRefactorViolationsSweepSupport,
):
    """Behavior contract for the ``refactor violations-sweep`` verb: publication."""

    def test_native_lint_failure_keeps_independent_scan_evidence(
        self,
        mod_workspace: Path,
    ) -> None:
        """A failed Ruff configuration remains red without erasing AST or text scans."""
        root = mod_workspace
        self._prepare(root, makefile=self._makefile(), local_rule=True)
        tm.ok(u.Cli.atomic_write_text_file(root / "sample.py", "marker = dict()\n"))
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / "ruff.toml", "line-length = 'invalid'\n"
            )
        )
        tm.that(self._sweep(root, "--audit-rules"), ne=0)
        report = self._receipt(root)
        snapshot = next(
            stage.audit_before
            for stage in report.stages
            if stage.audit_before is not None
        )
        ast_report = tm.not_none(snapshot.ast_report)
        tm.ok(snapshot.text_report is not None)
        tm.that(snapshot.observation_errors, empty=False)
        tm.that("\n".join(snapshot.observation_errors), has="invalid")
        lint = tm.not_none(snapshot.lint)
        receipt = next(
            tools[c.Infra.RUFF]
            for tools in lint.values()
            if tools[c.Infra.RUFF].execution_error is not None
        )
        tm.that(receipt.errors, empty=True)
        output = tm.not_none(receipt.output)
        tm.fail(u.Cli.process_succeeded(output.outcome))
        tm.that(
            any(entry.rule_id == "sweep-growth" for entry in ast_report.entries),
            eq=True,
        )

    @pytest.mark.parametrize("counts", [(2, 0), (2, 1), (1, 2), (0, 0)])
    def test_public_utility_deltas_preserve_native_scan_indexes_and_multiplicity(
        self,
        mod_workspace: Path,
        counts: tuple[int, int],
    ) -> None:
        """The single utility owner retains complete per-rule evidence fields."""
        self._prepare(mod_workspace, makefile=self._makefile(), local_rule=True)
        sample = mod_workspace / "sample.py"
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n" * counts[0]))
        before = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        tm.ok(u.Cli.atomic_write_text_file(sample, "marker = dict()\n" * counts[1]))
        after = tm.ok(FlextInfraModGateEngine.scan(mod_workspace, fix=False))
        evidence = m.Infra.ModScanEvidence.model_validate_json(
            (mod_workspace / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH).read_bytes()
        )
        for classification, field in c.Infra.MOD_SCAN_CLASS_COUNT_FIELDS.items():
            tm.that(
                getattr(evidence, field),
                eq=sum(
                    entry.classification == classification for entry in after.entries
                ),
            )
        with pytest.raises(ValueError, match="deferred differs"):
            m.Infra.ModScanEvidence.model_validate({
                **evidence.model_dump(
                    mode="python", exclude=set(type(evidence).model_computed_fields)
                ),
                "totals_by_class": {
                    **evidence.totals_by_class,
                    c.Infra.ModScanFindingClass.DEFERRED_SOURCE_DRIFT: evidence.deferred
                    + 1,
                },
            })
        plan = tm.ok(u.Infra.codemod_rule_plan(mod_workspace))
        inventory = tuple(
            (project.name, rule.id)
            for project in u.Infra.governed_project_roots(mod_workspace)
            for rule in plan.rules
        )
        deltas = u.Infra.rule_deltas(
            before, after, options=m.Infra.RuleDeltaOptions(inventory=inventory)
        )
        tm.that(
            [(row.repository, row.rule_id) for row in deltas], eq=sorted(set(inventory))
        )
        delta = next(row for row in deltas if row.rule_id == "sweep-growth")
        persisted = min(counts)
        tm.that((delta.before, delta.after), eq=counts)
        tm.that(
            (delta.resolved, delta.introduced),
            eq=tuple(count - persisted for count in counts),
        )
        tm.that(delta.persisted, eq=persisted)
        for row in deltas:
            for report, indexes in (
                (before, row.before_entries),
                (after, row.after_entries),
            ):
                tm.that(
                    indexes,
                    eq=tuple(
                        index
                        for index, entry in enumerate(report.entries)
                        if (entry.repository, entry.rule_id)
                        == (row.repository, row.rule_id)
                    ),
                )
        tm.fail(delta.semantic_correspondence_proven)
