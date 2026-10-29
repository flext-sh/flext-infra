"""Import-normalization phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, u
from flext_infra.transformers import FlextInfraTransformersSemanticPublication

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodemodLoopPhaseImportNormalization:
    """Import-form callback: the canonical import law in the loop.

    The engine self-scans every governed source file — leaf flattening,
    lazy placement and guard cleanup are semantic judgments no ast-grep
    capture owns — so this phase does not wait for a rule finding before
    normalizing a file.
    """

    name: str = "import-normalization"

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
                declared_files=(),
                snapshot=snapshot,
            ).unwrap()
        return cls._publish(project_root, planned).unwrap()

    @staticmethod
    def _publish(
        project_root: Path,
        planned: Sequence[m.Infra.CodegenFilePlan],
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

    @staticmethod
    def plan(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Plan target imports with all selected roots available for reads.

        Returns:
            The planned file plans, or the first planning failure.

        """
        del preflight
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
            planned = u.Infra.plan_import_normalization(
                project_root,
                selected,
                sources=sources,
                declared_files=(),
                snapshot=rope_workspace.snapshot,
            )
            if planned.failure:
                return planned
            files.extend(planned.value)
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(tuple(files))

    @classmethod
    def apply(
        cls,
        root: Path,
        preflight: m.Infra.ModScanReport,
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
        planned = cls.plan(root, preflight, rope_workspace, sources=sources)
        if planned.failure:
            return r[bool].from_failure(planned)
        return cls._publish(root, planned.value)


__all__: list[str] = ["FlextInfraCodemodLoopPhaseImportNormalization"]
