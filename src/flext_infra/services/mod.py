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
        with self.rope_workspace(root, structural_root) as rope:
            return FlextInfraCodemodBatchApply(
                workspace_factory=self.rope_workspace,
                source_preview=source_preview,
                repository_root=root,
                consumer_roots=request.consumer_roots,
                rename_plan=request.rename_plan or campaigns_config.semantic_plan,
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
