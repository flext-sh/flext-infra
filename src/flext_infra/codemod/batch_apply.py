"""Fix-forward ast-grep batch application for ``make mod``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import override

from flext_infra import FlextInfraServiceBase, c, m, p, r, t, u
from flext_infra.codegen.staged_package import FlextInfraStagedPackage
from flext_infra.codemod import (
    FlextInfraCodemodSemanticApply,
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
            self.progress.emit(f"mod: scan {len(rules)} discovered rule file(s)")
            pending = FlextInfraModGateEngine.scan(
                self.repository_root,
                fix=False,
            ).unwrap()
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
        return self._execute_apply(rules)

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
            for target in u.Infra.ast_grep_scan_targets(root):
                path = root / target
                paths = (
                    u.Infra.iter_directory_python_files(path)
                    if path.is_dir()
                    else (path,)
                )
                for source in paths:
                    captured = u.Cli.atomic_read_binary_file_state(
                        source, required=True
                    ).unwrap()
                    if inputs.setdefault(source.resolve(), captured) != captured:
                        msg = f"syntax input changed after global capture: {source}"
                        raise ValueError(msg)
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
                for source in (plan.before, *plan.source_states):
                    if source.path not in plans:
                        inputs.setdefault(source.path, source)
                plans[plan.path] = (
                    plan.model_copy(update={"before": inputs[plan.path]})
                    if original is None
                    else plan.model_copy(
                        update={
                            "before": original.before,
                            "changes": (*original.changes, *plan.changes),
                        }
                    )
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
                inputs=tuple(inputs.values()),
                workspaces=seed.workspaces,
                modes=seed.modes,
            ).unwrap()
        return seed

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
            inputs=tuple(inputs.values()),
            workspaces=seed.workspaces,
            modes=seed.modes,
        ).unwrap()
        for source in candidate.inputs:
            inputs.setdefault(source.path, source)

        def scan(
            view_root: Path, _paths: t.MappingKV[Path, Path]
        ) -> m.Infra.ModScanReport:
            return FlextInfraModGateEngine.scan_candidate(
                root, view_root, candidate
            ).unwrap()

        return self.source_preview.preview_sources(
            candidate.workspace,
            candidate.updates,
            scan,
            inputs=candidate.inputs,
            workspaces=candidate.workspaces,
            runtime_check=False,
        ).unwrap()

    @staticmethod
    def _apply_text_phase(
        root: Path,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[bool]:
        """Run the sed-by-list phase once, honoring first-pass exact receipts.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        current_text = FlextInfraModTextGateEngine.scan(
            root,
            fix=False,
            validate_receipts=text_precondition_pending,
        ).unwrap()
        if current_text.actionable:
            applied = FlextInfraModTextGateEngine.scan(
                root,
                fix=True,
                validate_receipts=text_precondition_pending,
            )
            if applied.failure:
                return r[bool].from_failure(applied)
        return r[bool].ok(value=True)

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
        driver = None
        if self.rename_plan is not None:
            loaded = FlextInfraCodemodSemanticApply._load_rename_artifact(
                root,
                m.Infra.ModCommand(repository_root=root, rename_plan=self.rename_plan),
            )
            if loaded.failure:
                return outcome.from_failure(loaded)
            seed, driver = loaded.value
            authenticated = (
                FlextInfraCodemodSemanticApply._authenticate_rename_candidate(
                    root, seed, driver
                )
            )
            if authenticated.failure:
                return outcome.from_failure(authenticated)
            rebuilt = FlextInfraCodemodSemanticApply.build_rename_plan(
                root,
                rope_workspace,
                FlextInfraCodemodSemanticApply.rename_selections(seed),
            )
            if rebuilt.failure:
                return outcome.from_failure(rebuilt)
            if rebuilt.value != seed:
                return outcome.fail(
                    "semantic rename artifact differs from current native plan"
                )
            if self.consumer_roots and set(self.consumer_roots) != set(
                seed.consumer_roots
            ):
                return outcome.fail(
                    "run consumer roots differ from the authenticated native artifact"
                )
        else:
            captured = FlextInfraCodemodSemanticApply.build_rename_plan(
                root,
                rope_workspace,
                m.Infra.SemanticRenameSelections(
                    decisions=(), consumer_roots=self.consumer_roots
                ),
            )
            if captured.failure:
                return outcome.from_failure(captured)
            seed = captured.value
        syntax = self._plan_ast_phase(root, current, seed.candidate)
        source_epoch = u.Infra.codemod_source_epoch(
            m.Infra.CodemodBindingSnapshot(states=seed.candidate.inputs)
        )
        original = dict(source_epoch.sources)
        working = dict(original)
        for path, source in syntax.updates.items():
            if source is None:
                working.pop(path)
            else:
                working[path] = source
        with FlextInfraCodemodSemanticApply.planning_workspace(
            root, seed, working
        ) as graph:
            with graph.rope_project.source_consumption():
                changed: set[Path] = set()
                transaction_paths = u.Infra.plan_transaction_path_cutover(
                    rope_workspace=graph,
                    sources=working,
                )
                FlextInfraCodemodSemanticApply._apply_plan(
                    working, transaction_paths, changed
                )
                semantic = FlextInfraCodemodSemanticApply.plan(
                    root,
                    FlextInfraModGateEngine.authored(current),
                    graph,
                    working,
                )
                if semantic.failure:
                    return outcome.from_failure(semantic)
                FlextInfraCodemodSemanticApply._apply_plan(
                    working, semantic.value, changed
                )
            source_states = m.Infra.CodemodBindingSnapshot(
                states=(
                    *seed.source_states,
                    *graph.rope_project.consumed_source_states(),
                    *((driver,) if driver is not None else ()),
                )
            ).states
            directories, topology = u.Cli.atomic_merge_directory_query_receipts(
                (
                    *seed.source_directories,
                    *graph.rope_project.consumed_source_directories(),
                ),
                (
                    *seed.source_query_topology,
                    *graph.rope_project.consumed_source_topology(),
                ),
            )
        updates = dict(syntax.updates)
        updates.update({
            path: source
            for path, source in working.items()
            if original.get(path) != source
        })
        staged = FlextInfraStagedPackage.plan_sources(
            seed.candidate.workspace,
            updates,
            inputs=seed.candidate.inputs,
            workspaces=seed.candidate.workspaces,
            modes=seed.candidate.modes,
        )
        if staged.failure:
            return outcome.from_failure(staged)
        candidate = seed.model_copy(
            update={
                "candidate": staged.value,
                "source_states": source_states,
                "source_directories": directories,
                "source_query_topology": topology,
            }
        )
        accepted = FlextInfraCodemodSemanticApply.publish_candidate(root, candidate)
        if accepted.failure:
            return outcome.from_failure(accepted)
        self.rename_plan = None
        rope_workspace.refresh()
        after_ast = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
        phase_states.append(fingerprint(root, after_ast))
        # Callback phases extend the joint fixed point with repairs that
        # own their own engines (the shared relocation cascade, the
        # origin-aware accessor rename); each returns whether it changed
        # sources, and the loop refreshes and rescans exactly as for its
        # built-in phases.
        callback_state = self._apply_phase_callbacks(
            root,
            after_ast,
            rope_workspace,
        )
        if callback_state.failure:
            return outcome.from_failure(callback_state)
        after_ast, callback_states = callback_state.value
        phase_states.extend(callback_states)
        text_phase = self._apply_text_phase(
            root,
            text_precondition_pending=text_precondition_pending,
        )
        if text_phase.failure:
            return outcome.from_failure(text_phase)
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

    def _apply_phase_callbacks(
        self,
        root: Path,
        after_ast: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[
        t.Pair[
            m.Infra.ModScanReport,
            t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]],
        ]
    ]:
        """Run every injected repair phase and return the post-phase scan state.

        Returns:
            The resulting ``p.Result[t.Pair[m.Infra.ModScanReport,
                t.SequenceOf[...]]]`` — the rescan report plus the fingerprint
            states the cycle must observe for cross-phase cycle detection.

        """
        fingerprint = FlextInfraCodemodSemanticApply.source_fingerprint
        outcome = r[
            t.Pair[
                m.Infra.ModScanReport,
                t.SequenceOf[t.VariadicTuple[t.Pair[str, str]]],
            ]
        ]
        states: list[t.VariadicTuple[t.Pair[str, str]]] = []
        for callback in self.phase_callbacks:
            self.progress.emit(f"mod: phase {callback.name} start")
            phase_changed = callback.apply(root, after_ast, rope_workspace)
            if phase_changed.failure:
                return outcome.from_failure(phase_changed)
            self.progress.emit(
                f"mod: phase {callback.name} finish changed={phase_changed.value}",
            )
            if not phase_changed.value:
                continue
            self.progress.emit(f"mod: phase {callback.name} changed sources")
            rope_workspace.refresh()
            after_ast = FlextInfraModGateEngine.scan(root, fix=False).unwrap()
            states.append(fingerprint(root, after_ast))
        return outcome.ok((after_ast, tuple(states)))

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
