"""Accessor-rename phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod.semantic_apply import FlextInfraCodemodSemanticApply
from flext_infra.refactor import (
    FlextInfraAccessorMigrationRewriteMixin,
    FlextInfraAccessorOriginResolver,
)


class FlextInfraAccessorRenamePhase(
    FlextInfraAccessorMigrationRewriteMixin,
):
    """Accessor callback: origin-owned rename catalog repairs in the loop.

    Reuses the accessor migration's origin-aware rewrite, so a homonym the
    catalog does not own is never renamed inside the loop either.
    """

    name: str = "accessor-rename"

    def __init__(self, *, source_preview: p.Infra.SourcePreview) -> None:
        """Receive the same authenticated candidate capability as the public verb."""
        self.source_preview = source_preview

    def apply(
        self,
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Apply the rename catalog over the governed files of the repository.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        states = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in FlextInfraCodemodSemanticApply.source_inventory(root, preflight)
        )
        planned = self.plan_edits(
            root,
            preflight,
            rope_workspace,
            sources={
                state.path: state.content.decode(c.DEFAULT_ENCODING)
                for state in states
                if state.content is not None
            },
            receipt=m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC, files=(), inputs=states
            ),
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        return FlextInfraCodemodSemanticApply.publish_planned_edits(
            root, planned.value, source_preview=self.source_preview
        )

    def plan_edits(
        self,
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
        receipt: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Plan origin-owned accessors on a separate immutable working view.

        Returns:
            The planned migration edits, or the first planning failure.

        """
        del preflight
        source_states, declared_files = receipt.inputs, receipt.files
        snapshot = u.Infra.snapshot_project(
            rope_workspace.rope_project,
            sources,
            captured=u.Infra.codemod_source_epoch(
                m.Infra.CodemodBindingSnapshot(
                    states=tuple(
                        state
                        for state in source_states
                        if state.path in sources
                        or state.path.suffix
                        in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                    )
                )
            ),
            declared_files=tuple(
                plan.model_copy(
                    update={
                        "desired_content": sources[plan.path].encode(
                            c.DEFAULT_ENCODING
                        ),
                    }
                )
                for plan in declared_files
                if plan.path in sources
                and (
                    isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan)
                    or plan.before.content is None
                )
            ),
        )
        resolver = FlextInfraAccessorOriginResolver(snapshot)
        edits: list[m.Infra.SemanticMigrationEdit] = []
        for py_file, source in sources.items():
            if not py_file.is_relative_to(root) or py_file.suffix not in {
                c.Infra.EXT_PYTHON,
                c.Infra.EXT_PYTHON_STUB,
            }:
                continue
            updated_source, rewrite_changes = self._apply_automated_rewrites(
                snapshot,
                py_file,
                source,
                resolver=resolver,
            )
            if not any(change.automated for change in rewrite_changes):
                continue
            edits.append(
                m.Infra.SemanticMigrationEdit(
                    file_path=py_file,
                    original_source=source,
                    updated_source=updated_source,
                    source_states=source_states,
                    changes=tuple(
                        change.reason for change in rewrite_changes if change.automated
                    ),
                ),
            )
        return r[t.VariadicTuple[m.Infra.SemanticMigrationEdit]].ok(tuple(edits))

    def plan(
        self,
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
        receipt: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Bind accessor effects to the original physical publication receipts.

        Returns:
            The bound phase analysis, or the first planning failure.

        """
        source_states, declared_files = receipt.inputs, receipt.files
        captured = u.Infra.unique_states((
            *source_states,
            *(state for plan in declared_files for state in plan.source_states),
        ))
        if captured.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(captured)
        source_states = captured.value
        planned = self.plan_edits(
            root,
            preflight,
            rope_workspace,
            sources=sources,
            receipt=receipt.model_copy(update={"inputs": source_states}),
        )
        if planned.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
        originals = {state.path: state for state in source_states}
        declarations = {plan.path: plan for plan in declared_files}
        files: list[m.Infra.CodegenFilePlan] = []
        for edit in planned.value:
            if edit.file_path in declarations:
                files.append(
                    declarations[edit.file_path].model_copy(
                        update={
                            "desired_content": edit.updated_source.encode(
                                c.DEFAULT_ENCODING
                            ),
                            "source_states": source_states,
                            "owner": self.name,
                        }
                    )
                )
                continue
            if edit.file_path not in originals:
                return r[m.Infra.CodegenPhaseAnalysis].fail(
                    f"accessor planning source lacks its original "
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
                    owner=self.name,
                )
            )
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=tuple(files),
                inputs=source_states,
            )
        )


__all__: list[str] = ["FlextInfraAccessorRenamePhase"]
