"""Duplicate-cure phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r
from flext_infra.codemod.duplicate_apply import FlextInfraCodemodDuplicateApply
from flext_infra.refactor._census import (
    FlextInfraRefactorCensusCollectHelpers,
    FlextInfraRefactorCensusFilters,
)
from flext_infra.transformers import FlextInfraTransformersSemanticPublication

if TYPE_CHECKING:
    from flext_infra import p, t


class FlextInfraCodemodLoopPhaseDuplicateApply:
    """Duplicate-cure callback: the census duplicate rule repaired in the loop.

    The phase rebuilds the workspace duplicate groups from the shared Rope
    inventory on every iteration, cures the identity-proven trivial groups
    through the journaled transaction, and leaves every structural duplicate
    as a typed manual plan — the loop then refreshes, rescans and converges
    when no curable group remains.
    """

    name: str = "duplicate-apply"

    @staticmethod
    def apply(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Cure the trivial duplicate groups of the current source state.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        del preflight
        groups = FlextInfraCodemodLoopPhaseDuplicateApply._duplicate_groups(
            rope_workspace
        )
        outcome = FlextInfraCodemodDuplicateApply.census_duplicates(
            root,
            rope_workspace,
            groups,
            apply=True,
        )
        if outcome.failure:
            return r[bool].from_failure(outcome)
        if outcome.value.plans:
            return r[bool].fail(
                "\n".join(plan.reason for plan in outcome.value.plans),
                error_code=c.Infra.ToolOutcome.ERROR.value,
            )
        return r[bool].ok(value=bool(outcome.value.edits))

    @staticmethod
    def plan(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan the trivial duplicate cures; a structural duplicate fails loud.

        Returns:
            The cure file plans, or the first unresolved duplicate plan.

        """
        del preflight
        planned = FlextInfraCodemodDuplicateApply.plan_census(
            root,
            rope_workspace,
            FlextInfraCodemodLoopPhaseDuplicateApply._duplicate_groups(rope_workspace),
            sources=sources,
        )
        if planned.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(planned)
        outcome, _deletions = planned.value
        if outcome.plans:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                "\n".join(plan.reason for plan in outcome.plans),
                error_code=c.Infra.ToolOutcome.ERROR.value,
            )
        return FlextInfraTransformersSemanticPublication.edit_file_plans(
            root, outcome.edits, owner=FlextInfraCodemodLoopPhaseDuplicateApply.name
        )

    @staticmethod
    def _duplicate_groups(
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> t.VariadicTuple[m.Infra.DuplicateGroup]:
        """Rebuild the workspace duplicate groups from the Rope inventory.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.DuplicateGroup]``.

        """
        project_objects: dict[str, list[m.Infra.Object]] = {}
        for module in rope_workspace.modules():
            if not FlextInfraRefactorCensusCollectHelpers.production_module(
                module,
            ):
                continue
            convention = rope_workspace.convention(module.file_path)
            project = FlextInfraRefactorCensusCollectHelpers.project_name_for_module(
                module,
                convention,
            )
            if not project:
                continue
            project_objects.setdefault(project, []).extend(
                rope_workspace.objects(
                    module.file_path,
                    include_local_scopes=False,
                    include_references=False,
                ),
            )
        return FlextInfraRefactorCensusFilters.duplicate_groups(
            tuple(project_objects.values()),
        )


__all__: list[str] = ["FlextInfraCodemodLoopPhaseDuplicateApply"]
