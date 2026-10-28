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
                apply=request.apply and not request.check and not request.dry_run_mode,
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
                rename_plan=rename_plan,
                apply_changes=request.apply,
                check_only=request.check,
                dry_run=request.dry_run_mode,
                rename_runner=codemod.FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
                rename_inputs=campaigns,
                phase_callbacks=(
                    codemod.FlextInfraCodemodLoopPhaseImportNormalization(),
                    codemod.FlextInfraCodemodLoopPhaseNamespaceRelocation(),
                    codemod.FlextInfraCodemodLoopPhaseDuplicateApply(),
                    codemod.FlextInfraCodemodLoopPhaseAccessorRename(rope.rope_project),
                ),
            ).execute()


__all__: list[str] = ["FlextInfraModHandlers"]
