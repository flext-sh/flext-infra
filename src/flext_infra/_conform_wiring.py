"""Projection wiring collaborators for the public API facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import m, r, t, u

from flext_infra.docs import FlextInfraDocGenerator
from flext_infra.gates import FlextInfraMarkdownFormatGate

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraConformWiring:
    """Bind the cross-family capabilities the projection executor consumes."""

    @staticmethod
    def generation_participant_policy(
        root: Path,
        *,
        initial_workspace: p.Infra.WorkspaceSpec | None,
    ) -> p.Result[p.Infra.CodegenParticipantPolicy]:
        """Authorize the actual physical coordination root and declared members.

        Returns:
            The resulting ``p.Result[p.Infra.CodegenParticipantPolicy]``.

        """
        return FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=root),
        ).participant_policy(initial_workspace=initial_workspace)

    @staticmethod
    def codegen_footprint(
        request: m.Infra.CodegenFootprintRequest,
    ) -> p.Result[str]:
        """Report original authority, then authorize a fresh footprint without copies.

        Returns:
            The resulting ``p.Result[str]``.

        """
        transaction = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
        )
        observed = transaction.inspect_journal()
        if observed.failure:
            return r[str].from_failure(observed)
        # Preserve recorded authority even if topology or authorization fails.
        u.Cli.info(observed.value.model_dump_json())
        policy = transaction.participant_policy()
        if policy.failure:
            return r[str].from_failure(policy)
        bounded = FlextInfraCodegenTransaction(
            FlextInfraCodegenMiseArtifacts(repository_root=request.root),
            participant_policy=policy.value,
        )
        authorized = bounded.validate_footprint(observed.value)
        if authorized.failure:
            return r[str].from_failure(authorized)
        return r[str].ok(authorized.value.model_dump_json())

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
        return FlextInfraDocGenerator(
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
        return FlextInfraMarkdownFormatGate(repository_root)

    def codegen_conform_collaborators(self) -> p.Infra.CodegenConformPorts:
        """Bind the docs family complete conform crosses into.

        Returns:
            The caller-bound docs planner and participant policy capabilities.

        """
        return m.Infra.CodegenConformPorts(
            docs_planner=self.docs_artifact_planner,
            participant_policy=self.generation_participant_policy,
        )


__all__: list[str] = ["FlextInfraConformWiring"]
