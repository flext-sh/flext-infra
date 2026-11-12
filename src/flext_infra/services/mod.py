"""Public codemod handler composed into the infrastructure service by MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence
from functools import partial
from pathlib import Path

from flext_infra import c, codemod, m, p, r, t, u
from flext_infra.codegen import FlextInfraStagedPackage
from flext_infra.codemod.loop import (
    FlextInfraCodemodLoopPhaseAccessorRename,
    FlextInfraCodemodLoopPhaseDuplicateApply,
    FlextInfraCodemodLoopPhaseFacadeComponents,
    FlextInfraCodemodLoopPhaseImportNormalization,
    FlextInfraCodemodLoopPhaseNamespaceRelocation,
)
from flext_infra.gates import FlextInfraGatesPyrefly
from flext_infra.validate import FlextInfraValidateFreshImport


class FlextInfraModHandlers:
    """Compose the existing mod executor using the API's injected capabilities."""

    @staticmethod
    def model_envelope_diagnostics(
        root: Path,
        sources: Mapping[Path, str],
        *,
        runtime_root: Path | None = None,
        storage_root: Path | None = None,
    ) -> Sequence[p.Infra.Issue]:
        """Compose the native checker once on the complete current source stage.

        Returns:
            Original findings mapped back to the supplied source candidate.

        """
        roots = u.Infra.import_project_roots(root)
        if runtime_root is None:
            runtime_root = u.Infra.runtime_owner_root(root).unwrap()
        stage_workspace = Path(os.path.commonpath(roots))
        projects = tuple(
            project
            for project in roots
            if project.is_relative_to(root)
            and any(path.is_relative_to(project) for path in sources)
        )
        u.Cli.info(
            f"mod: model-envelope checker root={root} workspace={stage_workspace} "
            f"projects={tuple(project.name for project in projects)}"
        )
        reports = (
            m.Infra.RunCommand(repository_root=runtime_root).reports_dir_path
            / u.generate_id()
        )

        def inspect(view: Path, _paths: Mapping[Path, Path]) -> Sequence[p.Infra.Issue]:
            findings: list[p.Infra.Issue] = []
            for project in projects:
                candidate = view / project.relative_to(stage_workspace)
                report_directory = reports / project.name
                u.Cli.ensure_dir(report_directory).unwrap()
                result = FlextInfraGatesPyrefly(repository_root=root).check(
                    candidate,
                    m.Infra.GateContext(
                        repository_root=candidate,
                        runtime_root=runtime_root,
                        reports_dir=report_directory,
                    ),
                )
                if result.outcome == c.Infra.ToolOutcome.ERROR:
                    message = "\n".join(issue.message for issue in result.issues)
                    raise RuntimeError(message or result.raw_output)
                for issue in result.issues:
                    path = Path(issue.file)
                    path = path if path.is_absolute() else candidate / path
                    logical = (
                        stage_workspace / path.relative_to(view)
                        if path.is_relative_to(view)
                        else path
                    )
                    findings.append(issue.model_copy(update={"file": str(logical)}))
            return tuple(findings)

        return (
            FlextInfraStagedPackage()
            .preview_sources(
                stage_workspace, sources, inspect, storage_root=storage_root
            )
            .unwrap()
        )

    @staticmethod
    def _mod_semantic_rule(
        context: p.Infra.ModExecutionContext,
        root: Path,
        request: p.Infra.ModCommand,
        selected: p.Infra.RopeContractRules,
        catalogue_inputs: tuple[p.Cli.AtomicFileState, ...],
    ) -> p.Result[t.Cli.ResultValue]:
        """Plan one declared semantic identity on the existing authenticated owner.

        Returns:
            The native planning/publication failure, pending preview, or acceptance.

        """
        outcome = r[t.Cli.ResultValue]
        structural_root = u.Infra.import_project_roots(root)[0].resolve()
        with context.rope_workspace(root, structural_root) as workspace:
            seed = codemod.FlextInfraCodemodSemanticApply.build_source_plan(
                root, request.consumer_roots, snapshot=workspace.snapshot
            )
            if seed.failure:
                return outcome.from_failure(seed)
            candidate = seed.value.candidate
            planned = u.Infra.plan_contract_rules(
                workspace,
                u.Infra.candidate_python_sources(candidate, candidate.inputs),
                selected.rules,
                options=m.Infra.ContractAdmissionOptions.model_validate({
                    "signature_additions": (selected.signature_additions),
                    "signature_removals": (selected.signature_removals),
                    "method_transfers": (selected.method_transfers),
                }),
            )
            if planned.failure:
                return outcome.from_failure(planned)
            staged = FlextInfraStagedPackage.plan_sources(
                candidate.workspace,
                {edit.file_path: edit.updated_source for edit in planned.value},
                options=m.Infra.StageSourceOptions.model_validate({
                    "snapshot": (workspace.snapshot),
                    "workspaces": (candidate.workspaces),
                    "inputs": ((*candidate.inputs, *catalogue_inputs)),
                    "modes": (candidate.modes),
                }),
            )
            if staged.failure:
                return outcome.from_failure(staged)
            published = codemod.FlextInfraCodemodSemanticApply.publish_candidate(
                root,
                m.Infra.SemanticSourcePlan(
                    candidate=staged.value, consumer_roots=seed.value.consumer_roots
                ),
                publish=request.apply,
                validator=partial(
                    FlextInfraModHandlers._validate_semantic_rule,
                    context=context,
                    selected=selected,
                    reports_root=root,
                    repository_relative=root.relative_to(structural_root),
                ),
            )
        if published.failure:
            return outcome.from_failure(published)
        if not request.apply and published.value:
            return outcome.fail(
                f"{request.rule_id}: {len(published.value)} pending semantic file(s)"
            )
        return outcome.ok(value=True)

    @staticmethod
    def _validate_semantic_rule(
        root: Path,
        *,
        context: p.Infra.ModExecutionContext,
        selected: p.Infra.RopeContractRules,
        reports_root: Path,
        repository_relative: Path,
    ) -> p.Result[bool]:
        """Verify the same logical repository inside its physical staged workspace.

        Returns:
            The original planning/runtime failure, or staged consumer acceptance.

        """
        outcome = r[bool]
        root /= repository_relative
        structural_root = u.Infra.import_project_roots(root)[0].resolve()
        with context.rope_workspace(root, structural_root) as workspace:
            workspace.model_envelope_checker = partial(
                FlextInfraModHandlers.model_envelope_diagnostics,
                root,
                runtime_root=u.Infra.runtime_owner_root(reports_root).unwrap(),
                storage_root=reports_root,
            )
            captured = codemod.FlextInfraCodemodSemanticApply.build_source_plan(
                root, snapshot=workspace.snapshot
            )
            if captured.failure:
                return outcome.from_failure(captured)
            candidate = captured.value.candidate
            planned = u.Infra.plan_contract_rules(
                workspace,
                u.Infra.candidate_python_sources(candidate, candidate.inputs),
                selected.rules,
                options=m.Infra.ContractAdmissionOptions.model_validate({
                    "signature_additions": (selected.signature_additions),
                    "signature_removals": (selected.signature_removals),
                    "method_transfers": (selected.method_transfers),
                }),
            )
        if planned.failure:
            return outcome.from_failure(planned)
        if planned.value:
            return outcome.fail("selected semantic candidate is not a fixed point")
        return (
            FlextInfraValidateFreshImport(
                repository_root=root,
                runtime_root=u.Infra.runtime_owner_root(reports_root).unwrap(),
            )
            .build_report(repository_roots=(root,))
            .flat_map(
                lambda report: (
                    outcome.ok(value=True)
                    if report.passed
                    else outcome.fail("\n".join((report.summary, *report.violations)))
                )
            )
        )

    @staticmethod
    def _semantic_decisions_request(
        root: Path,
        decisions: Path,
        output: Path | None,
        request: p.Infra.ModCommand,
    ) -> tuple[p.Infra.SemanticRenamePlanCommand, p.Cli.AtomicFileState]:
        """Validate configured decisions at their required-content boundary.

        Returns:
            The native planner request and original decisions witness.

        Raises:
            ValueError: If decisions conflict with the request or escape the workspace.

        """
        if request.rename_plan is not None:
            msg = "explicit rename_plan conflicts with declared semantic_decisions"
            raise ValueError(msg)
        decisions_path = (root / decisions).resolve()
        if not decisions_path.is_relative_to(root.resolve()):
            msg = "semantic decisions escape workspace"
            raise ValueError(msg)
        state = u.Cli.atomic_read_binary_file_state(
            decisions_path, required=True
        ).unwrap()
        if state.content is None:
            msg = "semantic decisions content is absent"
            raise ValueError(msg)
        selections = m.Infra.SemanticRenameSelections.model_validate_json(state.content)
        if output is None:
            msg = "semantic_decisions requires semantic_plan"
            raise ValueError(msg)
        return (
            m.Infra.SemanticRenamePlanCommand(
                repository_root=root,
                decisions=selections.model_dump_json(round_trip=True),
                output=output,
            ),
            state,
        )

    @staticmethod
    def _campaign_scope_failure(
        root: Path,
        config_dir: Path,
        campaigns_config: p.Infra.RefactorCsvCampaignsSpec,
    ) -> p.Result[t.Cli.ResultValue] | None:
        """Reject declared CSV campaigns that escape their boundary.

        Returns:
            The first boundary failure, or ``None`` when every campaign is contained.

        """
        config_root = config_dir.resolve()
        repository_root = root.resolve()
        for declared in campaigns_config.campaigns:
            csv = config_dir / declared.csv
            if not csv.resolve().is_relative_to(config_root):
                return r[t.Cli.ResultValue].fail(
                    f"CSV campaign driver escapes config directory: {csv}",
                )
            campaign_roots = tuple(
                (root / value).resolve() for value in declared.roots
            ) or (root,)
            escaped = next(
                (
                    path
                    for path in campaign_roots
                    if not path.is_relative_to(repository_root)
                ),
                None,
            )
            if escaped is not None:
                return r[t.Cli.ResultValue].fail(
                    f"CSV campaign scan root escapes repository: {escaped}",
                )
        return None

    @staticmethod
    def _campaign_input(
        root: Path,
        declared: p.Infra.RenameCampaignSpec,
        *,
        apply: bool,
    ) -> p.Infra.ApplyRenamesInput:
        """Bind one declared CSV campaign to this invocation's write mode.

        Returns:
            The native request retaining every declared campaign option.

        """
        config_dir = root / c.CONFIG_DIR_NAME
        return m.Infra.ApplyRenamesInput(
            repository_root=root,
            csv=str(config_dir / declared.csv),
            roots=tuple(str((root / value).resolve()) for value in declared.roots)
            or (str(root),),
            apply=apply,
            bindings=declared.bindings,
            rename_definitions=declared.rename_definitions,
            text_globs=declared.text_globs,
            python_documentation=declared.python_documentation,
            exclude_globs=declared.exclude_globs,
        )

    @staticmethod
    def _focused_csv(
        root: Path,
        declared: p.Infra.RenameCampaignSpec,
        *,
        apply: bool,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Inspect or converge exactly one CSV campaign, never its siblings.

        Returns:
            The original rename failure or converged campaign acceptance.

        """
        runner = codemod.FlextInfraApplyRenames()
        first = runner.run(
            FlextInfraModHandlers._campaign_input(root, declared, apply=apply)
        )
        if first.failure:
            return r[t.Cli.ResultValue].from_failure(first)
        progress.emit_rename(first.value)
        residual = runner.run(
            FlextInfraModHandlers._campaign_input(root, declared, apply=False)
        )
        if residual.failure:
            return r[t.Cli.ResultValue].from_failure(residual)
        if residual.value.occurrences:
            return r[t.Cli.ResultValue].fail(
                f"mod: selected CSV campaign {declared.id} retains "
                f"{residual.value.occurrences} occurrence(s)"
            )
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def _callback(
        name: str,
        rope_project: p.Infra.RopeProject,
    ) -> p.Infra.ModRuleOwnerRunner:
        """Construct the one callback explicitly admitted by configuration.

        Returns:
            The configured native owner bound to the elected project.

        """
        callbacks: dict[str, p.Infra.ModRuleOwnerRunner] = {
            "import-normalization": FlextInfraCodemodLoopPhaseImportNormalization(),
            "facade-components": FlextInfraCodemodLoopPhaseFacadeComponents(),
            "namespace-relocations": FlextInfraCodemodLoopPhaseNamespaceRelocation(),
            "duplicate-apply": FlextInfraCodemodLoopPhaseDuplicateApply(),
            "accessor-rename": FlextInfraCodemodLoopPhaseAccessorRename(rope_project),
        }
        return callbacks[name]

    @staticmethod
    def _converge_selected(
        root: Path,
        plan: Callable[[], p.Result[tuple[p.Infra.CodegenFilePlan, ...]]],
        *,
        apply: bool,
        rope: p.Infra.RopeWorkspaceDsl,
        owner: str,
    ) -> p.Result[t.Cli.ResultValue]:
        """Publish and replan one selected owner through the existing lifecycle.

        Returns:
            The original failure, pending preview, or converged acceptance.

        """
        outcome = r[t.Cli.ResultValue]
        planned = plan()
        if planned.failure:
            return outcome.from_failure(planned)
        if not planned.value:
            return outcome.ok(value=True)
        if not apply:
            return outcome.fail(
                f"mod: selected {owner} proposes {len(planned.value)} file change(s)"
            )
        published = u.Infra.publish_codegen_plans(root, planned.value)
        if published.failure:
            return outcome.from_failure(published)
        rope.refresh()
        residual = plan()
        if residual.failure:
            return outcome.from_failure(residual)
        return (
            outcome.fail(
                f"mod: selected {owner} retains {len(residual.value)} file change(s)"
            )
            if residual.value
            else outcome.ok(value=True)
        )

    @staticmethod
    def _focused_callback(
        root: Path,
        callback: p.Infra.ModRuleOwnerRunner,
        *,
        apply: bool,
        rope: p.Infra.RopeWorkspaceDsl,
        artifact_planner: Callable[
            [Path, p.Infra.SemanticSourcePlan],
            p.Result[tuple[p.Infra.CodegenFilePlan, ...]],
        ]
        | None = None,
    ) -> p.Result[t.Cli.ResultValue]:
        """Plan and converge one callback without global mod triage.

        Returns:
            The callback's original failure or converged native effects.

        """

        def plan() -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
            preflight = codemod.FlextInfraModGateEngine.scan(root, fix=False)
            if preflight.failure:
                return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(preflight)
            sources = codemod.FlextInfraCodemodSemanticApply.source_inventory(
                root, preflight.value, source_project=rope.rope_project
            )
            effects = callback.plan(root, preflight.value, rope, sources=sources)
            if effects.failure or not effects.value or artifact_planner is None:
                return effects
            seed = codemod.FlextInfraCodemodSemanticApply.build_source_plan(root)
            if seed.failure:
                return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(seed)
            composed = codemod.FlextInfraCodemodSemanticApply.compose_candidate(
                seed.value, effects.value
            )
            if composed.failure:
                return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(composed)
            return artifact_planner(root, composed.value).map(
                lambda artifacts: (*effects.value, *artifacts)
            )

        return FlextInfraModHandlers._converge_selected(
            root, plan, apply=apply, rope=rope, owner=f"callback {callback.name}"
        )

    @staticmethod
    def _focused_semantic(
        root: Path,
        *,
        apply: bool,
        rope: p.Infra.RopeWorkspaceDsl,
        phase: c.Infra.SemanticCutoverPhase | None = None,
    ) -> p.Result[t.Cli.ResultValue]:
        """Plan and converge semantic cutover without unrelated mod phases.

        Returns:
            The semantic owner's original failure or converged native effects.

        """

        def plan() -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
            rule_ids = (
                c.Infra.SEMANTIC_CUTOVER_RULE_IDS.get(phase, ())
                if phase is not None
                else ()
            )
            preflight = codemod.FlextInfraModGateEngine.scan(
                root,
                fix=False,
                selection=rule_ids or None,
            )
            if preflight.failure:
                return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(preflight)
            findings = (
                tuple(
                    entry
                    for entry in preflight.value.entries
                    if entry.rule_id in rule_ids
                )
                if rule_ids
                else preflight.value.entries
            )
            sources = codemod.FlextInfraCodemodSemanticApply.source_inventory(
                root, preflight.value, source_project=rope.rope_project
            )
            edits = (
                u.Infra.plan_semantic_cutover(
                    phase,
                    rope_workspace=rope,
                    sources=sources,
                    findings=findings,
                    import_normalizer=u.Infra.normalize_import_source,
                )
                if phase is not None
                else codemod.FlextInfraCodemodSemanticApply.plan_semantic_edits(
                    root, preflight.value, rope, sources
                )
            )
            if edits.failure:
                return r[tuple[p.Infra.CodegenFilePlan, ...]].from_failure(edits)
            return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(
                tuple(
                    u.Infra.source_file_plan_from_edit(
                        root,
                        edit,
                        source_project=rope.rope_project,
                        declared_files={},
                    )
                    for edit in edits.value
                )
            )

        return FlextInfraModHandlers._converge_selected(
            root,
            plan,
            apply=apply,
            rope=rope,
            owner=phase.value if phase is not None else "semantic cutover",
        )

    @staticmethod
    def _declared_selection(
        context: p.Infra.ModExecutionContext,
        root: Path,
        request: p.Infra.ModCommand,
        progress: p.Infra.ModProgress,
        campaigns: p.Infra.RefactorCsvCampaignsSpec,
    ) -> p.Result[t.Cli.ResultValue] | None:
        """Dispatch one validated campaign or owner without reclassifying rules.

        Returns:
            The selected owner's result, or None when no declaration matches.

        """
        campaign = next(
            (item for item in campaigns.campaigns if item.id == request.rule_id), None
        )
        if campaign is not None:
            boundary = FlextInfraModHandlers._campaign_scope_failure(
                root,
                root / c.CONFIG_DIR_NAME,
                m.Infra.RefactorCsvCampaignsSpec.model_validate({
                    "campaigns": ((campaign,)),
                    "owners": (campaigns.owners),
                    "semantic_plan": (campaigns.semantic_plan),
                    "semantic_decisions": (campaigns.semantic_decisions),
                    "rewire_directory": campaigns.rewire_directory,
                }),
            )
            return (
                boundary
                if boundary is not None
                else FlextInfraModHandlers._focused_csv(
                    root, campaign, apply=request.apply, progress=progress
                )
            )
        owner = next(
            (item for item in campaigns.owners if item.id == request.rule_id), None
        )
        if owner is None:
            return None
        if request.rename_plan is not None or campaigns.semantic_decisions:
            return r[t.Cli.ResultValue].fail(
                "selected semantic/callback owner conflicts with rename plan or "
                "decisions"
            )
        structural_root = u.Infra.import_project_roots(root)[0].resolve()
        with context.rope_workspace(root, structural_root) as rope:
            if owner.kind == "semantic":
                return FlextInfraModHandlers._focused_semantic(
                    root,
                    apply=request.apply,
                    rope=rope,
                    phase=(
                        c.Infra.SemanticCutoverPhase(owner.phase)
                        if owner.phase is not None
                        else None
                    ),
                )
            if owner.callback is None:
                return r[t.Cli.ResultValue].fail(
                    "declared callback owner has no callback"
                )
            facade = FlextInfraCodemodLoopPhaseFacadeComponents()
            callback = (
                facade
                if owner.callback == facade.name
                else FlextInfraModHandlers._callback(owner.callback, rope.rope_project)
            )
            return FlextInfraModHandlers._focused_callback(
                root,
                callback,
                apply=request.apply,
                rope=rope,
                artifact_planner=partial(
                    FlextInfraModHandlers._protocol_artifact_files,
                    organization=lambda: facade.protocol_organization,
                    directory=campaigns.rewire_directory,
                )
                if callback is facade
                else None,
            )

    @staticmethod
    def _selected_rule(
        context: p.Infra.ModExecutionContext,
        root: Path,
        request: p.Infra.ModCommand,
        progress: p.Infra.ModProgress,
        campaigns: p.Infra.RefactorCsvCampaignsSpec,
    ) -> p.Result[t.Cli.ResultValue]:
        """Resolve every declared rule domain before dispatching a unique identity.

        Returns:
            The uniquely selected owner result, or the original selection failure.

        Raises:
            ValueError: The request has no rule identity to select.

        """
        selector = request.rule_id
        if selector is None:
            message = "selected-rule execution requires a rule identity"
            raise ValueError(message)
        text_rules = codemod.FlextInfraModTextGateEngine.load_rules(root)
        if text_rules.failure:
            return r[t.Cli.ResultValue].from_failure(text_rules)
        with u.Infra.codemod_workspace_snapshot(root) as snapshot:
            ast_rules = u.Infra.codemod_rule_plan(snapshot, rule_ids=(selector,))
        if ast_rules.failure and ast_rules.error_code != c.ErrorCode.NOT_FOUND:
            return r[t.Cli.ResultValue].from_failure(ast_rules)
        additions: list[p.Infra.RopeSignatureAddition] = []
        removals: list[p.Infra.RopeSignatureRemoval] = []
        transfers: list[p.Infra.RopeMethodTransfer] = []
        catalogue_inputs: list[p.Cli.AtomicFileState] = []
        rules = u.Infra.declared_contract_rules(
            root,
            signature_additions=additions,
            signature_removals=removals,
            method_transfers=transfers,
            catalogue_inputs=catalogue_inputs,
        )
        native = m.Infra.RopeContractRules.model_validate({
            "rules": tuple(rule for rule in rules if rule.id == request.rule_id),
            "signature_additions": tuple(
                rule for rule in additions if rule.id == request.rule_id
            ),
            "signature_removals": tuple(
                rule for rule in removals if rule.id == request.rule_id
            ),
            "method_transfers": tuple(
                rule for rule in transfers if rule.id == request.rule_id
            ),
        })
        native_selected = bool(
            native.rules
            or native.signature_additions
            or native.signature_removals
            or native.method_transfers
        )
        ast_selected = ast_rules.success
        text_selected = request.rule_id in {rule.rule_id for rule in text_rules.value}
        if (
            sum((
                native_selected,
                ast_selected,
                text_selected,
                any(item.id == request.rule_id for item in campaigns.campaigns),
                any(item.id == request.rule_id for item in campaigns.owners),
            ))
            > 1
        ):
            return r[t.Cli.ResultValue].fail(
                f"ambiguous refactor mod rule selector {request.rule_id}"
            )
        if native_selected:
            return (
                r[t.Cli.ResultValue].fail(
                    "a semantic rule cannot also consume a rename plan"
                )
                if request.rename_plan is not None
                else FlextInfraModHandlers._mod_semantic_rule(
                    context, root, request, native, tuple(catalogue_inputs)
                )
            )
        if text_selected or ast_selected:
            return (
                codemod.FlextInfraModTextGateEngine.run(
                    root, apply=request.apply, rule_ids=(selector,)
                )
                if text_selected
                else FlextInfraModHandlers._execute_batch(
                    context, root, request, progress, None
                )
            )
        declared = FlextInfraModHandlers._declared_selection(
            context, root, request, progress, campaigns
        )
        return (
            declared
            if declared is not None
            else r[t.Cli.ResultValue].fail(
                f"unknown refactor mod rule selector: {request.rule_id}"
            )
        )

    @staticmethod
    def _protocol_artifact_files(
        root: Path,
        source_plan: p.Infra.SemanticSourcePlan,
        *,
        organization: Callable[[], p.Infra.ProtocolOrganizationPlan | None],
        directory: Path,
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Bind phase metadata to its existing native artifact planning owner.

        Returns:
            The admitted cohort's immutable artifact file plan, when one exists.

        """
        observed = organization()
        if observed is None:
            return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(())
        return codemod.FlextInfraCodemodSemanticApply.protocol_rewire_intents(
            root, source_plan, observed.census
        ).flat_map(
            lambda intents: (
                codemod.FlextInfraCodemodSemanticApply.rewire_artifact_file_plans(
                    root,
                    source_plan,
                    intents,
                    pre_move_sources=observed.pre_move_sources,
                    directory=directory,
                )
            )
        )

    @staticmethod
    def _execute_batch(
        context: p.Infra.ModExecutionContext,
        root: Path,
        request: p.Infra.ModCommand,
        progress: p.Infra.ModProgress,
        scope: p.Infra.RefactorCsvCampaignsSpec | tuple[str, ...] | None,
    ) -> p.Result[t.Cli.ResultValue]:
        """Compose the existing batch once for the selected native scope.

        ``scope`` is the declared campaigns of a rename-plan run, or the
        request's own exact AST rule IDs. A law theme reaches the batch
        unexpanded: the batch expands it over its own snapshot.

        Returns:
            The original executor result over the same captured workspace.

        """
        campaigns = None if isinstance(scope, tuple) else scope
        structural_root = u.Infra.import_project_roots(root)[0].resolve()
        source_preview = context.source_preview(structural_root)
        with context.rope_workspace(root, structural_root) as rope:
            facade = FlextInfraCodemodLoopPhaseFacadeComponents()
            return codemod.FlextInfraCodemodBatchApply(
                workspace_factory=context.rope_workspace,
                source_preview=source_preview,
                repository_root=root,
                consumer_roots=request.consumer_roots,
                rule_id=request.rule_id,
                rule_ids=(
                    scope if isinstance(scope, tuple) and request.laws is None else None
                ),
                laws=request.laws,
                rename_plan=(
                    request.rename_plan or campaigns.semantic_plan
                    if campaigns is not None
                    else None
                ),
                apply_changes=request.apply,
                check_only=request.check,
                dry_run=request.dry_run_mode,
                rename_runner=codemod.FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
                rename_inputs=(
                    tuple(
                        FlextInfraModHandlers._campaign_input(
                            root, declared, apply=request.apply
                        )
                        for declared in campaigns.campaigns
                    )
                    if campaigns is not None
                    else ()
                ),
                phase_callbacks=(
                    (
                        FlextInfraCodemodLoopPhaseImportNormalization(),
                        facade,
                        FlextInfraCodemodLoopPhaseNamespaceRelocation(),
                        FlextInfraCodemodLoopPhaseDuplicateApply(),
                        FlextInfraCodemodLoopPhaseAccessorRename(rope.rope_project),
                    )
                    if campaigns is not None
                    else ()
                ),
                artifact_planner=partial(
                    FlextInfraModHandlers._protocol_artifact_files,
                    organization=lambda: facade.protocol_organization,
                    directory=campaigns.rewire_directory,
                )
                if campaigns is not None
                else None,
            ).execute()

    @staticmethod
    def _execute_exact(
        context: p.Infra.ModExecutionContext,
        root: Path,
        request: p.Infra.ModCommand,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Run one theme over exact rule IDs: its own or its expanded laws.

        Laws expand inside this repository's own plan (static, generated and
        partitioned rules alike), once, over the batch's own snapshot; the
        batch accepts a theme its plan does not claim as nothing to check or
        fix. Exact IDs that all name declarative text rules replay only those
        rules to their verified fixed point; mixing them with catalog IDs is
        refused, because each owner proves its own fixed point.

        Returns:
            The exact text or batch result over the selected rule IDs.

        """
        if request.rule_ids is not None:
            text_rules = codemod.FlextInfraModTextGateEngine.load_rules(root)
            if text_rules.failure:
                return r[t.Cli.ResultValue].from_failure(text_rules)
            selected = frozenset(request.rule_ids)
            text_ids = selected.intersection(rule.rule_id for rule in text_rules.value)
            if text_ids == selected:
                return codemod.FlextInfraModTextGateEngine.run(
                    root, apply=request.apply, rule_ids=request.rule_ids
                )
            if text_ids:
                return r[t.Cli.ResultValue].fail(
                    "refactor mod --rule-ids mixes text rule IDs with catalog "
                    "rule IDs: " + ", ".join(sorted(text_ids))
                )
        return FlextInfraModHandlers._execute_batch(
            context,
            root,
            request,
            progress,
            request.rule_ids if request.laws is None else None,
        )

    def mod(
        self: p.Infra.ModExecutionContext,
        request: p.Infra.ModCommand,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Execute the codemod use case through the invocation-owned Rope session.

        Returns:
            The executor's result, preserving its first failure.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        if request.laws is not None or request.rule_ids is not None:
            return FlextInfraModHandlers._execute_exact(self, root, request, progress)
        selected = u.Infra.load_refactor_csv_campaigns(root)
        if selected.failure:
            return r[t.Cli.ResultValue].from_failure(selected)
        campaigns_config = selected.value
        if request.rule_id is not None:
            return FlextInfraModHandlers._selected_rule(
                self, root, request, progress, campaigns_config
            )
        rename_plan = request.rename_plan or campaigns_config.semantic_plan
        if campaigns_config.semantic_decisions is not None:
            configured = FlextInfraModHandlers._semantic_decisions_request(
                root, campaigns_config.semantic_decisions, rename_plan, request
            )
            published = codemod.FlextInfraCodemodSemanticApply.publish_rename_plan(
                configured[0], self.rope_workspace
            )
            if published.failure:
                return r[t.Cli.ResultValue].from_failure(published)
            u.Cli.atomic_verify_binary_file_states((configured[1],)).unwrap()
        config_dir = root / c.CONFIG_DIR_NAME
        scope_failure = FlextInfraModHandlers._campaign_scope_failure(
            root, config_dir, campaigns_config
        )
        if scope_failure is not None:
            return scope_failure
        return FlextInfraModHandlers._execute_batch(
            self, root, request, progress, campaigns_config
        )


__all__: list[str] = ["FlextInfraModHandlers"]
