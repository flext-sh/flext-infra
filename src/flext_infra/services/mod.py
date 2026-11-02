"""Public codemod handler composed into the infrastructure service by MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

import flext_infra
from flext_infra import c, codemod, m, r, t
from flext_infra.codemod.loop import (
    FlextInfraCodemodLoopPhaseAccessorRename,
    FlextInfraCodemodLoopPhaseDuplicateApply,
    FlextInfraCodemodLoopPhaseFacadeComponents,
    FlextInfraCodemodLoopPhaseImportNormalization,
    FlextInfraCodemodLoopPhaseNamespaceRelocation,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraModHandlers:
    """Compose the existing mod executor using the API's injected capabilities."""

    @staticmethod
    def _semantic_decisions_request(
        root: Path,
        decisions: Path,
        output: Path | None,
        request: p.Infra.ModRequest,
    ) -> tuple[m.Infra.SemanticRenamePlanCommand, m.Cli.AtomicFileState]:
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
        campaigns_config: m.Infra.RefactorCsvCampaignsSpec,
    ) -> p.Result[t.Cli.ResultValue] | None:
        """Reject declared campaigns whose drivers or roots escape their boundary.

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
        declared: m.Infra.RenameCampaignSpec,
        *,
        apply: bool,
    ) -> m.Infra.ApplyRenamesInput:
        """Bind one declared CSV campaign to this invocation's write mode."""
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
        declared: m.Infra.RenameCampaignSpec,
        *,
        apply: bool,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Inspect or converge exactly one CSV campaign, never its siblings."""
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
        """Construct the one callback explicitly admitted by configuration."""
        callbacks: dict[str, p.Infra.ModRuleOwnerRunner] = {
            "import-normalization": FlextInfraCodemodLoopPhaseImportNormalization(),
            "facade-components": FlextInfraCodemodLoopPhaseFacadeComponents(),
            "namespace-relocations": FlextInfraCodemodLoopPhaseNamespaceRelocation(),
            "duplicate-apply": FlextInfraCodemodLoopPhaseDuplicateApply(),
            "accessor-rename": FlextInfraCodemodLoopPhaseAccessorRename(rope_project),
        }
        return callbacks[name]

    @staticmethod
    def _focused_callback(
        root: Path,
        callback: p.Infra.ModRuleOwnerRunner,
        *,
        apply: bool,
        rope: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[t.Cli.ResultValue]:
        """Plan and converge one callback without global mod triage."""

        def plan() -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
            preflight = codemod.FlextInfraModGateEngine.scan(root, fix=False)
            if preflight.failure:
                return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(preflight)
            sources = codemod.FlextInfraCodemodSemanticApply.source_inventory(
                root, preflight.value
            )
            return callback.plan(root, preflight.value, rope, sources=sources)

        planned = plan()
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        if not planned.value:
            return r[t.Cli.ResultValue].ok(value=True)
        if not apply:
            return r[t.Cli.ResultValue].fail(
                f"mod: selected callback {callback.name} proposes "
                f"{len(planned.value)} file change(s)"
            )
        published = flext_infra.u.Infra.publish_codegen_plans(root, planned.value)
        if published.failure:
            return r[t.Cli.ResultValue].from_failure(published)
        rope.refresh()
        residual = plan()
        if residual.failure:
            return r[t.Cli.ResultValue].from_failure(residual)
        if residual.value:
            return r[t.Cli.ResultValue].fail(
                f"mod: selected callback {callback.name} retains "
                f"{len(residual.value)} file change(s)"
            )
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def _focused_semantic(
        root: Path,
        *,
        apply: bool,
        rope: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[t.Cli.ResultValue]:
        """Plan and converge semantic cutover without unrelated mod phases."""

        def plan() -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
            preflight = codemod.FlextInfraModGateEngine.scan(root, fix=False)
            if preflight.failure:
                return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(preflight)
            sources = codemod.FlextInfraCodemodSemanticApply.source_inventory(
                root, preflight.value, source_project=rope.rope_project
            )
            edits = codemod.FlextInfraCodemodSemanticApply.plan_semantic_edits(
                root, preflight.value, rope, sources
            )
            if edits.failure:
                return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(edits)
            return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(
                tuple(
                    flext_infra.u.Infra.source_file_plan_from_edit(
                        root,
                        edit,
                        source_project=rope.rope_project,
                        declared_files={},
                    )
                    for edit in edits.value
                )
            )

        planned = plan()
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        if not planned.value:
            return r[t.Cli.ResultValue].ok(value=True)
        if not apply:
            return r[t.Cli.ResultValue].fail(
                f"mod: selected semantic cutover proposes {len(planned.value)} file change(s)"
            )
        published = flext_infra.u.Infra.publish_codegen_plans(root, planned.value)
        if published.failure:
            return r[t.Cli.ResultValue].from_failure(published)
        rope.refresh()
        residual = plan()
        if residual.failure:
            return r[t.Cli.ResultValue].from_failure(residual)
        if residual.value:
            return r[t.Cli.ResultValue].fail(
                "mod: selected semantic cutover retains "
                f"{len(residual.value)} file change(s)"
            )
        return r[t.Cli.ResultValue].ok(value=True)

    def mod(
        self: p.Infra.ModExecutionContext,
        request: p.Infra.ModRequest,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Execute the codemod use case through the invocation-owned Rope session.

        Returns:
            The executor's result, preserving its first failure.

        """
        root = flext_infra.u.Infra.resolve_repository_root_or_cwd(
            request.repository_root
        )
        selected = flext_infra.u.Infra.load_refactor_csv_campaigns(root)
        if selected.failure:
            return r[t.Cli.ResultValue].from_failure(selected)
        campaigns_config = selected.value
        if request.rule_id is not None:
            text_rules = codemod.FlextInfraModTextGateEngine.load_rules(root)
            if text_rules.failure:
                return r[t.Cli.ResultValue].from_failure(text_rules)
            campaign = next(
                (
                    item
                    for item in campaigns_config.campaigns
                    if item.id == request.rule_id
                ),
                None,
            )
            owner = next(
                (
                    item
                    for item in campaigns_config.owners
                    if item.id == request.rule_id
                ),
                None,
            )
            sources = sum((
                request.rule_id in {rule.rule_id for rule in text_rules.value},
                campaign is not None,
                owner is not None,
            ))
            if sources > 1:
                return r[t.Cli.ResultValue].fail(
                    f"ambiguous refactor mod rule selector {request.rule_id}"
                )
            if request.rule_id in {rule.rule_id for rule in text_rules.value}:
                return codemod.FlextInfraModTextGateEngine.run(
                    root, apply=request.apply, rule_ids=(request.rule_id,)
                )
            if campaign is not None:
                scope_failure = FlextInfraModHandlers._campaign_scope_failure(
                    root,
                    root / c.CONFIG_DIR_NAME,
                    campaigns_config.model_copy(update={"campaigns": (campaign,)}),
                )
                if scope_failure is not None:
                    return scope_failure
                return FlextInfraModHandlers._focused_csv(
                    root, campaign, apply=request.apply, progress=progress
                )
            if owner is not None:
                if (
                    request.rename_plan is not None
                    or campaigns_config.semantic_decisions
                ):
                    return r[t.Cli.ResultValue].fail(
                        "selected semantic/callback owner conflicts with rename plan or decisions"
                    )
                structural_root = flext_infra.u.Infra.import_project_roots(root)[
                    0
                ].resolve()
                with self.rope_workspace(root, structural_root) as rope:
                    if owner.kind == "semantic":
                        return FlextInfraModHandlers._focused_semantic(
                            root, apply=request.apply, rope=rope
                        )
                    callback = FlextInfraModHandlers._callback(
                        owner.callback or "", rope.rope_project
                    )
                    return FlextInfraModHandlers._focused_callback(
                        root, callback, apply=request.apply, rope=rope
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
        campaigns = tuple(
            m.Infra.ApplyRenamesInput(
                repository_root=root,
                csv=str(config_dir / declared.csv),
                roots=tuple(str((root / value).resolve()) for value in declared.roots)
                or (str(root),),
                apply=request.apply,
                bindings=declared.bindings,
                rename_definitions=declared.rename_definitions,
                text_globs=declared.text_globs,
                python_documentation=declared.python_documentation,
                exclude_globs=declared.exclude_globs,
            )
            for declared in campaigns_config.campaigns
        )
        structural_root = flext_infra.u.Infra.import_project_roots(root)[0].resolve()
        source_preview = self.source_preview(structural_root)
        with self.rope_workspace(root, structural_root) as rope:
            return codemod.FlextInfraCodemodBatchApply(
                workspace_factory=self.rope_workspace,
                source_preview=source_preview,
                repository_root=root,
                consumer_roots=request.consumer_roots,
                rule_id=request.rule_id,
                rename_plan=rename_plan,
                apply_changes=request.apply,
                check_only=request.check,
                dry_run=request.dry_run_mode,
                rename_runner=codemod.FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
                rename_inputs=campaigns,
                phase_callbacks=(
                    FlextInfraCodemodLoopPhaseImportNormalization(),
                    FlextInfraCodemodLoopPhaseFacadeComponents(),
                    FlextInfraCodemodLoopPhaseNamespaceRelocation(),
                    FlextInfraCodemodLoopPhaseDuplicateApply(),
                    FlextInfraCodemodLoopPhaseAccessorRename(rope.rope_project),
                ),
            ).execute()


__all__: list[str] = ["FlextInfraModHandlers"]
