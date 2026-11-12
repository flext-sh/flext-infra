"""Fix-forward ast-grep batch application for ``make mod``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import override

from flext_infra import c, m, p, r, s, t, u
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod import (
    FlextInfraCodemodSemanticApply,
    FlextInfraModGateEngine,
    FlextInfraModReplacements,
    FlextInfraModTextGateEngine,
)
from flext_infra.codemod.loop import FlextInfraCodemodLoopPhaseImportNormalization
from flext_infra.refactor import FlextInfraRefactorCensus


class FlextInfraCodemodBatchApply(s[t.Cli.ResultValue]):
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
    rename_inputs: tuple[t.Port[p.Infra.ApplyRenamesInput], ...] = m.Field(
        exclude=True,
        default=(),
        description="Typed declared CSV campaigns",
    )
    phase_callbacks: tuple[t.Port[p.Infra.ModLoopPhase], ...] = m.Field(
        exclude=True,
        default=(),
        description=(
            "Injected repair phases the loop invokes as callbacks between the"
            " semantic and text phases (namespace relocations, accessor"
            " renames)"
        ),
    )
    artifact_planner: (
        Callable[
            [Path, p.Infra.SemanticSourcePlan],
            p.Result[tuple[p.Infra.CodegenFilePlan, ...]],
        ]
        | None
    ) = m.Field(
        default=None,
        exclude=True,
        description="Injected source-artifact planning after final phase composition",
    )
    consumer_roots: tuple[Path, ...] = m.Field(
        default=(),
        description="Explicit read scopes; not additional syntax targets",
    )
    rename_plan: Path | None = m.Field(
        default=None,
        description="Optional native candidate composed before publication",
    )
    rule_id: str | None = m.Field(
        default=None,
        description="Exact catalog rules selected for this isolated transaction",
    )
    rule_ids: tuple[str, ...] | None = m.Field(
        default=None,
        description="Exact ast-grep catalog rules selected for this transaction",
    )
    laws: tuple[str, ...] | None = m.Field(
        default=None,
        description=(
            "Theme laws re-expanded against the current plan whenever a source "
            "the expansion read changes"
        ),
    )
    _quarantine: dict[Path, p.Infra.ModModuleQuarantine] = m.PrivateAttr(
        default_factory=dict
    )
    _excluded: dict[str, p.Infra.ModQuarantineExclusion] = m.PrivateAttr(
        default_factory=dict
    )
    _plan: p.Infra.CodemodRulePlan | None = m.PrivateAttr(default=None)
    _plan_selection: t.StrTuple | None = m.PrivateAttr(default=None)
    _plan_states: tuple[p.Cli.AtomicFileState, ...] = m.PrivateAttr(default=())
    _snapshot: p.Infra.WorkspaceSnapshot | None = m.PrivateAttr(default=None)

    @property
    def focused(self) -> bool:
        """Whether the transaction selects rules instead of the complete catalog.

        Returns:
            Whether a law, plural or single rule selection is declared.

        """
        return (self.laws, self.rule_ids, self.rule_id) != (None, None, None)

    @property
    def selected_rule_ids(self) -> t.StrTuple | None:
        """Exact AST selection of a focused transaction.

        Returns:
            The law expansion over the current plan, the plural catalog
            selection, the single selector, or ``None`` for the complete catalog.

        """
        if self.laws is None:
            if self.rule_ids is not None:
                return self.rule_ids
            return (self.rule_id,) if self.rule_id is not None else None
        _ = self.selected_plan
        return self._plan_selection

    @property
    def selected_plan(self) -> p.Infra.CodemodRulePlan:
        """Rule plan of the selection, reused while its sources are unchanged.

        Generated rule ids and scopes derive from the current import layout,
        so a publication or another actor's write plans the selection again.

        Returns:
            The plan every scan of this transaction runs.

        """
        plan = self._plan
        if plan is not None and not self._drifted(self._plan_states):
            return plan
        with u.Infra.codemod_workspace_snapshot(self.repository_root) as snapshot:
            return self._plan_snapshot(snapshot, self._selection(snapshot)).unwrap()

    def _selection(self, snapshot: p.Infra.WorkspaceSnapshot) -> t.StrTuple | None:
        """Expand the laws over ``snapshot``, or return the declared selection.

        Returns:
            The exact rule ids, or ``None`` for the complete catalog.

        """
        if self.laws is None:
            return self.selected_rule_ids
        return u.Infra.codemod_law_rule_ids(snapshot, frozenset(self.laws)).unwrap()

    def _plan_snapshot(
        self, snapshot: p.Infra.WorkspaceSnapshot, selection: t.StrTuple | None
    ) -> p.Result[p.Infra.CodemodRulePlan]:
        """Plan ``selection`` over ``snapshot`` and record the states it read.

        Returns:
            The selection's rule plan, or the planning failure.

        """
        self._snapshot = snapshot
        planned = u.Infra.codemod_rule_plan(snapshot, rule_ids=selection)
        if planned.success:
            self._plan = planned.value
            self._plan_selection = selection
            self._plan_states = tuple(
                source.state for source in snapshot.sources.values()
            )
        return planned

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Inspect or apply the selected rule cascade with visible phases.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        if any(
            not root.is_absolute() or not root.is_dir() for root in self.consumer_roots
        ):
            return r[t.Cli.ResultValue].fail(
                "consumer roots must be existing absolute checkout roots"
            )
        with u.Infra.codemod_workspace_snapshot(self.repository_root) as snapshot:
            selection = self._selection(snapshot)
            if self.laws is not None:
                laws = ", ".join(sorted(self.laws))
                if not selection:
                    self.progress.emit(
                        f"mod: no planned rule in {self.repository_root} claims {laws}"
                    )
                    return r[t.Cli.ResultValue].ok(value=True)
                self.progress.emit(
                    f"mod: laws expand to {len(selection)} rule(s) in "
                    f"{self.repository_root}"
                )
            preflight = self._preflight(snapshot, selection)
        if preflight.failure:
            return r[t.Cli.ResultValue].from_failure(preflight)
        rules, pending = preflight.value
        if self.effective_dry_run:
            return self._execute_dry_run(rules, pending)
        return self._execute_apply(pending)

    def _preflight(
        self,
        snapshot: p.Infra.WorkspaceSnapshot,
        selection: t.StrTuple | None,
    ) -> p.Result[tuple[tuple[Path, ...], p.Infra.ModScanReport]]:
        """Plan and scan the current snapshot once; concurrent writers never block it.

        Sessions share the checkout and write concurrently. The preflight is
        read-only, so a source another actor changes meanwhile is reported and
        left to the apply loop, which authenticates every input before each
        effect and voids an iteration on drift (optimistic publication). The
        preflight never discards and re-captures the whole snapshot, which a
        busy shared checkout would starve. The law expansion and the plan
        share ``snapshot``, so the theme's sources are read once, and every
        later scan reuses the plan until one of them changes.

        Returns:
            The discovered rule files and the scan of the captured snapshot.

        """
        outcome = r[tuple[tuple[Path, ...], p.Infra.ModScanReport]]
        planned = self._plan_snapshot(snapshot, selection)
        if planned.failure:
            return outcome.from_failure(planned)
        rules = u.Infra.codemod_fixture_resources(planned.value)
        self.progress.emit("mod: validate ast-grep rule fixtures")
        FlextInfraModGateEngine.validate_rule_fixtures(
            self.repository_root,
            rules,
            rule_ids=tuple(rule.id for rule in planned.value.rules),
        ).unwrap()
        states = tuple(source.state for source in snapshot.sources.values())
        pending = FlextInfraModGateEngine.scan(
            self.repository_root,
            fix=False,
            selection=planned.value,
        ).unwrap()
        self._emit_drift("preflight", self._drifted(states))
        return outcome.ok((rules, pending))

    def _execute_dry_run(
        self,
        rules: Sequence[Path],
        pending: p.Infra.ModScanReport,
    ) -> p.Result[t.Cli.ResultValue]:
        """Report every pending finding without applying any phase.

        Returns:
            The inspection verdict over the discovered rule cascade.

        """
        seed_renames = r[int].ok(value=0)
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
        elif not self.focused:
            seed_renames = self._preview_module_names()
            if seed_renames.failure:
                return r[t.Cli.ResultValue].from_failure(seed_renames)
        text_pending, cycles = self._catalog_verdicts(validate_receipts=True)
        pending_count = pending.findings + seed_renames.value + len(cycles)
        pending_count += text_pending.findings
        renames_pending = r[int].ok(value=0)
        error_data: t.JsonDict | None = None
        if not self.focused:
            error_data = {"text": text_pending.model_dump(mode="json")}
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
                f"({text_pending.actionable} actionable), "
                f"{seed_renames.value} pending module rename(s), "
                f"{len(cycles)} module(s) in runtime import cycles and "
                f"{renames_pending.value} pending CSV-rename occurrence(s), "
                f"across {len(rules)} rule file(s)",
                error_data=error_data,
            )
        self.progress.emit("mod: no pending ast-grep or sed-by-list fixes")
        return r[t.Cli.ResultValue].ok(value=True)

    def _execute_apply(
        self, current: p.Infra.ModScanReport
    ) -> p.Result[t.Cli.ResultValue]:
        """Converge AST, semantic, and text phases over the same source state.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        self._quarantine.clear()
        self._excluded.clear()
        result = self._converge(
            self.repository_root,
            current,
            text_precondition_pending=True,
        )
        if result.failure or self.focused:
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
        current: p.Infra.ModScanReport,
        seed: p.Infra.StageSourcePlan,
        inputs: MutableMapping[Path, p.Cli.AtomicFileState],
    ) -> p.Result[p.Infra.StageSourcePlan]:
        """Compose syntax fixes without publishing the original producer epoch.

        Every fixable rule without engine context applies first through the
        native ast-grep cascade (header, catalog, Ruff import fix) to its
        fixed point; the engine then composes only the admitted fixes of the
        rules that carry project context.

        Returns:
            The complete all-root candidate with target-only syntax effects,
            or the first staging, scan or replacement failure.

        The wave loop refuses native residue and repeated states loudly
        (``_require_wave_progress``).

        Raises:
            ValueError: If native syntax planning requires its original scan rule plan.

        """
        rule_plan = current.rule_plan
        if rule_plan is None:
            msg = "native syntax planning requires its original scan rule plan"
            raise ValueError(msg)
        plans = self._native_plans(root, rule_plan, inputs, seed)
        start = (
            self._preview_ast_candidate(root, plans, inputs, seed)
            if seed.updates or plans
            else r[p.Infra.ModScanReport].ok(current)
        )
        if start.failure:
            return r[p.Infra.StageSourcePlan].from_failure(start)
        native_ids = frozenset(
            rule.id for rule in rule_plan.rules if u.Infra.codemod_native_eligible(rule)
        )
        after_ast = FlextInfraModGateEngine.authored(start.value)
        if self.focused:
            # A focused transaction must not compose unrelated catalog
            # findings: the wave loop would never settle on rules the
            # selection could not apply.
            selected = frozenset(self.selected_rule_ids or ())
            after_ast = after_ast.model_copy(
                update={
                    "entries": tuple(
                        entry
                        for entry in after_ast.entries
                        if entry.rule_id in selected
                    )
                }
            )
        converged = self._syntax_waves(
            root,
            after_ast,
            native_ids,
            (plans, inputs, seed),
        )
        if converged.failure:
            return r[p.Infra.StageSourcePlan].from_failure(converged)
        return self._admitted_syntax(root, plans, inputs, seed)

    def _native_plans(
        self,
        root: Path,
        rule_plan: p.Infra.CodemodRulePlan,
        inputs: Mapping[Path, p.Cli.AtomicFileState],
        seed: p.Infra.StageSourcePlan,
    ) -> dict[Path, p.Infra.SemanticFilePlan]:
        """Bind every native-cascade rewrite to its captured input state.

        Returns:
            One syntax plan per source the native cascade changed.

        """
        return {
            path: m.Infra.SemanticFilePlan.model_validate({
                "project": (u.Infra.project_root(path) or root),
                "path": (path),
                "before": (inputs[path]),
                "desired_content": (content),
                "desired_mode": (inputs[path].mode),
                "changes": ((c.Infra.MOD_NATIVE_CASCADE_CHANGE,)),
            })
            for path, content in self._native_cascade(rule_plan, inputs, seed).items()
        }

    def _syntax_waves(
        self,
        root: Path,
        after_ast: p.Infra.ModOccurrenceReport[p.Infra.ModScanFinding],
        native_ids: frozenset[str],
        state: tuple[
            dict[Path, p.Infra.SemanticFilePlan],
            MutableMapping[Path, p.Cli.AtomicFileState],
            p.Infra.StageSourcePlan,
        ],
    ) -> p.Result[bool]:
        """Compose engine replacement waves until no actionable finding remains.

        Returns:
            ``True`` at the syntax fixed point, or the first wave failure.

        """
        plans, inputs, seed = state
        seen: set[tuple[tuple[str, str], ...]] = set()
        while after_ast.actionable:
            self._require_wave_progress(after_ast, native_ids, plans, seen)
            wave = FlextInfraModReplacements.compose(root, after_ast)
            if wave.failure:
                return r[bool].from_failure(wave)
            self._merge_wave(plans, inputs, wave.value)
            previewed = self._preview_ast_candidate(root, plans, inputs, seed)
            if previewed.failure:
                return r[bool].from_failure(previewed)
            before_ast = after_ast
            after_ast = FlextInfraModGateEngine.authored(previewed.value)
            FlextInfraCodemodBatchApply.validate_fix_match(before_ast, after_ast)
        return r[bool].ok(value=True)

    @staticmethod
    def _require_wave_progress(
        after_ast: p.Infra.ModOccurrenceReport[p.Infra.ModScanFinding],
        native_ids: frozenset[str],
        plans: Mapping[Path, p.Infra.SemanticFilePlan],
        seen: set[tuple[tuple[str, str], ...]],
    ) -> None:
        """Refuse native residue and a repeated syntax candidate state.

        Raises:
            RuntimeError: If a native-eligible rule still reports an actionable
                finding, or the syntax cascade repeats a source state.

        """
        residue = sorted({
            entry.rule_id
            for entry in after_ast.entries
            if entry.actionable and entry.rule_id in native_ids
        })
        if residue:
            msg = (
                "native cascade left actionable findings of native rules: "
                f"{', '.join(residue)}"
            )
            raise RuntimeError(msg)
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

    @staticmethod
    def _merge_wave(
        plans: dict[Path, p.Infra.SemanticFilePlan],
        inputs: MutableMapping[Path, p.Cli.AtomicFileState],
        wave: Sequence[p.Infra.SemanticFilePlan],
    ) -> None:
        """Fold one wave into the plans, keeping each file's first witness."""
        for plan in wave:
            original = plans.get(plan.path)
            if original is None:
                inputs.setdefault(
                    plan.path, m.Cli.AtomicFileState.model_validate(plan.before)
                )
                plans[plan.path] = plan.model_copy(update={"before": inputs[plan.path]})
                continue
            plans[plan.path] = plan.model_copy(
                update={
                    "before": original.before,
                    "changes": (*original.changes, *plan.changes),
                }
            )

    @staticmethod
    def _admitted_syntax(
        root: Path,
        plans: Mapping[Path, p.Infra.SemanticFilePlan],
        inputs: Mapping[Path, p.Cli.AtomicFileState],
        seed: p.Infra.StageSourcePlan,
    ) -> p.Result[p.Infra.StageSourcePlan]:
        """Stage the admitted syntax fixes over the seed candidate.

        Returns:
            The seed when no syntax plan exists, else the staged candidate, or
            the admission or staging failure.

        """
        if not plans:
            return r[p.Infra.StageSourcePlan].ok(seed)
        accepted = FlextInfraModReplacements.admit(
            root, tuple(plans.values()), seed.updates
        )
        if accepted.failure:
            return r[p.Infra.StageSourcePlan].from_failure(accepted)
        return FlextInfraStagedPackage.plan_sources(
            seed.workspace,
            {
                **seed.updates,
                **{
                    plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                    for plan in accepted.value
                    if plan.desired_content is not None
                },
            },
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": (seed.workspaces),
                "modes": (seed.modes),
                "inputs": (tuple(inputs.values())),
            }),
        )

    @staticmethod
    def _native_cascade(
        rule_plan: p.Infra.CodemodRulePlan,
        inputs: Mapping[Path, p.Cli.AtomicFileState],
        seed: p.Infra.StageSourcePlan,
    ) -> Mapping[Path, bytes]:
        """Run each governed project's native cascade over the seeded sources.

        Each source belongs to its deepest governed project; the plan carries
        that project's generated provider beside its catalogs.

        Returns:
            Absolute path to new bytes for every source a cascade changed.

        """
        current: dict[Path, bytes] = {
            path: state.content
            for path, state in inputs.items()
            if state.content is not None and path.suffix == c.Infra.EXT_PYTHON
        }
        for path, source in seed.updates.items():
            if source is None:
                current.pop(path, None)
            elif path.suffix == c.Infra.EXT_PYTHON:
                current[path] = source.encode(c.DEFAULT_ENCODING)
        projects = sorted(
            rule_plan.project_rule_ids,
            key=lambda project: len(project.parts),
            reverse=True,
        )
        owned: dict[Path, dict[Path, bytes]] = {project: {} for project in projects}
        for path, content in current.items():
            owner = next(
                (project for project in projects if path.is_relative_to(project)),
                None,
            )
            if owner is not None:
                owned[owner][path] = content
        changed: dict[Path, bytes] = {}
        for project, sources in owned.items():
            if not sources:
                continue
            changed.update(u.Infra.native_cascade(project, rule_plan, sources))
        return changed

    @staticmethod
    def _capture_ast_inputs(
        root: Path, inputs: MutableMapping[Path, p.Cli.AtomicFileState]
    ) -> tuple[Path, ...]:
        """Authenticate every syntax target before composing the first wave.

        A source another actor changed or removed after the seed capture is
        external drift of this iteration, never a defect of the run.

        Returns:
            Every seeded input whose current disk state differs from its capture.

        """
        drifted: list[Path] = []
        for target in u.Infra.ast_grep_scan_targets(root):
            path = root / target
            paths = (
                u.Infra.iter_directory_python_files(path, repository_root=root)
                if path.is_dir()
                else (path,)
            )
            for source in paths:
                resolved = source.resolve()
                captured = u.Cli.atomic_read_binary_file_state(source).unwrap()
                if captured.content is None and resolved not in inputs:
                    continue
                if inputs.setdefault(resolved, captured) != captured:
                    drifted.append(resolved)
        return tuple(drifted)

    @staticmethod
    def _drifted(states: Sequence[p.Cli.AtomicFileState]) -> tuple[Path, ...]:
        """Observe which captured states another actor changed on disk.

        Returns:
            Every captured path whose current physical state differs.

        """
        return tuple(
            Path(state.path)
            for state in {state.path: state for state in states}.values()
            if u.Cli.atomic_read_binary_file_state(state.path).unwrap() != state
        )

    def _emit_drift(self, scope: str, drifted: Sequence[Path]) -> None:
        """Name every externally changed path whose candidate was discarded."""
        for path in drifted:
            self.progress.emit(
                f"mod: {scope} observed external change: {path}; "
                "the apply loop re-authenticates it before any effect"
            )

    def _preview_ast_candidate(
        self,
        root: Path,
        plans: Mapping[Path, p.Infra.SemanticFilePlan],
        inputs: MutableMapping[Path, p.Cli.AtomicFileState],
        seed: p.Infra.StageSourcePlan,
    ) -> p.Result[p.Infra.ModScanReport]:
        """Bind each wave's authenticated plan to its transactional scan.

        Returns:
            The full-catalog report for this candidate's staged bytes, or the
            staging or scan failure (an input changed on disk included).

        """
        staged = FlextInfraStagedPackage.plan_sources(
            seed.workspace,
            {
                **seed.updates,
                **{
                    path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                    for path, plan in plans.items()
                    if plan.desired_content is not None
                },
            },
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": (seed.workspaces),
                "modes": (seed.modes),
                "inputs": (tuple(inputs.values())),
            }),
        )
        if staged.failure:
            return r[p.Infra.ModScanReport].from_failure(staged)
        candidate = staged.value
        for source in candidate.inputs:
            inputs.setdefault(source.path, source)

        def scan(
            view_root: Path, _paths: Mapping[Path, Path]
        ) -> p.Result[p.Infra.ModScanReport]:
            del _paths
            return FlextInfraModGateEngine.scan_candidate(
                root,
                view_root,
                candidate,
                selection=self.selected_plan,
            )

        return self.source_preview.preview_sources(
            candidate.workspace,
            candidate.updates,
            scan,
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": (candidate.workspaces),
                "modes": (candidate.modes),
                "inputs": (candidate.inputs),
            }),
        ).flat_map(lambda report: report)

    def _plan_text_phase(
        self,
        root: Path,
        candidate: p.Infra.SemanticSourcePlan,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
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
        for path in self._quarantine:
            sources.pop(path, None)
        planned = FlextInfraModTextGateEngine.plan(
            root,
            sources=sources,
            validate_receipts=text_precondition_pending,
        )
        if planned.failure:
            return r[p.Infra.SemanticSourcePlan].from_failure(planned)
        return FlextInfraCodemodSemanticApply.compose_candidate(
            candidate, planned.value[1]
        )

    def _apply_renames(
        self,
    ) -> p.Result[tuple[p.Cli.AtomicFileState, ...]]:
        """Apply every declared CSV rename campaign in declared order.

        Returns:
            The latest authenticated state of every published campaign path.

        """
        published: dict[Path, p.Cli.AtomicFileState] = {}
        for rename_params in self.rename_inputs:
            renamed = self.rename_runner.run(rename_params)
            if renamed.failure:
                return r[tuple[p.Cli.AtomicFileState, ...]].from_failure(renamed)
            published.update({
                state.path: state for state in renamed.value.published_states
            })
            self.progress.emit_rename(renamed.value)
        return r[tuple[p.Cli.AtomicFileState, ...]].ok(tuple(published.values()))

    def _advance_phases(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        current: p.Infra.ModScanReport,
        *,
        text_precondition_pending: bool,
        publish: bool = True,
    ) -> p.Result[p.Infra.ModPhaseAdvance]:
        """Run the AST, semantic, callback, text, and rename phases once.

        The iteration captures its inputs from the current disk state and
        rebuilds its planning graph from them. A captured input another actor
        changes before publication voids only this iteration's candidate;
        nothing of it is published. A planning failure attributed to one source
        module voids the candidate and names the module for quarantine.

        Returns:
            The post-phase scan report plus the fingerprint states the
            fixed-point check must observe, or the discarded iteration's drift
            or quarantine, or the first unattributed failure.

        """
        fingerprint = FlextInfraCodemodSemanticApply.source_fingerprint
        voided = m.Infra.ModPhaseAdvance(
            report=current, phase_states=(fingerprint(root, current),)
        )
        seeded = self._phase_seed(root, rope_workspace)
        if seeded.failure:
            return self._attributed(seeded, voided)
        inputs: MutableMapping[Path, p.Cli.AtomicFileState] = {
            state.path: state for state in seeded.value.candidate.inputs
        }
        # The candidate is linearized at the seed capture; a source another
        # session changed since is guarded by the destination compare-and-swap
        # at publication, never by voiding the whole iteration here.
        self._capture_ast_inputs(root, inputs)
        planned = self._plan_iteration(
            root,
            current,
            (seeded.value, inputs),
            text_precondition_pending=text_precondition_pending,
        )
        if planned.failure:
            return self._attributed(planned, voided, tuple(inputs.values()))
        return self._publish_iteration(
            root,
            rope_workspace,
            (planned.value, (*inputs.values(), *planned.value.candidate.inputs)),
            voided,
            publish=publish,
        )

    def _plan_iteration(
        self,
        root: Path,
        current: p.Infra.ModScanReport,
        captured: tuple[
            p.Infra.SemanticSourcePlan,
            MutableMapping[Path, p.Cli.AtomicFileState],
        ],
        *,
        text_precondition_pending: bool,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Compose every phase's effects inside one fresh planning graph.

        Returns:
            The publication candidate without quarantined effects, or the
            first planning failure.

        """
        seed, inputs = captured
        filtered_seed = self._without_quarantined(seed)
        if filtered_seed.failure:
            return filtered_seed
        seed = filtered_seed.value
        current = self._without_quarantined_report(root, current)
        with FlextInfraCodemodSemanticApply.planning_workspace(
            root, seed, self._candidate_sources(seed.candidate)
        ) as graph:
            prepared = self._prepare_phase_seed(
                root,
                current,
                (seed, inputs),
                graph,
                text_precondition_pending=text_precondition_pending,
            )
            if prepared.failure:
                return prepared
            semantic = self._plan_semantic_phase(root, prepared.value, graph)
            if semantic.failure:
                return semantic
            publication = self._plan_publication_candidate(root, semantic.value, graph)
        return publication.flat_map(self._without_quarantined)

    def _publish_iteration(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        planned: tuple[p.Infra.SemanticSourcePlan, Sequence[p.Cli.AtomicFileState]],
        voided: p.Infra.ModPhaseAdvance,
        *,
        publish: bool,
    ) -> p.Result[p.Infra.ModPhaseAdvance]:
        """Publish one candidate, voiding it only when a destination drifted.

        Concurrent sessions write the shared checkout. The candidate is linearized
        at its capture: a change another actor makes to an input the candidate
        does not write never voids it, because the publisher's compare-and-swap
        guards exactly the destinations. Only a drifted destination is new
        input for this iteration.

        Returns:
            The finished iteration, the voided iteration naming its drift or
            quarantine, or the first unattributed publication failure.

        """
        candidate, observed = planned
        destinations = frozenset(
            plan.path.resolve()
            for plan in FlextInfraCodemodSemanticApply.planning_file_plans(
                root, candidate.candidate, {}
            )
        )
        captured = tuple(
            state for state in observed if Path(state.path).resolve() in destinations
        )
        drifted = self._drifted(captured)
        if drifted:
            return r[p.Infra.ModPhaseAdvance].ok(
                voided.model_copy(update={"drifted": drifted})
            )
        accepted = (
            FlextInfraCodemodSemanticApply.publish_candidate(
                root, candidate, publish=publish
            )
            if destinations
            else r[tuple[Path, ...]].ok(())
        )
        if accepted.failure:
            # The publisher's compare-and-swap rejects the whole batch; only an
            # observed external change makes that rejection new input. A
            # failure after its own writes is never drift.
            if (accepted.error_data or {}).get(c.Infra.MOD_WRITTEN_FILES_KEY):
                return r[p.Infra.ModPhaseAdvance].from_failure(accepted)
            return self._attributed(accepted, voided, captured)
        return self._finish_phases(
            root,
            rope_workspace,
            voided.report,
            (publish, accepted.value, list(voided.phase_states)),
        )

    def _attributed(
        self,
        failure: p.FailureLike,
        voided: p.Infra.ModPhaseAdvance,
        captured: Sequence[p.Cli.AtomicFileState] = (),
    ) -> p.Result[p.Infra.ModPhaseAdvance]:
        """Judge a planning failure: external drift, one module, or the engine.

        A failure observed while a captured input changed on disk is new
        input, never a verdict: the iteration is voided and re-captured.

        Returns:
            The voided iteration naming the drift or the module, or the
            original failure when neither drift nor one module owns it, or when
            the exclusion of that module did not hold.

        """
        outcome = r[p.Infra.ModPhaseAdvance]
        drifted = self._drifted(captured)
        if drifted:
            return outcome.ok(voided.model_copy(update={"drifted": drifted}))
        module = (failure.error_data or {}).get(c.Infra.MOD_FAILURE_MODULE_KEY)
        if not isinstance(module, str) or not Path(module).is_absolute():
            return outcome.from_failure(failure)
        path = Path(module).resolve()
        if path in self._quarantine:
            return outcome.from_failure(failure)
        return outcome.ok(
            voided.model_copy(
                update={
                    "quarantined": m.Infra.ModModuleQuarantine(
                        path=path,
                        cause=failure.error or "",
                        error_code=failure.error_code,
                    )
                }
            )
        )

    def _without_quarantined_report(
        self,
        root: Path,
        report: p.Infra.ModScanReport,
    ) -> p.Infra.ModScanReport:
        """Drop quarantined modules from the next iteration's planning report.

        Quarantine is a planning input, not only a publication filter: keeping a
        failed module in the scanned findings makes every later joint iteration
        replan the same failure and never reaches the fixed point.

        Returns:
            The report without findings whose module is quarantined.

        """
        if not self._quarantine:
            return report

        def excluded(entry: p.Infra.ModScanFinding) -> bool:
            return (root / entry.file).resolve() in self._quarantine

        entries = tuple(entry for entry in report.entries if not excluded(entry))
        if len(entries) == len(report.entries):
            return report
        return report.model_copy(
            update={
                "entries": entries,
                "files": frozenset((root / entry.file).resolve() for entry in entries),
            }
        )

    def _without_quarantined(
        self, plan: p.Infra.SemanticSourcePlan
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Exclude every effect on a quarantined module from the candidate.

        Returns:
            The candidate without quarantined targets, or its staging failure.

        """
        excluded = set(self._quarantine)
        candidate = plan.candidate
        if excluded.isdisjoint(candidate.updates):
            return r[p.Infra.SemanticSourcePlan].ok(plan)
        return FlextInfraStagedPackage.plan_sources(
            candidate.workspace,
            {
                path: source
                for path, source in candidate.updates.items()
                if path not in excluded
            },
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": (candidate.workspaces),
                "modes": (candidate.modes),
                "inputs": (candidate.inputs),
            }),
        ).map(
            lambda staged: m.Infra.SemanticSourcePlan(
                candidate=staged, consumer_roots=plan.consumer_roots
            )
        )

    def _plan_publication_candidate(
        self,
        root: Path,
        seed: p.Infra.SemanticSourcePlan,
        graph: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Compose final effects before releasing the candidate's native session.

        Returns:
            The publication candidate or its first planning failure.

        """
        if self.focused:
            return r[p.Infra.SemanticSourcePlan].ok(seed)
        callbacks = self._plan_phase_callbacks(root, seed, graph)
        if callbacks.failure:
            return callbacks
        text = self._plan_text_phase(
            root, callbacks.value, text_precondition_pending=False
        )
        if text.failure or self.artifact_planner is None:
            return text
        artifacts = self.artifact_planner(root, text.value)
        if artifacts.failure:
            return r[p.Infra.SemanticSourcePlan].from_failure(artifacts)
        return FlextInfraCodemodSemanticApply.compose_candidate(
            text.value, artifacts.value
        )

    @staticmethod
    def _candidate_sources(
        candidate: p.Infra.StageSourcePlan,
    ) -> MutableMapping[Path, str]:
        """Compose observed Python sources and the candidate's declared effects.

        Returns:
            The complete Python source view, including additions and retirements.

        """
        sources = u.Infra.candidate_python_sources(candidate, candidate.inputs)
        for path, source in candidate.updates.items():
            if path.suffix not in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}:
                continue
            if source is None:
                sources.pop(path, None)
            else:
                sources[path] = source
        return sources

    def _coherent(self, phase: str, paths: Collection[Path]) -> bool:
        """Admit one phase's coherent change unless it touches quarantine.

        A change spanning a quarantined module is dropped whole, never split:
        publishing only its other half would break the atomic-effects law.

        Returns:
            Whether the phase's complete contribution may be composed.

        """
        targets = tuple(sorted(set(paths)))
        touched = tuple(path for path in targets if path in self._quarantine)
        if not touched:
            return True
        exclusion = m.Infra.ModQuarantineExclusion(
            phase=phase, modules=touched, paths=targets
        )
        if self._excluded.get(phase) != exclusion:
            self.progress.emit(
                f"mod: phase {phase} change over "
                f"{', '.join(map(str, targets))} dropped whole: it touches "
                f"quarantined {', '.join(map(str, touched))}"
            )
        self._excluded[phase] = exclusion
        return False

    def _planning_sources(
        self, candidate: p.Infra.StageSourcePlan
    ) -> MutableMapping[Path, str]:
        """Compose the planner's source view without quarantined modules.

        Returns:
            The candidate source view every planner receives in this run.

        """
        sources = self._candidate_sources(candidate)
        for path in self._quarantine:
            sources.pop(path, None)
        return sources

    def _phase_seed(
        self, root: Path, rope_workspace: p.Infra.RopeWorkspaceDsl
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Load an explicit rename artifact or capture a source campaign.

        Returns:
            The native seed, or the first loading or planning failure.

        """
        if self.rename_plan is None:
            return self._campaign_seed(root)
        loaded = FlextInfraCodemodSemanticApply.load_rename_artifact(
            root,
            m.Infra.ModCommand(repository_root=root, rename_plan=self.rename_plan),
        )
        if loaded.failure:
            return r[p.Infra.SemanticSourcePlan].from_failure(loaded)
        seed, driver = loaded.value
        current = FlextInfraCodemodSemanticApply.plan_rename_artifact(
            root, seed, driver, rope_workspace
        )
        if current.failure:
            return r[p.Infra.SemanticSourcePlan].from_failure(current)
        return self._admitted_rename_seed(current.value)

    def _campaign_seed(self, root: Path) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Capture the source campaign and its module-naming rename candidate.

        A rename spanning a quarantined module is dropped whole, leaving the
        captured campaign without it. A focused rule selection runs one rule at
        a time: module naming is a distinct campaign and stays unplanned.

        Returns:
            The named or plain campaign, or the first capture failure.

        """
        built = FlextInfraCodemodSemanticApply.build_source_plan(
            root, self.consumer_roots, snapshot=self._snapshot
        )
        if built.failure or self.focused:
            return built
        named = FlextInfraCodemodSemanticApply.plan_module_names(root, built.value)
        if named.success and not self._coherent(
            "module-naming", named.value.candidate.updates
        ):
            return built
        return named

    def _preview_module_names(self) -> p.Result[int]:
        """Plan the module-naming campaign without publishing or staging it.

        Apply plans the same seed, so a naming failure surfaces here exactly as
        it would there; every planned rename is reported before it is counted.

        Returns:
            The number of pending module renames, or the first planning failure.

        """
        seeded = self._campaign_seed(self.repository_root)
        if seeded.failure:
            return r[int].from_failure(seeded)
        moves = (
            seeded.value.moves
            if isinstance(seeded.value, p.Infra.SemanticRenamePlan)
            else ()
        )
        for source, destination in moves:
            self.progress.emit(f"mod: rename module {source} -> {destination}")
        return r[int].ok(len(moves))

    def _admitted_rename_seed(
        self, seed: p.Infra.SemanticSourcePlan
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Admit an authenticated rename artifact for this run's scope.

        Returns:
            The artifact seed, or the scope or quarantine refusal.

        """
        if self.consumer_roots and set(self.consumer_roots) != set(seed.consumer_roots):
            return r[p.Infra.SemanticSourcePlan].fail(
                "run consumer roots differ from the native rename artifact"
            )
        if not self._coherent("rename-artifact", seed.candidate.updates):
            return r[p.Infra.SemanticSourcePlan].fail(
                "native rename artifact spans a quarantined module: "
                + ", ".join(map(str, self._excluded["rename-artifact"].modules))
            )
        return r[p.Infra.SemanticSourcePlan].ok(seed)

    def _prepare_phase_seed(
        self,
        root: Path,
        current: p.Infra.ModScanReport,
        captured: tuple[
            p.Infra.SemanticSourcePlan,
            MutableMapping[Path, p.Cli.AtomicFileState],
        ],
        graph: p.Infra.RopeWorkspaceDsl,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Compose syntax, initial text effects and import normalization.

        Returns:
            The prepared seed, or the first planning failure.

        """
        captured_seed, inputs = captured
        syntax = self._plan_ast_phase(root, current, captured_seed.candidate, inputs)
        if syntax.failure:
            return r[p.Infra.SemanticSourcePlan].from_failure(syntax)
        seed = m.Infra.SemanticSourcePlan(
            candidate=syntax.value,
            consumer_roots=captured_seed.consumer_roots,
        )
        changed_paths = tuple(
            plan.path
            for plan in FlextInfraCodemodSemanticApply.planning_file_plans(
                root, seed.candidate, {}
            )
            if plan.desired_content is not None
        )
        if self.focused and not changed_paths:
            return r[p.Infra.SemanticSourcePlan].ok(seed)
        text_preparation = (
            r[p.Infra.SemanticSourcePlan].ok(seed)
            if self.focused
            else self._plan_text_phase(
                root,
                seed,
                text_precondition_pending=text_precondition_pending,
            )
        )
        if text_preparation.failure:
            return text_preparation
        return self._plan_phase_callbacks(
            root,
            text_preparation.value,
            graph,
            callbacks=(
                FlextInfraCodemodLoopPhaseImportNormalization(
                    paths=changed_paths if self.focused else None,
                ),
            ),
        )

    def _plan_semantic_phase(
        self,
        root: Path,
        seed: p.Infra.SemanticSourcePlan,
        graph: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Compose all native semantic effects on the prepared candidate.

        A selected theme composes only the semantic phases that repair one of
        its rule families (the constants family selects the constant-consumer
        phase); the census constants sweep stays with the complete catalog.
        A theme claiming no phase returns its seed.

        Returns:
            The staged semantic candidate, or the seed for a phase-less theme.

        """
        selection = self.selected_rule_ids
        phases: frozenset[c.Infra.SemanticCutoverPhase] | None = None
        if selection is not None:
            families = {
                rule_id.partition(c.Infra.CODEMOD_GENERATED_ID_SEPARATOR)[0]
                for rule_id in selection
            }
            phases = frozenset(
                c.Infra.SemanticCutoverPhase(phase)
                for phase, rule_ids in c.Infra.SEMANTIC_CUTOVER_RULE_IDS.items()
                if families.intersection(rule_ids)
            )
            if not phases:
                return r[p.Infra.SemanticSourcePlan].ok(seed)
        outcome = r[p.Infra.SemanticSourcePlan]
        syntax = seed.candidate
        semantic_preflight = self._preview_ast_candidate(
            root,
            {},
            {state.path: state for state in syntax.inputs},
            syntax,
        )
        if semantic_preflight.failure:
            return outcome.from_failure(semantic_preflight)
        original = u.Infra.candidate_python_sources(syntax, seed.candidate.inputs)
        working = self._planning_sources(syntax)
        # Why: the candidate carries every staged Python file, but the
        # semantic cutover edits only the governed source inventory. Scenario
        # data and ignored artifacts are not edit targets, and their presence
        # makes a closed Rope observation reject the plan.
        governed = {
            (root / target).resolve() for target in u.Infra.ast_grep_scan_targets(root)
        }
        working = {
            path: source
            for path, source in working.items()
            if path.resolve() in governed
        }
        graph.bind_candidate(
            declared_files=FlextInfraCodemodSemanticApply.planning_file_plans(
                root, syntax, working
            )
        )
        changed: set[Path] = set()
        if phases is None:
            constants = FlextInfraCodemodSemanticApply.plan_census_constants(
                root,
                graph,
                sources=working,
            )
            if constants.failure:
                return outcome.from_failure(constants)
            if self._coherent(
                "census-constants", [edit.file_path for edit in constants.value]
            ):
                FlextInfraCodemodSemanticApply.apply_plan(
                    working, constants.value, changed
                )
            graph.bind_candidate(
                declared_files=FlextInfraCodemodSemanticApply.planning_file_plans(
                    root, syntax, working
                )
            )
        semantic = FlextInfraCodemodSemanticApply.plan_semantic_edits(
            root,
            FlextInfraModGateEngine.authored(semantic_preflight.value),
            graph,
            working,
            phases=phases,
        )
        if semantic.failure:
            return outcome.from_failure(semantic)
        if self._coherent("semantic", [edit.file_path for edit in semantic.value]):
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
            options=m.Infra.StageSourceOptions.model_validate({
                "workspaces": (seed.candidate.workspaces),
                "modes": (seed.candidate.modes),
                "inputs": (seed.candidate.inputs),
            }),
        ).map(
            lambda staged: m.Infra.SemanticSourcePlan(
                candidate=staged, consumer_roots=seed.consumer_roots
            )
        )

    def _finish_phases(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        current: p.Infra.ModScanReport,
        publication: tuple[bool, tuple[Path, ...], list[tuple[tuple[str, str], ...]]],
    ) -> p.Result[p.Infra.ModPhaseAdvance]:
        """Refresh and scan a published candidate before applying CSV campaigns.

        Returns:
            The post-publication report and its observed fingerprint sequence.

        """
        outcome = r[p.Infra.ModPhaseAdvance]
        publish, published_paths, phase_states = publication
        if not publish:
            return outcome.ok(
                m.Infra.ModPhaseAdvance(
                    report=current, phase_states=tuple(phase_states)
                )
            )
        self.rename_plan = None
        self.progress.emit(f"mod: published {len(published_paths)} source file(s)")
        rope_workspace.refresh()
        after_ast = FlextInfraModGateEngine.scan(
            root, fix=False, selection=self.selected_plan
        ).unwrap()
        phase_states.append(
            FlextInfraCodemodSemanticApply.source_fingerprint(root, after_ast)
        )
        # Exact optional migration receipts apply once per invocation,
        # not to every internal convergence pass after consuming matches.
        renames = self._apply_renames()
        if renames.failure:
            return outcome.from_failure(renames)
        u.Cli.atomic_verify_binary_file_states(renames.value).unwrap()
        if renames.value:
            rope_workspace.refresh()
            after_ast = FlextInfraModGateEngine.scan(
                root, fix=False, selection=self.selected_plan
            ).unwrap()
        return outcome.ok(
            m.Infra.ModPhaseAdvance(report=after_ast, phase_states=tuple(phase_states))
        )

    def _emit_residuals(
        self,
        current: p.Infra.ModScanReport,
        current_text: p.Infra.ModTextReport,
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

    def _catalog_verdicts(
        self, *, validate_receipts: bool
    ) -> tuple[p.Infra.ModTextReport, tuple[p.Infra.Issue, ...]]:
        """Observe the whole-catalog text and import-cycle verdicts.

        A selected theme (ADR-028 Decision 18 item 2) checks and fixes only
        its own rules, so the whole-catalog text verdict does not belong to
        it. The import law always runs, inside a selected run too: a theme
        that binds a family's own letter at runtime closes an import cycle
        (ENFORCE-006/ENFORCE-051), and that cycle blocks its fixed point.

        Returns:
            The text report (empty for a selected theme) and the runtime
            import cycles.

        """
        cycles = u.Infra.codemod_import_cycle_issues(self.repository_root)
        if self.focused:
            empty = m.Infra.ModTextReport(
                findings=0, actionable=0, files=frozenset(), entries=()
            )
            return empty, cycles
        return (
            FlextInfraModTextGateEngine.scan(
                self.repository_root, fix=False, validate_receipts=validate_receipts
            ).unwrap(),
            cycles,
        )

    def _verdict_message(
        self,
        states: tuple[
            tuple[tuple[str, str], ...],
            Sequence[tuple[tuple[str, str], ...]],
        ],
        current: p.Infra.ModScanReport,
    ) -> str | None:
        """Judge the converged fixed point and report residual owner repairs.

        Returns:
            The fixed-point failure message, or ``None`` when the joint AST,
            semantic, and text fixed point is verified with zero remaining
            findings and no runtime import cycle.

        """
        before, phase_states = states
        if any(state != before for state in phase_states):
            return "mod cross-phase cycle returned to its starting source state"
        current_text, cycles = self._catalog_verdicts(validate_receipts=False)
        if current.actionable or current_text.actionable:
            return (
                "mod made no progress with "
                f"{current.actionable} AST and {current_text.actionable} text "
                "actionable findings"
            )
        self._emit_residuals(current, current_text)
        # ENFORCE-006: the runtime import graph, not a syntax rule, decides a
        # cycle; any cycle at the fixed point blocks, like check's verdict.
        for issue in cycles:
            self.progress.emit(f"mod: {issue.file}: {issue.message}")
        if cycles:
            return f"mod: {len(cycles)} module(s) remain in runtime import cycles"
        if current.findings or current_text.findings:
            return (
                f"mod: fixed point retains {current.findings} AST finding(s) "
                f"({current.detection_only} detection-only, "
                f"{current.non_actionable_with_fix} non-actionable with fix) and "
                f"{current_text.findings} text finding(s); owner repair required"
            )
        return None

    def _converge(
        self,
        root: Path,
        current: p.Infra.ModScanReport,
        *,
        text_precondition_pending: bool,
    ) -> p.Result[t.Cli.ResultValue]:
        """Converge every mod phase through one shared Rope workspace.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        rope_workspace = self.rope
        fingerprint = FlextInfraCodemodSemanticApply.source_fingerprint
        seen: MutableMapping[tuple[tuple[str, str], ...], int] = {}
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
            advance = advanced.value
            if advance.drifted or advance.quarantined is not None:
                # A voided iteration had no effect: its start state is not a
                # visited state of the fixed-point search.
                del seen[before]
                if advance.quarantined is not None:
                    self._quarantine[advance.quarantined.path] = advance.quarantined
                    self.progress.emit(
                        f"mod: quarantine {advance.quarantined.path} for the rest "
                        f"of this run: {advance.quarantined.cause}"
                    )
                else:
                    self._emit_drift(f"joint iteration {iteration}", advance.drifted)
                    rope_workspace.refresh()
                    current = FlextInfraModGateEngine.scan(
                        root,
                        fix=False,
                        selection=self.selected_plan,
                    ).unwrap()
                continue
            current, phase_states = advance.report, advance.phase_states
            text_precondition_pending = False
            after = fingerprint(root, current)
            if after != before:
                continue
            message = self._verdict_message(
                (before, phase_states), current
            ) or self._relocation_verdict(root, rope_workspace, current)
            quarantined = self._quarantine_verdict()
            if quarantined is not None:
                message = (
                    quarantined if message is None else f"{quarantined}; {message}"
                )
            if message is not None:
                return r[t.Cli.ResultValue].fail(message)
            self.progress.emit(
                "mod: joint AST, semantic, and text fixed point verified "
                "with zero AST/text findings",
            )
            return r[t.Cli.ResultValue].ok(value=True)

    def _quarantine_verdict(self) -> str | None:
        """Name every module whose own failure excluded it from this run.

        Returns:
            The failure message naming each quarantined module and its cause,
            or ``None`` when every module was planned.

        """
        if not self._quarantine:
            return None
        causes = "; ".join(
            f"{quarantine.path}: {quarantine.cause}"
            for quarantine in self._quarantine.values()
        )
        dropped = "".join(
            f"; phase {exclusion.phase} change over "
            f"{', '.join(map(str, exclusion.paths))} dropped whole because of "
            f"{', '.join(map(str, exclusion.modules))}"
            for exclusion in self._excluded.values()
        )
        return (
            f"mod: {len(self._quarantine)} quarantined module(s) failed their "
            f"own planning and were excluded: {causes}{dropped}"
        )

    def _relocation_verdict(
        self,
        root: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        current: p.Infra.ModScanReport,
    ) -> str | None:
        """Report each unresolved declaration relocation as its own finding.

        An unresolved owner is a finding of that declaration, never a plan
        crash; accepted writes remain available for the next fix-forward pass.
        The relocation census owns no selected theme, so a selected run skips it.

        Returns:
            The failure message naming every unresolved declaration, or
            ``None`` for a selected theme or when every payload declaration
            has a resolved owner.

        """
        if self.focused:
            return None
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

    def _plan_phase_callbacks(
        self,
        root: Path,
        candidate: p.Infra.SemanticSourcePlan,
        graph: p.Infra.RopeWorkspaceDsl,
        *,
        callbacks: Sequence[p.Infra.ModLoopPhase] | None = None,
    ) -> p.Result[p.Infra.SemanticSourcePlan]:
        """Compose callback effects in order over the staged view.

        Returns:
            The latest staged view, or the first planning failure.

        """
        for callback in self.phase_callbacks if callbacks is None else callbacks:
            self.progress.emit(f"mod: plan phase {callback.name}")
            sources = self._planning_sources(candidate.candidate)
            preflight = self._preview_ast_candidate(
                root,
                {},
                {state.path: state for state in candidate.candidate.inputs},
                candidate.candidate,
            )
            if preflight.failure:
                return r[p.Infra.SemanticSourcePlan].from_failure(preflight)
            graph.bind_candidate(
                declared_files=FlextInfraCodemodSemanticApply.planning_file_plans(
                    root, candidate.candidate, sources
                )
            )
            planned = callback.plan(root, preflight.value, graph, sources=sources)
            if planned.failure:
                return r[p.Infra.SemanticSourcePlan].from_failure(planned)
            if not self._coherent(callback.name, [plan.path for plan in planned.value]):
                continue
            composed = FlextInfraCodemodSemanticApply.compose_candidate(
                candidate, planned.value
            )
            if composed.failure:
                return composed
            candidate = composed.value
        return r[p.Infra.SemanticSourcePlan].ok(candidate)

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
    def validate_fix_match[FindingT: p.Infra.ModOccurrence](
        before: p.Infra.ModOccurrenceReport[FindingT],
        after_apply: p.Infra.ModOccurrenceReport[FindingT],
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
