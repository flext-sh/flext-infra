"""Projection wiring collaborators for the public API facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import codegen, docs, gates, m, r, t, u, validate
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
        projects: t.StrSequence,
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
        return gates.FlextInfraMarkdownFormatGate(repository_root)

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
            imports_planner=u.Infra.plan_import_normalization,
            component_planner=u.Infra.plan_component_facades,
        )

    @staticmethod
    def validate_codegen_candidate(
        root: Path,
        candidate: Path,
        projects: tuple[Path, ...],
    ) -> p.Result[bool]:
        """Admit the complete candidate through the existing fresh-import owner.

        The source repository elects its physical runtime. Only the candidate's
        sources of every owning project are probed; a successful import of the
        live package cannot admit a half-published facade and initializer cohort.

        Returns:
            Acceptance, or the original native runtime or import failure.

        """
        workspace = codegen.FlextInfraStagedPackage.workspace_root(root)
        if workspace.failure:
            return r[bool].from_failure(workspace)
        repository = candidate / root.relative_to(workspace.value)
        repositories = tuple(
            candidate / project.relative_to(workspace.value) for project in projects
        )
        return (
            FlextInfraUtilitiesProjectDiscovery
            .runtime_owner_root(root)
            .flat_map(
                lambda runtime: validate.FlextInfraValidateFreshImport(
                    repository_root=repository,
                    runtime_root=runtime,
                ).build_report(repository_roots=repositories)
            )
            .flat_map(
                lambda report: (
                    r[bool].ok(value=True)
                    if report.passed
                    else r[bool].fail("\n".join((report.summary, *report.violations)))
                )
            )
        )


__all__: list[str] = ["FlextInfraConformWiring"]
