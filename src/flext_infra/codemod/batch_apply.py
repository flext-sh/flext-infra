"""Fix-forward ast-grep batch application for ``make mod``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import override

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod import (
    FlextInfraCodemodSemanticApply,
    FlextInfraImportNormalizationPhase,
    FlextInfraModGateEngine,
    FlextInfraModReplacements,
    FlextInfraModTextGateEngine,
)
from flext_infra.refactor import FlextInfraRefactorCensus


class FlextInfraCodemodBatchApply(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Apply guarded rewrites and retain accepted progress for fix-forward."""

    workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl] = (
        m.Field(exclude=True, description="Injected candidate Rope workspace factory")
    )

    source_preview: t.Port[p.Infra.SourcePreview] = m.Field(
        exclude=True,
        description="Injected authenticated source preview capability",
    )
    rename_runner: t.Port[p.Infra.RenameCampaignRunner] = m.Field(
        exclude=True,
        description="Injected CSV campaign execution port",
    )
    progress: t.Port[p.Infra.ModProgress] = m.Field(
        exclude=True,
        description="Injected mod progress transport port",
    )
    rope: t.Port[p.Infra.RopeWorkspaceDsl] = m.Field(
        exclude=True,
        description="Injected Rope workspace port",
    )
    rename_inputs: t.VariadicTuple[m.Infra.ApplyRenamesInput] = m.Field(
        exclude=True,
        default=(),
        description="Typed declared CSV campaigns",
    )
    phase_callbacks: t.VariadicTuple[t.Port[p.Infra.ModLoopPhase]] = m.Field(
        exclude=True,
        default=(),
        description=(
            "Injected repair phases the loop invokes as callbacks between the"
            " semantic and text phases (namespace relocations, accessor"
            " renames)"
        ),
    )
    consumer_roots: t.VariadicTuple[Path] = m.Field(
        default=(),
        description="Explicit read scopes; not additional syntax targets",
    )
    rename_plan: Path | None = m.Field(
        default=None,
        description="Optional native candidate composed before publication",
    )

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Inspect or apply the complete rule cascade with visible phases.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        if any(
            not root.is_absolute() or not root.is_dir() for root in self.consumer_roots
        ):
            return r[t.Cli.ResultValue].fail(
                "consumer roots must be existing absolute checkout roots"
            )
        planned = u.Infra.codemod_rule_plan(self.repository_root)
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        rules = tuple(dict.fromkeys(rule.resource for rule in planned.value.rules))
        if self.effective_dry_run:
            return self._execute_dry_run(rules)
        return self._execute_apply(rules)

    def _execute_dry_run(
        self,
        rules: t.SequenceOf[Path],
    ) -> p.Result[t.Cli.ResultValue]:
        """Report every pending finding without applying any phase.

        Returns:
            The inspection verdict over the discovered rule cascade.

        """
        self.progress.emit(f"mod: scan {len(rules)} discovered rule file(s)")
        pending = FlextInfraModGateEngine.scan(
            self.repository_root,
            fix=False,
        ).unwrap()
        if self.rename_plan is not None:
            preview = self._advance_phases(
                self.repository_root,
                self.rope,
                pending,
                text_precondition_pending=True,
                publish=False,
            )
            if preview.failure:
                return r[t.Cli.ResultValue].from_failure(preview)
        pending_count = pending.findings
        text_pending = FlextInfraModTextGateEngine.scan(
            self.repository_root,
            fix=False,
            validate_receipts=True,
        ).unwrap()
        pending_count += text_pending.findings
        renames_pending = self._pending_renames()
        if renames_pending.failure:
            return r[t.Cli.ResultValue].from_failure(renames_pending)
        if pending_count or renames_pending.value:
            return r[t.Cli.ResultValue].fail(
                f"{pending.findings} pending ast-grep finding(s), "
                f"{pending.actionable} actionable and "
                f"{pending.detection_only} detection-only and "
                f"{pending.non_actionable_with_fix} non-actionable with fix, plus "
                f"{text_pending.findings} pending sed-by-list finding(s) "
                f"({text_pending.actionable} actionable) and "
                f"{renames_pending.value} pending CSV-rename occurrence(s), "
                f"across {len(rules)} rule file(s)",
            )
        self.progress.emit("mod: no pending ast-grep or sed-by-list fixes")
        return r[t.Cli.ResultValue].ok(value=True)

    def _execute_apply(self, rules: t.SequenceOf[Path]) -> p.Result[t.Cli.ResultValue]:
        """Converge AST, semantic, and text phases over the same source state.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        self.progress.emit("mod: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(
            self.repository_root,
            rules,
        ).unwrap()
        result = self._execute_apply_cycle(text_precondition_pending=True)
        if result.failure:
            return result
        self.progress.emit("mod: verify the workspace constants census")
        census_runner = FlextInfraRefactorCensus(
            workspace_factory=self.workspace_factory,
            source_preview=self.source_preview,
            repository_root=self.repository_root,
            apply_changes=False,
            options=m.Infra.CensusOptions(
                families=("c",),
                rules=(
                    c.Infra.CensusRule.CONSTANT_CONSUMERS,
                    c.Infra.CensusRule.DUPLICATE,
                    c.Infra.CensusRule.WRONG_TIER,
                ),
            ),
        )
        census = census_runner.build_report()
        self.progress.emit(
            "mod: constants census "
            f"projects={len(census.projects)} "
            f"objects={census.total_objects} "
            f"violations={census.total_violations} "
            f"rewritten_files={census.constant_consumer_files} "
            f"rewritten_bindings={census.constant_consumer_bindings}",
        )
        if census.total_violations:
            return r[t.Cli.ResultValue].fail(
                f"mod: constants census retains {census.total_violations} violation(s)"
            )
        return result

    def _plan_ast_phase(
        self,
        root: Path,
        current: m.Infra.ModScanReport,
        seed: m.Infra.StageSourcePlan,
    ) -> m.Infra.StageSourcePlan:
        """Compose syntax fixes without publishing the original producer epoch.

        Returns:
            The complete all-root candidate with target-only syntax effects.

        Raises:
            RuntimeError: If the syntax cascade repeats a source state.

        """
        after_ast = FlextInfraModGateEngine.authored(current)
        plans: dict[Path, m.Infra.SemanticFilePlan] = {}
        inputs = {state.path: state for state in seed.inputs}
        if seed.updates:
            after_ast = FlextInfraModGateEngine.authored(
                self._preview_ast_candidate(root, plans, inputs, seed)
            )
        if after_ast.actionable:
            self._capture_ast_inputs(root, inputs)
        seen: set[t.VariadicTuple[t.Pair[str, str]]] = set()
        while after_ast.actionable:
            state = tuple(
                sorted(
                    (str(path), plan.desired_content.hex())
                    for path, plan in plans.items()
                    if plan.desired_content is not None
                )
            )
            if state in seen:
                msg = "mod syntax cascade cycle before semantic publication"
                raise RuntimeError(msg)
            seen.add(state)
            before_ast = after_ast
            wave = FlextInfraModReplacements.compose(root, after_ast).unwrap()
            for plan in wave:
                original = plans.get(plan.path)
                if plan.path not in plans:
                    inputs.setdefault(plan.path, plan.before)
                plans[plan.path] = plan.model_copy(
                    update={
                        "before": (
                            inputs[plan.path] if original is None else original.before
                        ),
                        "changes": (
                            plan.changes
                            if original is None
                            else (*original.changes, *plan.changes)
                        ),
                    }
                )
            after_ast = FlextInfraModGateEngine.authored(
                self._preview_ast_candidate(root, plans, inputs, seed)
            )
            FlextInfraCodemodBatchApply.validate_fix_match(before_ast, after_ast)
        if plans:
            accepted = FlextInfraModReplacements.admit(
                root, tuple(plans.values())
            ).unwrap()
            return FlextInfraStagedPackage.plan_sources(
                seed.workspace,
                {
                    **seed.updates,
                    **{
                        plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                        for plan in accepted
                        if plan.desired_content is not None
                    },
                },
                options=m.Infra.StageSourceOptions(
                    inputs=tuple(inputs.values()),
                    workspaces=seed.workspaces,
                    modes=seed.modes,
                ),
            ).unwrap()
        return seed

    @staticmethod
    def _capture_ast_inputs(
        root: Path, inputs: MutableMapping[Path, m.Cli.AtomicFileState]
    ) -> None:
        """Authenticate every syntax target before composing the first wave.

        Raises:
            ValueError: If a captured source changed after global capture.

        """
        for target in u.Infra.ast_grep_scan_targets(root):
            path = root / target
            paths = (
                u.Infra.iter_directory_python_files(path) if path.is_dir() else (path,)
            )
            for source in paths:
                captured = u.Cli.atomic_read_binary_file_state(
                    source, required=True
                ).unwrap()
                if inputs.setdefault(source.resolve(), captured) != captured:
                    msg = f"syntax input changed after global capture: {source}"
                    raise ValueError(msg)

    def _preview_ast_candidate(
        self,
        root: Path,
        plans: t.MappingKV[Path, m.Infra.SemanticFilePlan],
        inputs: MutableMapping[Path, m.Cli.AtomicFileState],
        seed: m.Infra.StageSourcePlan,
    ) -> m.Infra.ModScanReport:
        """Bind each wave's authenticated plan to its transactional scan.

        Returns:
            The full-catalog report for this candidate's staged bytes.

        """
        candidate = FlextInfraStagedPackage.plan_sources(
            seed.workspace,
            {
                **seed.updates,
                **{
                    path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                    for path, plan in plans.items()
                    if plan.desired_content is not None
                },
            },
            options=m.Infra.StageSourceOptions(
                inputs=tuple(inputs.values()),
                workspaces=seed.workspaces,
                modes=seed.modes,
            ),
        ).unwrap()
        for source in candidate.inputs:
            inputs.setdefault(source.path, source)

        def scan(
            view_root: Path, _paths: t.MappingKV[Path, Path]
        ) -> m.Infra.ModScanReport:
            del _paths
            return FlextInfraModGateEngine.scan_candidate(
                root, view_root, candidate
            ).unwrap()

        return self.source_preview.preview_sources(
            candidate.workspace,
            candidate.updates,
            scan,
            options=m.Infra.CodegenSourcePreviewOptions(
                inputs=candidate.inputs,
                workspaces=candidate.workspaces,
                modes=candidate.modes,
                runtime_check=False,
            ),
        ).unwrap()

    @staticmethod
    def _plan_text_phase(
        root: Path,
        candidate: m.Infra.SemanticSourcePlan,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Compose declared text effects over the current staged view.

        Returns:
            The staged view carrying the text effects.

        """
        sources = dict(
            u.Infra.candidate_python_sources(
                candidate.candidate, candidate.candidate.inputs
            )
        )
        for path, source in candidate.candidate.updates.items():
            if source is None:
                sources.pop(path, None)
            else:
                sources[path] = source
        planned = FlextInfraModTextGateEngine.plan(
            root,
            sources=sources,
            validate_receipts=text_precondition_pending,
        )
        if planned.failure:
            return r[m.Infra.SemanticSourcePlan].from_failure(planned)
        return FlextInfraCodemodSemanticApply.compose_candidate(
            candidate, planned.value[1]
        )

    def _apply_renames(self) -> p.Result[bool]:
        """Apply every declared CSV rename campaign in declared order.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for rename_params in self.rename_inputs:
            renamed = self.rename_runner.run(rename_params)
            if renamed.failure:
                return r[bool].from_failure(renamed)
            self.progress.emit_rename(renamed.value)
        return r[bool].ok(value=True)

    def _advance_phases(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        current: m.Infra.ModScanReport,
        *,
        text_precondition_pending: bool,
        publish: bool = True,
    ) -> p.Result[
        t.Pair[
            m.Infra.ModScanReport,
            t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]],
        ]
    ]:
        """Run the AST, semantic, callback, text, and rename phases once.

        Returns:
            The resulting post-phase scan report plus the fingerprint states the
            fixed-point check must observe for cross-phase cycle detection.

        """
        outcome = r[
            t.Pair[
                m.Infra.ModScanReport,
                t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]],
            ]
        ]
        fingerprint = FlextInfraCodemodSemanticApply.source_fingerprint
        phase_states = [fingerprint(root, current)]
        seeded = self._phase_seed(root, rope_workspace)
        if seeded.failure:
            return outcome.from_failure(seeded)
        prepared = self._prepare_phase_seed(
            root,
            current,
            seeded.value,
            text_precondition_pending=text_precondition_pending,
        )
        if prepared.failure:
            return outcome.from_failure(prepared)
        semantic = self._plan_semantic_phase(root, prepared.value)
        if semantic.failure:
            return outcome.from_failure(semantic)
        accepted = self._publish_phase_candidate(root, semantic.value, publish=publish)
        if accepted.failure:
            return outcome.from_failure(accepted)
        return self._finish_phases(
            root, rope_workspace, current, (publish, phase_states)
        )

    def _publish_phase_candidate(
        self,
        root: Path,
        seed: m.Infra.SemanticSourcePlan,
        *,
        publish: bool,
    ) -> p.Result[bool]:
        """Compose final callbacks and text before publishing one candidate.

        Returns:
            The native publication result or the first planning failure.

        """
        callbacks = self._plan_phase_callbacks(root, seed)
        if callbacks.failure:
            return r[bool].from_failure(callbacks)
        text = self._plan_text_phase(
            root, callbacks.value, text_precondition_pending=False
        )
        if text.failure:
            return r[bool].from_failure(text)
        return FlextInfraCodemodSemanticApply.publish_candidate(
            root, text.value, publish=publish
        )

    def _phase_seed(
        self, root: Path, rope_workspace: p.Infra.RopeWorkspaceDsl
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Load an explicit rename artifact or capture a source campaign.

        Returns:
            The native seed, or the first loading or planning failure.

        """
        if self.rename_plan is None:
            return FlextInfraCodemodSemanticApply.build_source_plan(
                root, self.consumer_roots
            ).flat_map(
                lambda seed: FlextInfraCodemodSemanticApply.plan_module_names(
                    root, seed
                )
            )
        loaded = FlextInfraCodemodSemanticApply.load_rename_artifact(
            root,
            m.Infra.ModCommand(repository_root=root, rename_plan=self.rename_plan),
        )
        if loaded.failure:
            return r[m.Infra.SemanticSourcePlan].from_failure(loaded)
        seed, driver = loaded.value
        current = FlextInfraCodemodSemanticApply.authenticate_rename_candidate(
            root, seed, driver, rope_workspace
        )
        if current.failure:
            return r[m.Infra.SemanticSourcePlan].from_failure(current)
        if self.consumer_roots and set(self.consumer_roots) != set(seed.consumer_roots):
            return r[m.Infra.SemanticSourcePlan].fail(
                "run consumer roots differ from the native rename artifact"
            )
        return r[m.Infra.SemanticSourcePlan].ok(seed)

    def _prepare_phase_seed(
        self,
        root: Path,
        current: m.Infra.ModScanReport,
        seed: m.Infra.SemanticSourcePlan,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Compose syntax, initial text effects and import normalization.

        Returns:
            The prepared seed, or the first planning failure.

        """
        seed = seed.model_copy(
            update={"candidate": self._plan_ast_phase(root, current, seed.candidate)}
        )
        text_preparation = self._plan_text_phase(
            root,
            seed,
            text_precondition_pending=text_precondition_pending,
        )
        if text_preparation.failure:
            return text_preparation
        return self._plan_phase_callbacks(
            root,
            text_preparation.value,
            callbacks=(FlextInfraImportNormalizationPhase(),),
        )

    def _plan_semantic_phase(
        self,
        root: Path,
        seed: m.Infra.SemanticSourcePlan,
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Compose all native semantic effects on the prepared candidate.

        Returns:
            The staged semantic candidate.

        """
        outcome = r[m.Infra.SemanticSourcePlan]
        syntax = seed.candidate
        semantic_preflight = self._preview_ast_candidate(
            root,
            {},
            {state.path: state for state in syntax.inputs},
            syntax,
        )
        original = u.Infra.candidate_python_sources(syntax, seed.candidate.inputs)
        working = dict(original)
        for path, source in syntax.updates.items():
            if path.suffix not in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}:
                continue
            if source is None:
                working.pop(path)
            else:
                working[path] = source
        with FlextInfraCodemodSemanticApply.planning_workspace(
            root, seed, working
        ) as graph:
            changed: set[Path] = set()
            constants = FlextInfraCodemodSemanticApply.plan_census_constants(
                root,
                graph,
                sources=working,
            )
            if constants.failure:
                return outcome.from_failure(constants)
            FlextInfraCodemodSemanticApply.apply_plan(working, constants.value, changed)
            transaction_paths = u.Infra.plan_transaction_path_cutover(
                rope_workspace=graph,
                sources=working,
            )
            FlextInfraCodemodSemanticApply.apply_plan(
                working, transaction_paths, changed
            )
            semantic = FlextInfraCodemodSemanticApply.plan(
                root,
                FlextInfraModGateEngine.authored(semantic_preflight),
                graph,
                working,
            )
            if semantic.failure:
                return outcome.from_failure(semantic)
            FlextInfraCodemodSemanticApply.apply_plan(working, semantic.value, changed)
        updates = dict(syntax.updates)
        updates.update({
            path: source
            for path, source in working.items()
            if original.get(path) != source
        })
        return FlextInfraStagedPackage.plan_sources(
            seed.candidate.workspace,
            updates,
            options=m.Infra.StageSourceOptions(
                inputs=seed.candidate.inputs,
                workspaces=seed.candidate.workspaces,
                modes=seed.candidate.modes,
            ),
        ).map(lambda staged: seed.model_copy(update={"candidate": staged}))

    def _finish_phases(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        current: m.Infra.ModScanReport,
        publication: t.Pair[bool, list[t.VariadicTuple[t.Pair[str, str]]]],
    ) -> p.Result[
        t.Pair[m.Infra.ModScanReport, t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]]]
    ]:
        """Refresh and scan a published candidate before applying CSV campaigns.

        Returns:
            The post-publication report and its observed fingerprint sequence.

        """
        outcome = r[
            t.Pair[
                m.Infra.ModScanReport, t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]]
            ]
        ]
        publish, phase_states = publication
        if not publish:
            return outcome.ok((current, tuple(phase_states)))
        self.rename_plan = None
        rope_workspace.refresh()
        after_ast = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        phase_states.append(
            FlextInfraCodemodSemanticApply.source_fingerprint(root, after_ast)
        )
        # Exact optional migration receipts apply once per invocation,
        # not to every internal convergence pass after consuming matches.
        renames = self._apply_renames()
        if renames.failure:
            return outcome.from_failure(renames)
        return outcome.ok((after_ast, tuple(phase_states)))

    def _emit_residuals(
        self,
        current: m.Infra.ModScanReport,
        current_text: m.Infra.ModTextReport,
    ) -> None:
        """Report residual owners without waiving their final gate failures."""
        generated = FlextInfraModReplacements.generator_owned(current.entries)
        if generated:
            self.progress.emit(
                f"mod: {len(generated)} generated finding(s) remain for "
                f"canonical generator repair: {', '.join(generated)}",
            )
        if current.detection_only or current.non_actionable_with_fix:
            detection_rules = sorted({
                finding.rule_id for finding in current.entries if not finding.actionable
            })
            self.progress.emit(
                f"mod: {current.detection_only} detection-only and "
                f"{current.non_actionable_with_fix} non-actionable with fix "
                f"finding(s) remain for owner repair: {', '.join(detection_rules)}",
            )
        if current_text.findings:
            text_rules = sorted({entry.rule_id for entry in current_text.entries})
            self.progress.emit(
                f"mod: {current_text.findings} detection-only sed-by-list "
                f"finding(s) remain for owner repair: {', '.join(text_rules)}",
            )

    def _verdict_message(
        self,
        root: Path,
        baseline_cycles: t.SequenceOf[frozenset[str]],
        states: t.Pair[
            t.VariadicTuple[t.Pair[str, str]],
            t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]],
        ],
        reports: t.Pair[m.Infra.ModScanReport, m.Infra.ModTextReport],
    ) -> str | None:
        """Judge the converged fixed point and report residual owner repairs.

        Returns:
            The fixed-point failure message, or ``None`` when the joint AST,
            semantic, and text fixed point is verified with zero remaining
            findings and no new runtime import cycles.

        """
        before, phase_states = states
        current, current_text = reports
        # Cyclic-import regression gate: a refactor phase that closed a
        # new runtime import cycle fails the fixed point loud — zero new
        # cycles is an acceptance condition, and cycles the tree already
        # had stay check's existing verdict.
        if any(state != before for state in phase_states):
            return "mod cross-phase cycle returned to its starting source state"
        if current.actionable or current_text.actionable:
            return (
                "mod made no progress with "
                f"{current.actionable} AST and {current_text.actionable} text "
                "actionable findings"
            )
        self._emit_residuals(current, current_text)
        converged_cycles = self._import_cycles(root)
        new_cycles = [
            cycle for cycle in converged_cycles if cycle not in baseline_cycles
        ]
        if new_cycles:
            return "mod introduced new runtime import cycle(s): " + "; ".join(
                " -> ".join(sorted(cycle)) for cycle in new_cycles
            )
        if current.findings or current_text.findings:
            return (
                f"mod: fixed point retains {current.findings} AST finding(s) "
                f"({current.detection_only} detection-only, "
                f"{current.non_actionable_with_fix} non-actionable with fix) and "
                f"{current_text.findings} text finding(s); owner repair required"
            )
        return None

    def _execute_apply_cycle(
        self,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[t.Cli.ResultValue]:
        """Converge every mod phase while retaining accepted progress.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        root = self.repository_root
        current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        return self._converge(
            root,
            current,
            text_precondition_pending=text_precondition_pending,
        )

    def _converge(
        self,
        root: Path,
        current: m.Infra.ModScanReport,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[t.Cli.ResultValue]:
        """Converge every mod phase through one shared Rope workspace.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        rope_workspace = self.rope
        baseline_cycles = self._import_cycles(root)
        fingerprint = FlextInfraCodemodSemanticApply.source_fingerprint
        seen: MutableMapping[t.VariadicTuple[t.Pair[str, str]], int] = {}
        iteration = 0
        while True:
            iteration += 1
            before = fingerprint(root, current)
            if before in seen:
                return r[t.Cli.ResultValue].fail(
                    f"mod cross-phase cycle at iteration {iteration}; "
                    f"source state repeats iteration {seen[before]}",
                )
            seen[before] = iteration
            self.progress.emit(
                f"mod: joint iteration {iteration} — "
                f"{current.actionable} actionable, "
                f"{current.detection_only} detection-only",
            )
            advanced = self._advance_phases(
                root,
                rope_workspace,
                current,
                text_precondition_pending=text_precondition_pending,
            )
            if advanced.failure:
                return r[t.Cli.ResultValue].from_failure(advanced)
            _after_ast, phase_states = advanced.value
            text_precondition_pending = False
            current = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
            current_text = FlextInfraModTextGateEngine.scan(root, fix=False).unwrap()
            after = fingerprint(root, current)
            if after != before:
                continue
            message = self._verdict_message(
                root,
                baseline_cycles,
                (before, phase_states),
                (current, current_text),
            ) or self._relocation_verdict(root, rope_workspace, current)
            if message is not None:
                return r[t.Cli.ResultValue].fail(message)
            self.progress.emit(
                "mod: joint AST, semantic, and text fixed point verified "
                "with zero AST/text findings",
            )
            return r[t.Cli.ResultValue].ok(value=True)

    def _relocation_verdict(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        current: m.Infra.ModScanReport,
    ) -> str | None:
        """Report each unresolved declaration relocation as its own finding.

        An unresolved owner is a finding of that declaration, never a plan
        crash; accepted writes remain available for the next fix-forward pass.

        Returns:
            The failure message naming every unresolved declaration, or
            ``None`` when every payload declaration has a resolved owner.

        """
        findings = FlextInfraCodemodSemanticApply.relocation_findings(
            root,
            FlextInfraModGateEngine.authored(current),
            rope_workspace,
        )
        for finding in findings:
            self.progress.emit(
                "mod: declaration-relocation finding "
                f"{finding.file_path}:{finding.declaration} "
                f"expected owner {finding.expected_owner}: {finding.reason}",
            )
        if not findings:
            return None
        return (
            f"mod: {len(findings)} declaration-relocation finding(s) remain for "
            "owner repair"
        )

    @staticmethod
    def _import_cycles(root: Path) -> t.SequenceOf[frozenset[str]]:
        """Collect every runtime import cycle over the governed projects.

        The graph comes from the codemod project's Rope module-level import
        table — only imports that run at module load can form a cycle, so a
        lazy (function-local) import never registers as one.

        Returns:
            The resulting ``t.FrozenSet[t.FrozenSet[str]]``.

        """
        cycles: set[frozenset[str]] = set()
        for project_root in u.Infra.governed_project_roots(root):
            if not u.Infra.namespace_enabled(project_root):
                continue
            graph, _modules = u.Infra.project_import_graph(
                project_root,
            )
            cycles.update(
                frozenset(members)
                for members in u.Infra.project_import_cycles(
                    graph,
                ).values()
            )
        return tuple(sorted(cycles, key=sorted))

    def _plan_phase_callbacks(
        self,
        root: Path,
        candidate: m.Infra.SemanticSourcePlan,
        *,
        callbacks: t.SequenceOf[p.Infra.ModLoopPhase] | None = None,
    ) -> p.Result[m.Infra.SemanticSourcePlan]:
        """Compose callback effects in order over the staged view.

        Returns:
            The latest staged view, or the first planning failure.

        """
        for callback in self.phase_callbacks if callbacks is None else callbacks:
            self.progress.emit(f"mod: plan phase {callback.name}")
            sources = u.Infra.candidate_python_sources(
                candidate.candidate, candidate.candidate.inputs
            )
            for path, source in candidate.candidate.updates.items():
                if path.suffix not in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}:
                    continue
                if source is None:
                    sources.pop(path, None)
                else:
                    sources[path] = source
            preflight = self._preview_ast_candidate(
                root,
                {},
                {state.path: state for state in candidate.candidate.inputs},
                candidate.candidate,
            )
            with FlextInfraCodemodSemanticApply.planning_workspace(
                root, candidate, sources
            ) as graph:
                planned = callback.plan(root, preflight, graph, sources=sources)
            if planned.failure:
                return r[m.Infra.SemanticSourcePlan].from_failure(planned)
            composed = FlextInfraCodemodSemanticApply.compose_candidate(
                candidate, planned.value
            )
            if composed.failure:
                return composed
            candidate = composed.value
        return r[m.Infra.SemanticSourcePlan].ok(candidate)

    def _pending_renames(self) -> p.Result[int]:
        """Count pending rename occurrences across the configured campaigns.

        Returns:
            The resulting ``p.Result[int]``.

        """
        pending = 0
        for params in self.rename_inputs:
            report = self.rename_runner.run(params)
            if report.failure:
                return r[int].from_failure(report)
            pending += report.value.occurrences
        return r[int].ok(pending)

    @staticmethod
    def validate_fix_match[FindingT: m.Infra.ModOccurrence](
        before: m.Infra.ModOccurrenceReport[FindingT],
        after_apply: m.Infra.ModOccurrenceReport[FindingT],
    ) -> None:
        """Reject unresolved rewrites while preserving valid rule cascades.

        Raises:
            RuntimeError: If fix!=match.

        """
        # Check that actionable findings were actually resolved
        before_actionable = {
            (f.rule_id, f.file.as_posix(), f.text, f.replacement)
            for f in before.entries
            if f.actionable
        }
        after_apply_actionable = {
            (f.rule_id, f.file.as_posix(), f.text, f.replacement)
            for f in after_apply.entries
            if f.actionable
        }
        # Actionable findings should be resolved
        unresolved = before_actionable & after_apply_actionable
        if unresolved:
            rule_ids = {r for r, _, _, _ in unresolved}
            files = {p for _, p, _, _ in unresolved}
            msg = (
                f"fix!=match: ast-grep apply did not resolve {len(unresolved)} "
                f"actionable findings in rules {sorted(rule_ids)} "
                f"across files {sorted(files)}"
            )
            raise RuntimeError(msg)
        # A completed rule may enable a later rule in the declared cascade.
        # Those later-rule findings are consumed by the next fixed-point iteration.
        new_actionable = after_apply_actionable - before_actionable
        prior_rule_ids = {rule_id for rule_id, _, _, _ in before_actionable}
        unexpected = {
            finding for finding in new_actionable if finding[0] in prior_rule_ids
        }
        if unexpected:
            rule_ids = {r for r, _, _, _ in unexpected}
            files = {p for _, p, _, _ in unexpected}
            msg = (
                f"fix!=match: ast-grep apply introduced {len(unexpected)} new "
                f"actionable findings in rules {sorted(rule_ids)} "
                f"across files {sorted(files)}"
            )
            raise RuntimeError(msg)


__all__: list[str] = ["FlextInfraCodemodBatchApply"]
