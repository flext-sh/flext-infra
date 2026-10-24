"""Public codemod handler composed into the infrastructure service by MRO.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codemod import (
    FlextInfraAccessorRenamePhase,
    FlextInfraApplyRenames,
    FlextInfraCodemodBatchApply,
    FlextInfraCodemodSemanticApply,
    FlextInfraDuplicateApplyPhase,
    FlextInfraImportNormalizationPhase,
    FlextInfraNamespaceRelocationPhase,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraModHandlers:
    """Compose the existing mod executor using the API's injected capabilities."""

    def mod(
        self: p.Infra.ModExecutionContext,
        request: p.Infra.ModRequest,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Execute the codemod use case through the invocation-owned Rope session.

        Returns:
            The executor's result, preserving its first failure.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        selected = u.Infra.load_refactor_csv_campaigns(root)
        if selected.failure:
            return r[t.Cli.ResultValue].from_failure(selected)
        campaigns_config = selected.value
        rename_plan = request.rename_plan or campaigns_config.semantic_plan
        selections: m.Infra.SemanticRenameSelections | None = None
        decisions_states: t.VariadicTuple[m.Cli.AtomicFileState] = ()
        if campaigns_config.semantic_decisions is not None:
            if request.rename_plan is not None:
                msg = "explicit rename_plan conflicts with declared semantic_decisions"
                raise ValueError(msg)
            decisions_path = root / campaigns_config.semantic_decisions
            if not decisions_path.resolve().is_relative_to(root.resolve()):
                msg = "semantic decisions escape workspace"
                raise ValueError(msg)
            decisions_state = u.Cli.atomic_read_binary_file_state(
                decisions_path, required=True
            ).unwrap()
            if decisions_state.content is None:
                msg = f"semantic decisions disappeared: {decisions_path}"
                raise ValueError(msg)
            selections = m.Infra.SemanticRenameSelections.model_validate_json(
                decisions_state.content
            )
            if not selections.decisions:
                msg = "semantic rename requires an explicit naming decision"
                raise ValueError(msg)
            if rename_plan is None:
                msg = "semantic_decisions requires semantic_plan"
                raise ValueError(msg)
            decisions_states = (decisions_state,)
        config_dir = root / c.CONFIG_DIR_NAME
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
            for path in campaign_roots:
                if not path.resolve().is_relative_to(repository_root):
                    return r[t.Cli.ResultValue].fail(
                        f"CSV campaign scan root escapes repository: {path}",
                    )
        campaigns = tuple(
            m.Infra.ApplyRenamesInput(
                repository_root=root,
                csv=str(config_dir / declared.csv),
                roots=tuple(str((root / value).resolve()) for value in declared.roots)
                or (str(root),),
                apply=request.apply and not request.check and not request.dry_run_mode,
                bindings=declared.bindings,
                rename_definitions=declared.rename_definitions,
                text_globs=declared.text_globs,
                python_documentation=declared.python_documentation,
                exclude_globs=declared.exclude_globs,
            )
            for declared in campaigns_config.campaigns
        )
        structural_root = u.Infra.import_project_roots(root)[0].resolve()
        source_preview = self.source_preview(structural_root)
        consumer_roots = request.consumer_roots
        with self.rope_workspace(root, structural_root) as rope:
            declared_driver: m.Cli.AtomicFileState | None = None
            native_plan: m.Infra.SemanticRenamePlan | None = None
            if selections is not None and rename_plan is not None:
                if consumer_roots and set(consumer_roots) != set(
                    selections.consumer_roots
                ):
                    msg = "run consumer roots differ from declared decisions"
                    raise ValueError(msg)
                consumer_roots = selections.consumer_roots
                if request.apply and not request.check and not request.dry_run_mode:
                    published = FlextInfraCodemodSemanticApply.publish_rename_plan(
                        root, rope, selections, rename_plan, inputs=decisions_states
                    )
                    if published.failure:
                        return r[t.Cli.ResultValue].from_failure(published)
                    declared_driver = u.Cli.atomic_read_binary_file_state(
                        root / rename_plan, required=True
                    ).unwrap()
                    if (
                        declared_driver.content is None
                        or m.Infra.SemanticRenamePlan.model_validate_json(
                            declared_driver.content
                        ) != published.value
                    ):
                        msg = "declared rename artifact changed before consumption"
                        raise ValueError(msg)
                else:
                    planned = FlextInfraCodemodSemanticApply.plan_rename_artifact(
                        root, rope, selections, rename_plan, inputs=decisions_states
                    )
                    if planned.failure:
                        return r[t.Cli.ResultValue].from_failure(planned)
                    native_plan, declared_driver = planned.value
                    if (
                        FlextInfraCodemodSemanticApply.rename_selections(
                            native_plan
                        ).decisions != selections.decisions
                    ):
                        msg = "native rename plan differs from declared decisions"
                        raise ValueError(msg)
                    rename_plan = None
            return FlextInfraCodemodBatchApply(
                workspace_factory=self.rope_workspace,
                source_preview=source_preview,
                repository_root=root,
                consumer_roots=consumer_roots,
                rename_plan=rename_plan,
                native_plan=native_plan,
                driver_states=(
                    *decisions_states,
                    *((declared_driver,) if declared_driver is not None else ()),
                ),
                apply_changes=request.apply,
                check_only=request.check,
                dry_run=request.dry_run_mode,
                rename_runner=FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
                rename_inputs=campaigns,
                phase_callbacks=(
                    FlextInfraImportNormalizationPhase(),
                    FlextInfraNamespaceRelocationPhase(),
                    FlextInfraDuplicateApplyPhase(),
                    FlextInfraAccessorRenamePhase(source_preview=source_preview),
                ),
            ).execute()


__all__: list[str] = ["FlextInfraModHandlers"]
