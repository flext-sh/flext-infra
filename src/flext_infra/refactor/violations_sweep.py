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
from flext_infra.codemod.snapshot_reconciler import FlextInfraCodemodSnapshotReconciler
from flext_infra.codemod.text_gates import FlextInfraModTextGateEngine


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
        destination = c.Infra.VIOLATIONS_SWEEP_REPORT_RELATIVE_PATH
        invocation = destination.parent / destination.stem / uuid4().hex
        before_scan = self._scan_evidence(root, invocation / "before.json")
        if before_scan.failure and not self.audit_rules:
            return r[m.Infra.ViolationsSweepReport].from_failure(before_scan)
        initial = before_scan.value[2] if before_scan.success else None
        projects = (
            initial.repository_roots if initial is not None else (root.resolve(),)
        )
        if initial is None:
            declared = u.Infra.git_submodule_declarations(root)
            if declared.failure:
                return r[m.Infra.ViolationsSweepReport].from_failure(before_scan)
            projects = (
                root.resolve(),
                *(
                    (root / item.path).resolve()
                    for item in declared.value
                    if item.managed is not False
                ),
            )
        repairs = self._repair_stages(
            root,
            verbs,
            projects,
            initial,
        )
        after_scan = self._scan_evidence(root, invocation / "after.json")
        comparisons = tuple(
            u.Infra.violations_audit_comparison(
                project,
                m.Infra.ViolationsSweepStage(
                    repository_root=root.resolve(),
                    cwd=root.resolve(),
                    command=(),
                    verb="comparison",
                    duration=0,
                    invoked=False,
                    outcome=None,
                    error=str(after_scan.error) if after_scan.failure else None,
                    audit_before=initial,
                    audit_after=after_scan.value[2] if after_scan.success else None,
                ),
                initial.plan if initial is not None else None,
            )
            for project in projects
        )
        report = m.Infra.ViolationsSweepReport(
            schema_version=c.Infra.VIOLATIONS_SWEEP_REPORT_SCHEMA_VERSION,
            repository_root=root.resolve(),
            repair_verbs=tuple(verbs),
            focused_rule_ids=rule_ids or (),
            repository_roots=projects,
            stages=tuple(repairs[1]),
            before=(
                u.Infra.violations_totals(before_scan.value[0])
                if before_scan.success
                else None
            ),
            after=(
                u.Infra.violations_totals(after_scan.value[0])
                if after_scan.success
                else None
            ),
            rule_deltas=(
                tuple(
                    row.delta
                    for stage in comparisons
                    for row in stage.rule_evaluations
                    if row.delta is not None
                )
            ),
            rule_evaluations=tuple(
                row for stage in comparisons for row in stage.rule_evaluations
            ),
            engine_coverage=tuple(
                row for stage in comparisons for row in stage.engine_coverage
            ),
            completed_verbs=tuple(repairs[0]),
            failed_verb=repairs[2],
            repair_error=str(repairs[3].error) if repairs[3] is not None else None,
            after_scan_error=str(after_scan.error) if after_scan.failure else None,
            before_scan_error=str(before_scan.error) if before_scan.failure else None,
            before_evidence=before_scan.value[1] if before_scan.success else None,
            after_evidence=after_scan.value[1] if after_scan.success else None,
            before_plan=initial.plan if initial is not None else None,
            after_plan=after_scan.value[2].plan if after_scan.success else None,
            before_source_sha256=initial.sha256 if initial is not None else None,
            after_source_sha256=after_scan.value[2].sha256
            if after_scan.success
            else None,
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
        if (
            repairs[3] is not None
            or before_scan.failure
            or after_scan.failure
            or published.failure
        ):
            return r[m.Infra.ViolationsSweepReport].from_failure(
                before_scan
                if before_scan.failure
                else repairs[3]
                if repairs[3] is not None
                else after_scan
                if after_scan.failure
                else published,
            )
        return self._verdict(report, comparisons)

    @staticmethod
    def _verdict(
        report: m.Infra.ViolationsSweepReport,
        comparisons: t.SequenceOf[m.Infra.ViolationsSweepStage],
    ) -> p.Result[m.Infra.ViolationsSweepReport]:
        """Reject introduced occurrences and preserve incomplete observation failures.

        Returns:
            The published report only when its actual native comparisons permit it.
        """
        if any(delta.introduced for delta in report.rule_deltas):
            return r[m.Infra.ViolationsSweepReport].fail(
                "violations sweep introduced finding occurrences",
            )
        if any(stage.error for stage in comparisons):
            return r[m.Infra.ViolationsSweepReport].fail(
                next(stage.error for stage in comparisons if stage.error),
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
            ("audit",)
            if self.audit_rules
            else tuple(verb.strip() for verb in self.repair_verbs.split(","))
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
        initial: m.Infra.ViolationsSweepSources | None,
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
        inventory = initial.plan if initial is not None else None
        if inventory is None:
            catalog = u.Infra.codemod_rule_plan(root)
            inventory = catalog.value if catalog.success else None
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
                stage, repaired = (
                    self._run_rule_audit(project, inventory, initial)
                    if self.audit_rules
                    else self._run_stage(
                        root,
                        project,
                        verb,
                        previous=next(
                            (
                                stage.audit_after
                                for stage in reversed(stages)
                                if stage.repository_root == project.resolve()
                                and stage.audit_after is not None
                            ),
                            initial,
                        ),
                    )
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
        *,
        previous: m.Infra.ViolationsSweepSources | None = None,
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
        before = cls._source_snapshot(project, observe=True, previous=previous)
        started = monotonic()
        executed = (
            u.Cli.run_raw(command, cwd=root)
            if before.success and not before.value.observation_errors
            else (
                r[p.Cli.CommandOutput].fail("; ".join(before.value.observation_errors))
                if before.success
                else r[p.Cli.CommandOutput].from_failure(before)
            )
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
        after = cls._source_snapshot(
            project,
            observe=True,
            previous=before.value if before.success else None,
        )
        stage = m.Infra.ViolationsSweepStage(
            repository_root=project.resolve(),
            cwd=root.resolve(),
            command=command,
            verb=verb,
            duration=duration,
            invoked=before.success and not before.value.observation_errors,
            outcome=(
                m.Cli.ProcessOutcome(
                    raw_return_code=output.outcome.raw_return_code,
                    timed_out=output.outcome.timed_out,
                    forwarded_signal=output.outcome.forwarded_signal,
                )
                if output is not None
                else None
            ),
            error=(
                str(verdict.error)
                if verdict.failure
                else str(after.error)
                if after.failure
                else None
            ),
            audit_before=before.value if before.success else None,
            audit_after=after.value if after.success else None,
        )
        stage = u.Infra.violations_audit_comparison(
            project,
            stage,
            before.value.plan if before.success else None,
        )
        if stage.error and verdict.success:
            verdict = r[bool].fail(stage.error)
        return stage, verdict

    @classmethod
    def _scan_evidence(
        root: Path,
        destination: Path,
    ) -> p.Result[
        t.Triple[
            m.Infra.ModScanReport,
            m.Infra.ModScanEvidenceReceipt,
            m.Infra.ViolationsSweepSources,
        ]
    ]:
        """Authenticate the canonical inventory around a scan and preserve its receipt.

        Returns:
            Full scan, immutable publication, elected plan and source digests.
        """
        result = r[
            t.Triple[
                m.Infra.ModScanReport,
                m.Infra.ModScanEvidenceReceipt,
                m.Infra.ViolationsSweepSources,
            ]
        ]
        captured = FlextInfraRefactorViolationsSweep._source_snapshot(
            root, observe=True
        )
        if captured.failure:
            return result.from_failure(captured)
        snapshot = captured.value
        if snapshot.ast_report is None:
            return result.fail(
                "; ".join(snapshot.observation_errors) or "native AST scan unavailable"
            )
        elected = {
            (project.name, rule_id)
            for project, rules in snapshot.plan.project_rule_ids.items()
            for rule_id in rules
        }
        unexpected = {
            (entry.repository, entry.rule_id) for entry in snapshot.ast_report.entries
        } - elected
        if unexpected:
            return result.fail(
                "native finding outside effective project rule plan: "
                f"{sorted(unexpected)}",
            )
        digests = cls._verify_entry_digests(snapshot.ast_report, snapshot)
        if digests.failure:
            return result.from_failure(digests)
        repositories = tuple(project.name for project in snapshot.repository_roots)
        receipt = u.Infra.publish_mod_scan_evidence(
            root,
            snapshot.ast_report,
            publication=m.Infra.ModScanPublication(
                command=c.Infra.ModScanCommand.SCAN,
                scope=snapshot.scope,
                relative_path=destination,
                repositories=repositories,
                rule_ids=tuple(rule.id for rule in snapshot.plan.rules),
            ),
        )
        if receipt.failure:
            return result.from_failure(receipt)
        return result.ok((
            snapshot.ast_report,
            receipt.value,
            snapshot,
        ))

    @staticmethod
    def _verify_entry_digests(
        report: m.Infra.ModScanReport,
        snapshot: m.Infra.ViolationsSweepSources,
    ) -> p.Result[bool]:
        """Require every native finding to carry its authenticated source digest.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for entry in report.entries:
            state = entry.source_state
            if (
                state is None
                or state.content is None
                or snapshot.sha256.get(str(state.path))
                != u.Cli.sha256_bytes(state.content)
            ):
                return r[bool].fail(
                    f"native finding lacks authenticated source digest: {entry.file}",
                )
        if not snapshot.source_verified:
            return r[bool].fail(
                "; ".join(snapshot.observation_errors) or "native inputs unverified",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _source_snapshot(
        cls,
        root: Path,
        *,
        observe: bool = False,
        previous: m.Infra.ViolationsSweepSources | None = None,
    ) -> p.Result[m.Infra.ViolationsSweepSources]:
        """Read the existing scan inventory without executing another native scan.

        Returns:
            Authenticated source, scope, topology and elected catalog identities.
        """
        inventory = cls._source_inventory(root)
        if inventory.failure:
            return r[m.Infra.ViolationsSweepSources].from_failure(inventory)
        plan, targets, projects, declared = inventory.value
        paths, inventory_errors = cls._scan_source_paths(root, targets, plan)
        captured = cls._read_sources(tuple(sorted(paths)))
        if captured.failure:
            return r[m.Infra.ViolationsSweepSources].from_failure(captured)
        if not observe:
            validated = cls._validate_scan_sources(root, targets, captured.value, plan)
            if validated.failure:
                return r[m.Infra.ViolationsSweepSources].from_failure(validated)
        observed = u.Infra.git_submodule_declarations(root)
        if observed.failure or declared != observed.value:
            return (
                r[m.Infra.ViolationsSweepSources].from_failure(observed)
                if observed.failure
                else r[m.Infra.ViolationsSweepSources].fail(
                    "violations sweep project topology changed during observation",
                )
            )
        snapshot = m.Infra.ViolationsSweepSources(
            source_verified=not observe,
            plan=plan,
            scope=targets,
            states=captured.value,
            repository_roots=projects,
            observation_errors=inventory_errors,
            sha256={
                str(state.path): u.Cli.sha256_bytes(state.content)
                for state in captured.value
                if state.content is not None
            },
        )
        return r[m.Infra.ViolationsSweepSources].ok(
            cls._observed_snapshot(root, snapshot, previous) if observe else snapshot,
        )

    @staticmethod
    def _source_inventory(
        root: Path,
    ) -> p.Result[
        t.Quad[
            m.Infra.CodemodRulePlan,
            t.StrSequence,
            tuple[Path, ...],
            tuple[m.Infra.GitSubmoduleDeclaration, ...],
        ]
    ]:
        """Elect native scope and topology before capturing any file proof.

        Returns:
            Existing owner contracts, or their original preflight failure.
        """
        result = r[
            t.Quad[
                m.Infra.CodemodRulePlan,
                t.StrSequence,
                tuple[Path, ...],
                tuple[m.Infra.GitSubmoduleDeclaration, ...],
            ]
        ]
        planned = u.Infra.codemod_rule_plan(root)
        if planned.failure:
            return result.from_failure(planned)
        targets = u.Infra.ast_grep_scan_targets(root)
        if not targets:
            return result.fail(
                "no governed AST source targets; native rules NOT_EXECUTED"
            )
        declared = u.Infra.git_submodule_declarations(root)
        if declared.failure:
            return result.from_failure(declared)
        projects = (
            root.resolve(),
            *(
                root.resolve() / item.path
                for item in declared.value
                if item.managed is not False
            ),
        )
        if set(projects) != set(planned.value.project_rule_ids) or len({
            project.name for project in projects
        }) != len(projects):
            return result.fail(
                "effective rule plan differs from declared project topology"
            )
        return result.ok((planned.value, targets, projects, tuple(declared.value)))

    @staticmethod
    def _read_sources(
        paths: t.SequenceOf[Path],
    ) -> p.Result[tuple[m.Cli.AtomicFileState, ...]]:
        """Capture required inputs through the canonical authenticated file owner.

        Returns:
            Actual binary states; absent or invalid inputs preserve their failure.
        """
        states: list[m.Cli.AtomicFileState] = []
        for path in paths:
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return r[tuple[m.Cli.AtomicFileState, ...]].from_failure(state)
            if state.value.content is None:
                return r[tuple[m.Cli.AtomicFileState, ...]].fail(
                    f"violations sweep required scan source absent: {path}",
                )
            states.append(state.value)
        return r[tuple[m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @staticmethod
    def _observed_snapshot(
        root: Path,
        snapshot: m.Infra.ViolationsSweepSources,
        previous: m.Infra.ViolationsSweepSources | None,
    ) -> m.Infra.ViolationsSweepSources:
        """Observe native AST, text and Ruff through their existing owners.

        Returns:
            Full native evidence; failed scanners remain explicitly unobserved.
        """
        ast_scan = (
            r[m.Infra.ModScanReport].ok(previous.ast_report)
            if previous is not None
            and previous.ast_report is not None
            and previous.sha256 == snapshot.sha256
            and previous.plan == snapshot.plan
            and previous.scope == snapshot.scope
            else FlextInfraModGateEngine.scan(root, fix=False)
        )
        text_scan = FlextInfraModTextGateEngine.scan(root, fix=False)
        lint = u.Infra.lint_snapshots(
            tuple(
                state.path for state in snapshot.states if state.path.suffix == ".py"
            ),
            root,
            gates=(c.Infra.RUFF,),
        )
        validated = FlextInfraRefactorViolationsSweep._validate_scan_sources(
            root,
            snapshot.scope,
            snapshot.states,
            snapshot.plan,
        )
        return m.Infra.ViolationsSweepSources(
            source_verified=validated.success,
            plan=snapshot.plan,
            scope=snapshot.scope,
            states=snapshot.states,
            repository_roots=snapshot.repository_roots,
            sha256=snapshot.sha256,
            ast_report=ast_scan.value if ast_scan.success else None,
            text_report=text_scan.value if text_scan.success else None,
            lint={str(path): findings for path, findings in lint.items()},
            observation_errors=tuple(snapshot.observation_errors)
            + tuple(
                str(result.error)
                for result in (ast_scan, text_scan, validated)
                if result.failure
            ),
        )

    def _run_rule_audit(
        self,
        project: Path,
        inventory: m.Infra.CodemodRulePlan | None,
        initial: m.Infra.ViolationsSweepSources | None,
    ) -> t.Pair[m.Infra.ViolationsSweepStage, p.Result[bool]]:
        """Read the complete elected catalog for one repository, without Make effects.

        Returns:
            Per-rule dispositions and full collateral evidence for this observation.
        """
        started = monotonic()
        before = self._source_snapshot(project, observe=True, previous=initial)
        after = self._source_snapshot(
            project,
            observe=True,
            previous=before.value if before.success else None,
        )
        failure = before if before.failure else after if after.failure else None
        errors = (
            (str(failure.error),)
            if failure is not None
            else (*before.value.observation_errors, *after.value.observation_errors)
        )
        stage = m.Infra.ViolationsSweepStage(
            repository_root=project.resolve(),
            cwd=self.repository_root.resolve(),
            command=("flext-infra", "refactor", "violations-sweep", "--audit-rules"),
            verb="audit-rules",
            duration=monotonic() - started,
            invoked=True,
            outcome=None,
            error="; ".join(errors) if errors else None,
            audit_before=before.value if before.success else None,
            audit_after=after.value if after.success else None,
        )
        stage = u.Infra.violations_audit_comparison(project, stage, inventory)
        return stage, (
            r[bool].from_failure(failure)
            if failure is not None
            else r[bool].fail(stage.error)
            if stage.error
            else r[bool].ok(value=True)
        )

    @staticmethod
    def _scan_source_paths(
        root: Path,
        targets: t.StrSequence,
        plan: m.Infra.CodemodRulePlan,
    ) -> t.Pair[set[Path], t.StrSequence]:
        """Inventory sources and all declared executable catalog inputs.

        Returns:
            The input closure and independent text-inventory observation errors.
        """
        paths = {rule.resource.resolve() for rule in plan.rules}
        configs = {ruleset.config.resolve() for ruleset in plan.rulesets}
        configs.update(
            path
            for project in plan.project_rule_ids
            for path in (project / c.Infra.CODEMOD_CONFIG_RELPATH,)
            if path.is_file()
        )
        paths.update(configs)
        for config_path in configs:
            directories = FlextInfraCodemodSnapshotReconciler.fixture_directories(
                config_path.parent,
            )
            paths.update(
                path.resolve()
                for directory in (*directories.rule_dirs, *directories.util_dirs)
                for path in directory.rglob("*")
                if path.is_file()
            )
        paths.update(
            project / c.PYPROJECT_FILENAME for project in plan.project_rule_ids
        )
        paths.update(
            path
            for project in plan.project_rule_ids
            for path in (u.Infra.workspace_manifest_path(project),)
            if path.is_file()
        )
        if (root / c.Infra.GITMODULES).exists():
            paths.add((root / c.Infra.GITMODULES).resolve())
        text_paths = FlextInfraModTextGateEngine.source_paths(root)
        if text_paths.success:
            paths.update(text_paths.value)
        for target in targets:
            path = root / target
            paths.update(
                u.Infra.iter_directory_python_files(path) if path.is_dir() else (path,)
            )
        return paths, (str(text_paths.error),) if text_paths.failure else ()

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
        verified = u.Cli.atomic_verify_binary_file_states(states)
        if verified.failure:
            return r[bool].from_failure(verified)
        observed_plan = u.Infra.codemod_rule_plan(root)
        if observed_plan.failure:
            return r[bool].from_failure(observed_plan)
        if plan != observed_plan.value or targets != u.Infra.ast_grep_scan_targets(
            root
        ):
            return r[bool].fail("violations sweep scan rule plan or inventory changed")
        observed_paths, _errors = FlextInfraRefactorViolationsSweep._scan_source_paths(
            root, targets, plan
        )
        if {state.path for state in states} != observed_paths:
            return r[bool].fail("violations sweep scan source inventory changed")
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraRefactorViolationsSweep"]
