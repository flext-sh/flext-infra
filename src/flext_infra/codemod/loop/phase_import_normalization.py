"""Import-normalization phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from flext_infra import c, m, p, r, u
from flext_infra.codegen import FlextInfraCodegenLazyInit
from flext_infra.transformers._semantic import FlextInfraTransformersSemanticPublication


class FlextInfraCodemodLoopPhaseImportNormalization:
    """Import-form callback: the canonical import law in the loop.

    A full run scans every governed source. A selected syntax run binds its
    changed files against the same complete source view; unrelated modules
    remain the responsibility of their selected rule or the full run.
    """

    name: str = "import-normalization"

    def __init__(self, *, paths: Sequence[Path] | None = None) -> None:
        """Bind the planned write cohort; None selects the complete inventory."""
        self.paths = None if paths is None else frozenset(paths)

    @classmethod
    def apply_files(cls, project_root: Path, files: Sequence[Path]) -> bool:
        """Normalize every given file; return whether any source changed.

        Returns:
            Whether at least one file changed.

        """
        with u.Infra.workspace_snapshot(project_root, (project_root,)) as snapshot:
            sources = {
                path: captured.text
                for path, captured in u.Infra.workspace_sources(snapshot).items()
            }
            planned = u.Infra.plan_import_normalization(
                project_root,
                files,
                sources=sources,
                declared_files=cls._planned_initializers(
                    project_root, snapshot
                ).unwrap(),
                snapshot=snapshot,
            ).unwrap()
        return cls._publish(project_root, planned).unwrap()

    @staticmethod
    def _planned_initializers(
        project_root: Path, snapshot: p.Infra.WorkspaceSnapshot
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan the lazy initializers this candidate publishes with its rewrites.

        Consumer routes are decided against the initializers the publication
        joins into the same candidate, so an import of a name a planned
        initializer no longer publishes moves to its owner in this batch.

        Returns:
            The planned initializer cohort, or the first planning failure.

        """
        return FlextInfraCodegenLazyInit.plan_candidate(
            project_root, declared_files=(), snapshot=snapshot
        )

    @staticmethod
    def _publish(
        project_root: Path,
        planned: Sequence[p.Infra.CodegenFilePlan],
    ) -> p.Result[bool]:
        """Publish the planned batch with its lazy-init projections.

        Returns:
            Whether any file was published, or the first publication failure.

        """
        if not planned:
            return r[bool].ok(value=False)
        return (
            FlextInfraTransformersSemanticPublication.publish_semantic_artifact_plans(
                planned,
                repository_root=project_root,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(project_root,)
                ),
            ).map(bool)
        )

    def plan(
        self,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.CodegenFilePlan, ...]]:
        """Plan target imports with all selected roots available for reads.

        Returns:
            The planned file plans, or the first planning failure.

        """
        del preflight
        files: list[p.Infra.CodegenFilePlan] = []
        for project_root in u.Infra.governed_project_roots(root):
            if not u.Infra.namespace_enabled(project_root):
                continue
            selected = tuple(
                path
                for path in sources
                if self.paths is None or path in self.paths
                if path.is_relative_to(project_root)
                and path.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                and (u.Infra.project_root(path) or project_root) == project_root
            )
            if not selected:
                continue
            with u.Infra.workspace_snapshot(
                project_root, (project_root,)
            ) as project_snapshot:
                initializers = self._planned_initializers(
                    project_root, project_snapshot
                )
            if initializers.failure:
                return initializers
            planned = u.Infra.plan_import_normalization(
                project_root,
                selected,
                sources=sources,
                declared_files=initializers.value,
                snapshot=rope_workspace.snapshot,
            )
            if planned.failure:
                return planned
            files.extend(planned.value)
        return r[tuple[p.Infra.CodegenFilePlan, ...]].ok(tuple(files))

    @classmethod
    def apply(
        cls,
        root: Path,
        preflight: p.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Normalize every governed project's source imports.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        sources = {
            path: captured.text
            for path, captured in u.Infra.workspace_sources(
                rope_workspace.snapshot
            ).items()
        }
        planned = cls().plan(root, preflight, rope_workspace, sources=sources)
        if planned.failure:
            return r[bool].from_failure(planned)
        return cls._publish(root, planned.value)


__all__: list[str] = ["FlextInfraCodemodLoopPhaseImportNormalization"]
