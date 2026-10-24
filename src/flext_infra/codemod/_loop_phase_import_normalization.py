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
        sources = cls._project_sources((project_root,)).unwrap()
        with u.Infra.open_project(project_root) as project:
            planned = FlextInfraImportNormalization.plan_files(
                project_root, files, sources=sources, rope_project=project
            ).unwrap()
        return cls._publish(project_root, planned).unwrap()

    @staticmethod
    def _project_sources(
        project_roots: t.VariadicTuple[Path],
    ) -> p.Result[t.MappingKV[Path, str]]:
        """Read every governed Python source of the given projects once.

        Returns:
            The decoded sources, or the inventory failure.

        """
        return u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(project_roots=project_roots)
        ).map(
            lambda paths: {
                path: path.read_text(encoding=c.DEFAULT_ENCODING) for path in paths
            }
        )

    @staticmethod
    def _publish(
        project_root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[bool]:
        """Publish the planned batch with its lazy-init projections.

        Returns:
            Whether any file was published, or the first publication failure.

        """
        if not planned:
            return r[bool].ok(value=False)
        return FlextInfraSemanticPublication.publish_semantic_artifact_plans(
            planned,
            repository_root=project_root,
            options=m.Infra.SemanticPublicationOptions(
                projection_roots=(project_root,)
            ),
        ).map(bool)

    @staticmethod
    def plan(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
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
            planned = FlextInfraImportNormalization.plan_files(
                project_root,
                selected,
                sources=sources,
                rope_project=rope_workspace.rope_project,
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
        sources = cls._project_sources(tuple(u.Infra.governed_project_roots(root)))
        if sources.failure:
            return r[bool].from_failure(sources)
        planned = cls.plan(root, preflight, rope_workspace, sources=sources.value)
        if planned.failure:
            return r[bool].from_failure(planned)
        return cls._publish(root, planned.value)


__all__: list[str] = ["FlextInfraImportNormalizationPhase"]
