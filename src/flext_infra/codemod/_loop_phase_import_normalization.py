"""Import-normalization phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.refactor import FlextInfraImportNormalization
from flext_infra.transformers import FlextInfraSemanticPublication

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

    @classmethod
    def apply_files(cls, project_root: Path, files: t.SequenceOf[Path]) -> bool:
        """Normalize every given file; return whether any source changed.

        Returns:
            Whether at least one file changed.

        """
        paths = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=(project_root,))
        ).unwrap()
        states = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in paths
        )
        sources = {
            state.path: state.content.decode(c.DEFAULT_ENCODING)
            for state in states
            if state.content is not None
        }
        with u.Infra.open_project(project_root) as project:
            planned = FlextInfraImportNormalization.plan_files(
                project_root,
                files,
                sources=sources,
                receipt=m.Infra.CodegenPhaseAnalysis(
                    phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
                    inputs=states,
                    files=(),
                ),
                rope_project=project,
            ).unwrap()
        return cls.publish_plan(project_root, planned).unwrap()

    @staticmethod
    def publish_plan(
        project_root: Path,
        planned: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[bool]:
        """Prepare the owner-filename candidate and publish the planned batch once.

        Returns:
            Whether any batch was published, or the first publication failure.

        """
        if planned.issues:
            return r[bool].fail(
                "\n".join(issue.formatted for issue in planned.issues),
                exception=planned.exception,
            )
        if not planned.files:
            return r[bool].ok(value=False)
        prepared = u.Infra.normalize_sources(
            project_root,
            {
                plan.path: plan.desired_content.decode(c.DEFAULT_ENCODING)
                for plan in planned.files
                if plan.desired_content is not None
            },
            inputs=planned.inputs,
        )
        if prepared.failure:
            return r[bool].from_failure(prepared)
        files_to_publish: list[m.Infra.CodegenFilePlan] = []
        for plan in planned.files:
            source = prepared.value.updates[plan.path]
            if source is None:
                return r[bool].fail(f"import formatter retired a source: {plan.path}")
            files_to_publish.append(
                plan.model_copy(
                    update={
                        "desired_content": source.encode(c.DEFAULT_ENCODING),
                        "source_states": prepared.value.inputs,
                    }
                )
            )
        published = FlextInfraSemanticPublication.publish_semantic_artifact_plans(
            files_to_publish,
            repository_root=project_root,
            options=m.Infra.SemanticPublicationOptions(
                projection_roots=(project_root,),
            ),
        )
        if published.failure:
            return r[bool].from_failure(published)
        return r[bool].ok(bool(published.value))

    @staticmethod
    def plan(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
        receipt: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan target imports with all selected roots available for reads.

        Returns:
            The planned phase analysis, or the first planning failure.

        """
        del preflight
        source_states, declared_files = receipt.inputs, receipt.files
        captured = u.Infra.unique_states((
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
                receipt=receipt.model_copy(update={"inputs": source_states}),
                rope_project=rope_workspace.rope_project,
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
            receipt=m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.SEMANTIC, files=(), inputs=states
            ),
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        return FlextInfraImportNormalizationPhase.publish_plan(root, planned.value)


__all__: list[str] = ["FlextInfraImportNormalizationPhase"]
