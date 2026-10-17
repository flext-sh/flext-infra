"""Import-normalization phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.refactor import FlextInfraImportNormalization

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraImportNormalizationPhase:
    """Import-form callback: the canonical import law in the loop.

    The engine self-scans every governed source file — leaf flattening,
    lazy placement and guard cleanup are semantic judgments no ast-grep
    capture owns — so this phase does not wait for a rule finding before
    normalizing a file.
    """

    name: str = "import-normalization"

    @staticmethod
    def plan(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan target imports with all selected roots available for reads."""
        del preflight
        captured = FlextInfraCodegenPreconditions.unique_states((
            *source_states,
            *(state for plan in declared_files for state in plan.source_states),
        ))
        if captured.failure:
            return r[m.Infra.CodegenPhaseAnalysis].from_failure(captured)
        source_states = captured.value
        files: list[m.Infra.CodegenFilePlan] = []
        for project_root in u.Infra.governed_project_roots(root):
            if not u.Infra.namespace_enabled(project_root):
                continue
            selected = tuple(
                path
                for path in sources
                if path.is_relative_to(project_root)
                and path.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                and (u.Infra.project_root(path) or project_root) == project_root
            )
            planned = FlextInfraImportNormalization.plan_files(
                project_root,
                selected,
                sources=sources,
                source_states=source_states,
                rope_project=rope_workspace.rope_project,
                declared_files=declared_files,
            )
            if planned.failure:
                return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
            files.extend(planned.value.files)
        return r[m.Infra.CodegenPhaseAnalysis].ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                files=tuple(files),
                inputs=source_states,
            )
        )

    @staticmethod
    def apply(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Normalize every governed project's source imports.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        inventory = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(
                project_roots=tuple(u.Infra.governed_project_roots(root)),
            )
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        states = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in inventory.value
        )
        planned = FlextInfraImportNormalizationPhase.plan(
            root,
            preflight,
            rope_workspace,
            sources={
                state.path: state.content.decode(c.DEFAULT_ENCODING)
                for state in states
                if state.content is not None
            },
            source_states=states,
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        return FlextInfraImportNormalization.publish_plan(root, planned.value)


__all__: list[str] = ["FlextInfraImportNormalizationPhase"]
