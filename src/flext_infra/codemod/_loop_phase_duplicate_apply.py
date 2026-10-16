"""Duplicate-cure phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import r
from flext_infra.codemod.duplicate_apply import FlextInfraCodemodDuplicateApply
from flext_infra.refactor._census_collect_helpers import (
    FlextInfraRefactorCensusCollectHelpersMixin,
)
from flext_infra.refactor._census_filters import FlextInfraRefactorCensusFiltersMixin

if TYPE_CHECKING:
    from flext_infra import m, p, t


class FlextInfraDuplicateApplyPhase:
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
        groups = FlextInfraDuplicateApplyPhase._duplicate_groups(rope_workspace)
        if not groups:
            return r[bool].ok(value=False)
        outcome = FlextInfraCodemodDuplicateApply.census_duplicates(
            root,
            rope_workspace,
            groups,
            apply=True,
        )
        if outcome.failure:
            return r[bool].from_failure(outcome)
        return r[bool].ok(value=bool(outcome.value.edits))

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
            if not FlextInfraRefactorCensusCollectHelpersMixin.is_production_module(
                module,
            ):
                continue
            convention = rope_workspace.convention(module.file_path)
            project = (
                FlextInfraRefactorCensusCollectHelpersMixin.project_name_for_module(
                    module,
                    convention,
                )
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
        return FlextInfraRefactorCensusFiltersMixin.duplicate_groups(
            tuple(project_objects.values()),
        )


__all__: list[str] = ["FlextInfraDuplicateApplyPhase"]
