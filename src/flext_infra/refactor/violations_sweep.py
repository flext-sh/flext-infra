"""Violations sweep: repair through the canonical verbs, prove the reduction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import Counter
from typing import override

from flext_infra import c, m, p, r, s, u
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine


class FlextInfraRefactorViolationsSweep(s[m.Infra.ViolationsSweepReport]):
    """Run canonical repairs and reject introduced finding occurrences.

    The sweep measures the repository's mod scan totals, runs the repository's
    own canonical repair verbs in order (``make fix``, ``make fmt``,
    ``make mod`` — the same surface every agent and developer runs), measures
    again, and fails the command the moment any total increased: automation
    may reduce a tree's violations, never grow them. The before/after totals
    are published as one receipt under the repository's reports.
    """

    @override
    def execute(self) -> p.Result[m.Infra.ViolationsSweepReport]:
        """Scan, repair through the canonical verbs, rescan, publish, verdict.

        Returns:
            The resulting ``p.Result[m.Infra.ViolationsSweepReport]``.

        """
        root = self.repository_root
        before_scan = FlextInfraModGateEngine.scan(root, fix=False)
        if before_scan.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(before_scan)
        before = m.Infra.ViolationsTotals.from_scan_report(before_scan.value)
        completed: list[str] = []
        failed_verb: str | None = None
        repair_error: str | None = None
        for verb in c.Infra.VIOLATIONS_SWEEP_REPAIR_VERBS:
            repaired = u.Cli.run_checked([c.Infra.MAKE, verb], cwd=root)
            if repaired.failure:
                failed_verb = verb
                repair_error = str(repaired.error)
                break
            completed.append(verb)
        after_scan = FlextInfraModGateEngine.scan(root, fix=False)
        after = (
            None
            if after_scan.failure
            else m.Infra.ViolationsTotals.from_scan_report(after_scan.value)
        )
        deltas = (
            self._rule_deltas(before_scan.value, after_scan.value)
            if after_scan.success
            else ()
        )
        report = m.Infra.ViolationsSweepReport(
            schema_version=c.Infra.VIOLATIONS_SWEEP_REPORT_SCHEMA_VERSION,
            repository_root=root.resolve(),
            repair_verbs=tuple(c.Infra.VIOLATIONS_SWEEP_REPAIR_VERBS),
            before=before,
            after=after,
            rule_deltas=tuple(deltas),
            completed_verbs=tuple(completed),
            failed_verb=failed_verb,
            repair_error=repair_error,
            after_scan_error=str(after_scan.error) if after_scan.failure else None,
        )
        published = u.Infra.publish_refactor_report_evidence(
            root,
            report,
            relative_path=c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH,
        )
        if published.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(published)
        if repair_error is not None or after_scan.failure:
            return r[m.Infra.ViolationsSweepReport].fail(
                repair_error or str(after_scan.error),
            )
        if any(delta.introduced for delta in deltas):
            return r[m.Infra.ViolationsSweepReport].fail(
                "violations sweep introduced finding occurrences",
            )
        if report.increased_totals:
            return r[m.Infra.ViolationsSweepReport].fail(
                "violations sweep grew " + ", ".join(report.increased_totals),
            )
        return r[m.Infra.ViolationsSweepReport].ok(report)

    @staticmethod
    def _rule_deltas(
        before: m.Infra.ModScanReport,
        after: m.Infra.ModScanReport,
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Compare stable matched-source identities with occurrence multiplicity.

        Returns:
            Per-repository and per-rule occurrence deltas.
        """
        deltas: list[m.Infra.ViolationsRuleDelta] = []
        if before.entries or after.entries:
            # Positions move during formatting; retain exact matched text and file,
            # and compare multiplicities rather than collapsing duplicate matches.
            before_entries = Counter(
                (entry.repository, entry.rule_id, entry.file, entry.text)
                for entry in before.entries
            )
            after_entries = Counter(
                (entry.repository, entry.rule_id, entry.file, entry.text)
                for entry in after.entries
            )
            for repository, rule_id in sorted({
                (key[0], key[1]) for key in before_entries | after_entries
            }):
                keys = {
                    key
                    for key in before_entries | after_entries
                    if key[:2] == (repository, rule_id)
                }
                persisted = sum(
                    min(before_entries[key], after_entries[key]) for key in keys
                )
                before_count = sum(before_entries[key] for key in keys)
                after_count = sum(after_entries[key] for key in keys)
                deltas.append(
                    m.Infra.ViolationsRuleDelta(
                        repository=repository,
                        rule_id=rule_id,
                        before=before_count,
                        after=after_count,
                        resolved=before_count - persisted,
                        persisted=persisted,
                        introduced=after_count - persisted,
                    )
                )
        return tuple(deltas)


__all__: list[str] = ["FlextInfraRefactorViolationsSweep"]
