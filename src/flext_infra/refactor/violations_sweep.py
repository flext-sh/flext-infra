"""Violations sweep: repair through the canonical verbs, prove the reduction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import override
from uuid import uuid4

from flext_infra import c, m, p, r, s, t, u
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
        destination = c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        invocation = destination.parent / destination.stem / uuid4().hex
        before_scan = self._scan_evidence(root, invocation / "before.json")
        if before_scan.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(before_scan)
        before = m.Infra.ViolationsTotals.from_scan_report(before_scan.value[0])
        completed: list[str] = []
        failed_verb: str | None = None
        repair_failure: p.Result[p.Cli.CommandOutput] | None = None
        for verb in c.Infra.VIOLATIONS_SWEEP_REPAIR_VERBS:
            repaired = u.Cli.run_checked([c.Infra.MAKE, verb], cwd=root)
            if repaired.failure:
                failed_verb = verb
                repair_failure = repaired
                break
            completed.append(verb)
        after_scan = self._scan_evidence(root, invocation / "after.json")
        after = (
            None
            if after_scan.failure
            else m.Infra.ViolationsTotals.from_scan_report(after_scan.value[0])
        )
        deltas = (
            self.rule_deltas(
                before_scan.value[0],
                after_scan.value[0],
                inventory=tuple(
                    sorted({
                        (repository, rule_id)
                        for receipt in (before_scan.value[1], after_scan.value[1])
                        for repository in receipt.evidence.totals_by_repository
                        for rule_id in receipt.evidence.totals_by_rule
                    })
                ),
            )
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
            repair_error=(
                str(repair_failure.error) if repair_failure is not None else None
            ),
            after_scan_error=str(after_scan.error) if after_scan.failure else None,
            before_evidence=before_scan.value[1],
            after_evidence=after_scan.value[1] if after_scan.success else None,
            before_plan=before_scan.value[2],
            after_plan=after_scan.value[2] if after_scan.success else None,
            before_source_sha256=before_scan.value[3],
            after_source_sha256=after_scan.value[3] if after_scan.success else {},
        )
        published = u.Infra.publish_refactor_report_evidence(
            root,
            report,
            relative_path=invocation / destination.name,
        )
        if published.success:
            published = u.Infra.publish_refactor_report_evidence(
                root,
                report,
                relative_path=destination,
            )
        for label, outcome in (("scan", after_scan), ("publication", published)):
            if outcome.failure and repair_failure is not None:
                sys.stderr.write(
                    f"violations sweep secondary {label} failure: {outcome.error}\n",
                )
        if repair_failure is not None or after_scan.failure or published.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(
                repair_failure
                if repair_failure is not None
                else (after_scan if after_scan.failure else published),
            )
        if any(delta.introduced for delta in report.rule_deltas):
            return r[m.Infra.ViolationsSweepReport].fail(
                "violations sweep introduced finding occurrences",
            )
        if report.increased_totals:
            return r[m.Infra.ViolationsSweepReport].fail(
                "violations sweep grew " + ", ".join(report.increased_totals),
            )
        return r[m.Infra.ViolationsSweepReport].ok(report)

    @staticmethod
    def rule_deltas(
        before: m.Infra.ModScanReport,
        after: m.Infra.ModScanReport,
        *,
        inventory: tuple[tuple[str, str], ...] = (),
    ) -> tuple[m.Infra.ViolationsRuleDelta, ...]:
        """Compare lexical multiplicities, without asserting semantic correspondence.

        Returns:
            Per-repository and per-rule occurrence deltas.
        """
        deltas: list[m.Infra.ViolationsRuleDelta] = []
        if before.entries or after.entries or inventory:
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
            for repository, rule_id in sorted(
                set(inventory)
                | {(key[0], key[1]) for key in before_entries | after_entries}
            ):
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
                        before_entries=tuple(
                            index
                            for index, entry in enumerate(before.entries)
                            if (entry.repository, entry.rule_id)
                            == (repository, rule_id)
                        ),
                        after_entries=tuple(
                            index
                            for index, entry in enumerate(after.entries)
                            if (entry.repository, entry.rule_id)
                            == (repository, rule_id)
                        ),
                    )
                )
        return tuple(deltas)

    @staticmethod
    def _scan_evidence(
        root: Path,
        destination: Path,
    ) -> p.Result[
        t.Quad[
            m.Infra.ModScanReport,
            m.Infra.ModScanEvidenceReceipt,
            m.Infra.CodemodRulePlan,
            t.StrMapping,
        ]
    ]:
        """Authenticate the canonical inventory around a scan and preserve its receipt.

        Returns:
            Full scan, immutable publication, elected plan and source digests.
        """
        result = r[
            t.Quad[
                m.Infra.ModScanReport,
                m.Infra.ModScanEvidenceReceipt,
                m.Infra.CodemodRulePlan,
                t.StrMapping,
            ]
        ]
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return result.from_failure(planned)
        plan = planned.value
        targets = u.Infra.ast_grep_scan_targets(root)
        paths = {rule.resource.resolve() for rule in plan.rules}
        paths.update(ruleset.config.resolve() for ruleset in plan.rulesets)
        for target in targets:
            path = root / target
            paths.update(
                u.Infra.iter_directory_python_files(path) if path.is_dir() else (path,)
            )
        states: list[m.Cli.AtomicFileState] = []
        for path in sorted(paths):
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return result.from_failure(state)
            states.append(state.value)
        scanned = FlextInfraModGateEngine.scan(root, fix=False)
        if scanned.failure:
            return result.from_failure(scanned)
        validated = FlextInfraRefactorViolationsSweep._validate_scan_sources(
            root,
            targets,
            states,
            plan,
        )
        if validated.failure:
            return result.from_failure(validated)
        repositories = tuple(
            project.name for project in u.Infra.governed_project_roots(root)
        )
        receipt = u.Infra.publish_mod_scan_evidence(
            root,
            scanned.value,
            command=c.Infra.ModScanCommand.SCAN,
            scope=targets,
            relative_path=destination,
            repositories=repositories,
            rule_ids=tuple(rule.id for rule in plan.rules),
        )
        if receipt.failure:
            return result.from_failure(receipt)
        return result.ok((
            scanned.value,
            receipt.value,
            plan,
            {
                str(state.path): u.Cli.sha256_bytes(state.content)
                for state in states
                if state.content is not None
            },
        ))

    @staticmethod
    def _validate_scan_sources(
        root: Path,
        targets: t.StrSequence,
        states: t.SequenceOf[m.Cli.AtomicFileState],
        plan: m.Infra.CodemodRulePlan,
    ) -> p.Result[bool]:
        """Authenticate unchanged scan inventory and source snapshots.

        Returns:
            Success only for the inventory and sources actually scanned.
        """
        for state in states:
            observed = u.Cli.atomic_read_binary_file_state(state.path, required=True)
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != state:
                return r[bool].fail(
                    f"violations sweep scan source changed: {state.path}",
                )
        observed_plan = u.Infra.codemod_rule_plan(root)
        if observed_plan.failure:
            return r[bool].from_failure(observed_plan)
        if plan != observed_plan.value or targets != u.Infra.ast_grep_scan_targets(
            root
        ):
            return r[bool].fail("violations sweep scan rule plan or inventory changed")
        observed_paths = {rule.resource.resolve() for rule in plan.rules}
        observed_paths.update(ruleset.config.resolve() for ruleset in plan.rulesets)
        for target in targets:
            path = root / target
            observed_paths.update(
                u.Infra.iter_directory_python_files(path) if path.is_dir() else (path,)
            )
        if {state.path for state in states} != observed_paths:
            return r[bool].fail("violations sweep scan source inventory changed")
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraRefactorViolationsSweep"]
