"""Violations sweep: repair through the canonical verbs, prove the reduction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shlex
import sys
from pathlib import Path
from time import monotonic
from typing import override
from uuid import uuid4

from flext_infra import c, config, m, p, r, s, t, u
from flext_infra.codemod.batch_gates import FlextInfraModGateEngine


class FlextInfraRefactorViolationsSweep(
    m.Infra.ViolationsSweepRequest,
    s[m.Infra.ViolationsSweepReport],
):
    """Run canonical repairs and reject introduced finding occurrences.

    Rule focus is validated against the elected plan, never passed to the full
    before/after scans. Repairs use the configured default or a public ordered
    sequence of selector-free Make verbs. Audit inspects each discovered project
    separately and must preserve the governed source and catalog inventory.
    """

    @override
    def execute(self) -> p.Result[m.Infra.ViolationsSweepReport]:
        """Scan, repair through the canonical verbs, rescan, publish, verdict.

        Returns:
            The resulting ``p.Result[m.Infra.ViolationsSweepReport]``.

        """
        root = self.repository_root
        selection = self._validated_selection()
        if selection.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(selection)
        rule_ids, verbs = selection.value
        projects = tuple(u.Infra.governed_project_roots(root))
        destination = c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        invocation = destination.parent / destination.stem / uuid4().hex
        before_scan = self._scan_evidence(root, invocation / "before.json")
        if before_scan.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(before_scan)
        repairs = self._repair_stages(
            root,
            verbs,
            projects,
        )
        after_scan = self._scan_evidence(root, invocation / "after.json")
        report = m.Infra.ViolationsSweepReport(
            schema_version=c.Infra.VIOLATIONS_SWEEP_REPORT_SCHEMA_VERSION,
            repository_root=root.resolve(),
            repair_verbs=tuple(verbs),
            focused_rule_ids=rule_ids or (),
            repository_roots=projects,
            stages=tuple(repairs[1]),
            before=m.Infra.ViolationsTotals.from_scan_report(before_scan.value[0]),
            after=(
                m.Infra.ViolationsTotals.from_scan_report(after_scan.value[0])
                if after_scan.success
                else None
            ),
            rule_deltas=(
                u.Infra.rule_deltas(
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
            ),
            completed_verbs=tuple(repairs[0]),
            failed_verb=repairs[2],
            repair_error=str(repairs[3].error) if repairs[3] is not None else None,
            after_scan_error=str(after_scan.error) if after_scan.failure else None,
            before_evidence=before_scan.value[1],
            after_evidence=after_scan.value[1] if after_scan.success else None,
            before_plan=before_scan.value[2],
            after_plan=after_scan.value[2] if after_scan.success else None,
            before_source_sha256=before_scan.value[3],
            after_source_sha256=after_scan.value[3] if after_scan.success else None,
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
            if outcome.failure and repairs[3] is not None:
                sys.stderr.write(
                    f"violations sweep secondary {label} failure: {outcome.error}\n",
                )
        if repairs[3] is not None or after_scan.failure or published.failure:
            return r[m.Infra.ViolationsSweepReport].from_failure(
                repairs[3]
                if repairs[3] is not None
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

    def _validated_selection(
        self,
    ) -> p.Result[t.Pair[t.StrSequence | None, t.StrSequence]]:
        """Validate the existing sweep request before source or Make effects.

        Returns:
            The elected rule identities and declared selector-free verbs.
        """
        result = r[t.Pair[t.StrSequence | None, t.StrSequence]]
        if any(
            selector is not None
            for selector in (
                self.target_module,
                self.target_namespace,
                self.project_filter,
            )
        ):
            return result.fail(
                "violations sweep requires the full governed project inventory",
            )
        rule_ids = (
            tuple(rule_id.strip() for rule_id in self.rules.split(","))
            if self.rules is not None
            else None
        )
        focused = u.Infra.codemod_rule_plan(self.repository_root, rule_ids=rule_ids)
        if focused.failure:
            return result.from_failure(focused)
        verbs = (
            tuple(verb.strip() for verb in self.repair_verbs.split(","))
            if self.repair_verbs is not None
            else config.Infra.codegen.make.violations_sweep_repair_verbs
        )
        admissible = {
            verb.name
            for verb in config.Infra.codegen.make.verbs
            if not verb.arguments and set(verb.profiles) == set(c.Infra.MakeProfile)
        }
        if not verbs or any(verb not in admissible for verb in verbs):
            return result.fail(
                "violations sweep requires declared selector-free Make verbs: "
                + ", ".join(verb for verb in verbs if verb not in admissible),
            )
        if rule_ids is not None and any(verb != "audit" for verb in verbs):
            return result.fail(
                "selected-rule mutation is not implemented; no repair verb invoked",
            )
        return result.ok((rule_ids, verbs))

    def _repair_stages(
        self,
        root: Path,
        verbs: t.StrSequence,
        projects: t.SequenceOf[Path],
    ) -> t.Quad[
        t.StrSequence,
        t.SequenceOf[m.Infra.ViolationsSweepStage],
        str | None,
        p.Result[bool] | None,
    ]:
        """Run the declared sequence and retain every invoked or blocked stage.

        Returns:
            Completed verbs, stage receipts, first failed verb and original failure.
        """
        completed: list[str] = []
        stages: list[m.Infra.ViolationsSweepStage] = []
        failed_verb: str | None = None
        repair_failure: p.Result[bool] | None = None
        for verb in verbs:
            blocked = repair_failure is not None
            for project in projects if verb == "audit" else (root,):
                if blocked:
                    stages.append(
                        m.Infra.ViolationsSweepStage(
                            repository_root=project.resolve(),
                            cwd=root.resolve(),
                            command=(
                                (
                                    c.Infra.MAKE,
                                    "-f",
                                    str(project / c.Infra.MAKEFILE_FILENAME),
                                    verb,
                                )
                                if verb == "audit"
                                else (c.Infra.MAKE, verb)
                            ),
                            verb=verb,
                            duration=0,
                            invoked=False,
                            outcome=None,
                            error=f"not invoked after failed {failed_verb}",
                        )
                    )
                    continue
                stage, repaired = self._run_stage(
                    root,
                    project,
                    verb,
                )
                stages.append(stage)
                if repaired.failure and repair_failure is None:
                    failed_verb = verb
                    repair_failure = repaired
            if repair_failure is not None:
                continue
            completed.append(verb)
        return tuple(completed), tuple(stages), failed_verb, repair_failure

    @classmethod
    def _run_stage(
        cls,
        root: Path,
        project: Path,
        verb: str,
    ) -> t.Pair[m.Infra.ViolationsSweepStage, p.Result[bool]]:
        """Invoke one canonical operation and preserve audit checks even on failure.

        Returns:
            The process receipt and its causal verdict.
        """
        command = (
            (c.Infra.MAKE, "-f", str(project / c.Infra.MAKEFILE_FILENAME), verb)
            if verb == "audit"
            else (c.Infra.MAKE, verb)
        )
        before = cls._source_snapshot(root) if verb == "audit" else None
        started = monotonic()
        executed = (
            u.Cli.run_raw(command, cwd=root)
            if before is None or before.success
            else r[p.Cli.CommandOutput].from_failure(before)
        )
        duration = monotonic() - started
        output = executed.value if executed.success else None
        verdict = (
            r[bool].from_failure(executed)
            if executed.failure
            else r[bool].ok(value=True)
        )
        if output is not None and not u.Cli.process_succeeded(output.outcome):
            verdict = r[bool].fail(
                f"failed ({output.outcome.raw_return_code}): "
                f"{shlex.join(list(command))}: "
                f"timed_out={output.outcome.timed_out}, "
                f"forwarded_signal={output.outcome.forwarded_signal}: "
                f"{(output.stderr or output.stdout).strip()}",
            )
        after = cls._source_snapshot(root) if verb == "audit" else None
        unchanged: bool | None = None
        inspection_error: str | None = None
        if after is not None:
            if after.failure:
                inspection_error = str(after.error)
                if verdict.success:
                    verdict = r[bool].from_failure(after)
            elif before is not None and before.success:
                unchanged = (
                    before.value.plan == after.value.plan
                    and before.value.sha256 == after.value.sha256
                    and before.value.scope == after.value.scope
                    and before.value.repository_roots == after.value.repository_roots
                )
                if not unchanged:
                    inspection_error = (
                        "audit changed governed source bytes, rule plan or inventory"
                    )
                    if verdict.success:
                        verdict = r[bool].fail(inspection_error)
        return m.Infra.ViolationsSweepStage(
            repository_root=project.resolve(),
            cwd=root.resolve(),
            command=command,
            verb=verb,
            duration=duration,
            invoked=before is None or before.success,
            outcome=(
                m.Cli.ProcessOutcome(
                    raw_return_code=output.outcome.raw_return_code,
                    timed_out=output.outcome.timed_out,
                    forwarded_signal=output.outcome.forwarded_signal,
                )
                if output is not None
                else None
            ),
            error=str(verdict.error) if verdict.failure else None,
            audit_before=before.value
            if before is not None and before.success
            else None,
            audit_after=after.value if after is not None and after.success else None,
            source_inventory_unchanged=unchanged,
            inspection_error=inspection_error,
        ), verdict

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
        captured = FlextInfraRefactorViolationsSweep._source_snapshot(root)
        if captured.failure:
            return result.from_failure(captured)
        snapshot = captured.value
        scanned = FlextInfraModGateEngine.scan(root, fix=False)
        if scanned.failure:
            return result.from_failure(scanned)
        validated = FlextInfraRefactorViolationsSweep._validate_scan_sources(
            root,
            snapshot.scope,
            snapshot.states,
            snapshot.plan,
        )
        if validated.failure:
            return result.from_failure(validated)
        repositories = tuple(project.name for project in snapshot.repository_roots)
        receipt = u.Infra.publish_mod_scan_evidence(
            root,
            scanned.value,
            command=c.Infra.ModScanCommand.SCAN,
            scope=snapshot.scope,
            relative_path=destination,
            repositories=repositories,
            rule_ids=tuple(rule.id for rule in snapshot.plan.rules),
        )
        if receipt.failure:
            return result.from_failure(receipt)
        return result.ok((
            scanned.value,
            receipt.value,
            snapshot.plan,
            snapshot.sha256,
        ))

    @classmethod
    def _source_snapshot(cls, root: Path) -> p.Result[m.Infra.ViolationsSweepSources]:
        """Read the existing scan inventory without executing another native scan.

        Returns:
            Authenticated source, scope, topology and elected catalog identities.
        """
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return r[m.Infra.ViolationsSweepSources].from_failure(planned)
        plan = planned.value
        targets = u.Infra.ast_grep_scan_targets(root)
        projects = tuple(u.Infra.governed_project_roots(root))
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
                return r[m.Infra.ViolationsSweepSources].from_failure(state)
            states.append(state.value)
        validated = cls._validate_scan_sources(root, targets, states, plan)
        if validated.failure:
            return r[m.Infra.ViolationsSweepSources].from_failure(validated)
        if projects != tuple(u.Infra.governed_project_roots(root)):
            return r[m.Infra.ViolationsSweepSources].fail(
                "violations sweep project topology changed during observation",
            )
        return r[m.Infra.ViolationsSweepSources].ok(
            m.Infra.ViolationsSweepSources(
                plan=plan,
                scope=targets,
                states=tuple(states),
                repository_roots=projects,
                sha256={
                    str(state.path): u.Cli.sha256_bytes(state.content)
                    for state in states
                    if state.content is not None
                },
            )
        )

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
