"""Projection wiring collaborators for the public API facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, codegen, docs, gates, m, r, u, validate
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
        """Admit exact staged sources through native runtime and type contracts.

        Returns:
            Acceptance or the original candidate runtime or typing failure.

        """
        workspace = codegen.FlextInfraStagedPackage.workspace_root(root)
        if workspace.failure:
            return r[bool].from_failure(workspace)
        runtime = FlextInfraUtilitiesProjectDiscovery.runtime_owner_root(root)
        if runtime.failure:
            return r[bool].from_failure(runtime)
        repository = candidate / root.relative_to(workspace.value)
        repositories = tuple(
            candidate / project.relative_to(workspace.value) for project in projects
        )
        imported = validate.FlextInfraValidateFreshImport(
            repository_root=repository,
            runtime_root=runtime.value,
        ).build_report(repository_roots=repositories)
        if imported.failure:
            return r[bool].from_failure(imported)
        if not imported.value.passed:
            return r[bool].fail(
                "\n".join((imported.value.summary, *imported.value.violations)),
            )
        return FlextInfraConformWiring._validate_model_conformance(
            candidate,
            repositories,
            runtime.value,
        )

    @staticmethod
    def _validate_model_conformance(
        candidate: Path,
        repositories: tuple[Path, ...],
        runtime: Path,
    ) -> p.Result[bool]:
        """Check model-declaring packages once using only staged import roots.

        Returns:
            Acceptance or a missing witness or native typing failure.

        """
        layouts: list[p.Infra.RopeProjectLayout] = []
        witnesses: list[Path] = []
        for repository in repositories:
            layout = u.Infra.layout(repository)
            if layout is None:
                return r[bool].fail(
                    f"model conformance has no Python layout: {repository}"
                )
            layouts.append(layout)
            models = layout.package_dir / "_models"
            witness = (
                layout.package_dir
                / "_protocols"
                / c.Infra.MODEL_PROTOCOL_CONFORMANCE_FILENAME
            )
            if models.is_dir():
                if not witness.is_file():
                    return r[bool].fail(
                        f"model conformance witness is missing: {witness}"
                    )
                witnesses.append(witness)
        if not witnesses:
            return r[bool].ok(value=True)
        reports = u.Cli.ensure_dir(candidate / c.Infra.REPORTS_DIR_NAME)
        if reports.failure:
            return r[bool].from_failure(reports)
        context = m.Infra.GateContext(
            repository_root=candidate,
            runtime_root=runtime,
            reports_dir=reports.value,
            selected_files=tuple(witnesses),
        )
        checked = gates.FlextInfraGatesPyrefly(
            candidate,
            source_roots=tuple(layout.src_dir for layout in layouts),
        ).check_files(witnesses, candidate, context)
        if not checked.result.passed:
            return r[bool].fail(
                f"model/protocol conformance failed:\n{checked.raw_output}"
            )
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraConformWiring"]
