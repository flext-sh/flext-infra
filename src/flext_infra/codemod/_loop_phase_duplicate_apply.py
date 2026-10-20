"""Duplicate-cure phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, u
from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.codemod.duplicate_apply import FlextInfraCodemodDuplicateApply
from flext_infra.refactor._census_collect_helpers import (
    FlextInfraRefactorCensusCollectHelpersMixin,
)
from flext_infra.refactor._census_filters import FlextInfraRefactorCensusFiltersMixin

if TYPE_CHECKING:
    from flext_infra import p, t


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
        receipt: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Preserve native duplicate effects and unresolved diagnostic plans.

        Returns:
            The preserved phase analysis, or the first planning failure.

        """
        del preflight
        source_states, declared_files = receipt.inputs, receipt.files
        captured = FlextInfraCodegenPreconditions.unique_states((
            *source_states,
            *(state for plan in declared_files for state in plan.source_states),
        ))
        if captured.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(captured)
        source_states = captured.value
        planned = FlextInfraCodemodDuplicateApply.plan_census(
            root,
            rope_workspace,
            FlextInfraDuplicateApplyPhase._duplicate_groups(rope_workspace),
            sources=sources,
            receipt=receipt.model_copy(update={"inputs": source_states}),
        )
        if planned.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
        outcome, _deletions = planned.value
        originals = {state.path: state for state in source_states}
        declarations = {plan.path: plan for plan in declared_files}
        files: list[m.Infra.CodegenFilePlan] = []
        for edit in outcome.edits:
            if edit.file_path in declarations:
                files.append(
                    declarations[edit.file_path].model_copy(
                        update={
                            "desired_content": edit.updated_source.encode(
                                c.DEFAULT_ENCODING
                            ),
                            "source_states": source_states,
                            "owner": FlextInfraDuplicateApplyPhase.name,
                        }
                    )
                )
                continue
            if edit.file_path not in originals:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"duplicate planning source lacks its original "
                    f"receipt: {edit.file_path}"
                )
            before = originals[edit.file_path]
            files.append(
                m.Infra.CodegenFilePlan(
                    project=u.Infra.project_root(edit.file_path) or root,
                    path=edit.file_path,
                    before=before,
                    desired_content=edit.updated_source.encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode,
                    source_states=source_states,
                    owner=FlextInfraDuplicateApplyPhase.name,
                )
            )
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=tuple(files),
                inputs=source_states,
                issues=tuple(
                    m.Infra.Issue(
                        file=str(plan.owner_file_path),
                        line=plan.owner_line,
                        column=0,
                        code=c.Infra.ToolOutcome.ERROR.value,
                        message=plan.reason,
                    )
                    for plan in outcome.plans
                ),
            )
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
            if not FlextInfraRefactorCensusCollectHelpersMixin.production_module(
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
