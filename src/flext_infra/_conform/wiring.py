"""Projection wiring collaborators for the public API facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, codegen, docs, gates, m, r, validate
from flext_infra._utilities import (
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesProtectedEditLinting,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraConformWiring:
    """Bind the cross-family capabilities the projection executor consumes."""

    @staticmethod
    def docs_artifact_planner(
        *,
        repository_root: Path,
        projects: Sequence[str],
        include_root: bool,
    ) -> p.Infra.DocsArtifactPlanner:
        """Build the docs planner complete conform publishes through.

        Returns:
            The resulting ``p.Infra.DocsArtifactPlanner``.

        """
        return docs.FlextInfraDocGenerator(
            repository_root=repository_root,
            selected_projects=projects,
            include_root=include_root,
        )

    @staticmethod
    def markdown_format_gate(repository_root: Path) -> p.Infra.MarkdownFormatGate:
        """Build the markdown format gate the docs formatter delegates to.

        Returns:
            The resulting ``p.Infra.MarkdownFormatGate``.

        """
        return gates.FlextInfraGatesMarkdownFormat(repository_root)

    def codegen_conform_collaborators(self) -> p.Infra.CodegenConformPorts:
        """Bind planning and guarded publication at the public composition root.

        Returns:
            The existing capabilities retained by reference for this invocation.

        """
        return m.Infra.CodegenConformPorts(
            docs_planner=self.docs_artifact_planner,
            file_publisher=FlextInfraUtilitiesProtectedEditLinting,
            source_preview=codegen.FlextInfraStagedPackage(),
            candidate_validator=self.validate_codegen_candidate,
            component_planner=self.facade_component_planner,
        )

    @staticmethod
    def facade_component_planner(
        workspace: p.Infra.RopeWorkspaceDsl,
        *,
        declared_files: tuple[p.Infra.CodegenFilePlan, ...],
        selection: tuple[Path, c.Infra.FacadeFamily | None] | None,
    ) -> p.Infra.CodegenRepositoryPlanOutcome:
        """Close facade cohorts through the session's own projection DSL.

        Returns:
            The outcome the opened Rope workspace session plans.

        """
        return workspace.facade_projection(
            declared_files=declared_files,
            selection=selection,
        )

    @staticmethod
    def validate_codegen_candidate(
        root: Path,
        candidate: Path,
        projects: tuple[Path, ...],
    ) -> p.Result[bool]:
        """Admit exact staged sources through their native runtime imports.

        Returns:
            Acceptance or the original candidate runtime failure.

        """
        workspace = codegen.FlextInfraStagedPackage.workspace_root(root)
        if workspace.failure:
            return r[bool].from_failure(workspace)
        runtime = FlextInfraUtilitiesProjectDiscovery.runtime_owner_root(root)
        if runtime.failure:
            return r[bool].from_failure(runtime)
        runtime_root = runtime.value
        if not (runtime_root / c.Infra.ENVIRONMENT_DIRECTORY).is_dir():
            # A new project owns no environment until its first `make setup`;
            # the generator's runtime carries the FLEXT libraries its
            # generated modules import, so it admits the first candidate.
            runtime_root = Path(sys.prefix).parent
        repository = candidate / root.relative_to(workspace.value)
        repositories = tuple(
            candidate / project.relative_to(workspace.value) for project in projects
        )
        imported = validate.FlextInfraValidateFreshImport(
            repository_root=repository,
            runtime_root=runtime_root,
        ).build_report(repository_roots=repositories)
        if imported.failure:
            return r[bool].from_failure(imported)
        if not imported.value.passed:
            return r[bool].fail(
                "\n".join((imported.value.summary, *imported.value.violations)),
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraConformWiring"]
