"""Rendered GitHub workflows load through the canonical YAML boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import codegen, config, m, main
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraWorkflowDocumentContract:
    """Generated workflows contain executable jobs in valid YAML documents."""

    @staticmethod
    @pytest.mark.slow
    def test_generated_workflows_publish_the_complete_declared_surface(
        tmp_path: Path,
    ) -> None:
        """Public generation stages every declared workflow, then converges."""
        root = tmp_path / "project"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="project_database",
                issue_prefix="project-prefix",
            ),
        )

        surface = c.Infra.CodegenConformSurface.WORKFLOWS
        contract = codegen.FlextInfraCodegenConform.surface_contract(
            surface,
            codegen=config.Infra.codegen,
        )
        expected = {root / path for path in tm.not_none(contract.destinations)}
        workflow_root = root / c.Infra.GITHUB_WORKFLOWS_RELATIVE_PATH
        tm.that(expected, empty=False)
        arguments = [
            "codegen",
            "generate",
            "--root",
            str(root),
            "--what",
            surface.value,
            "--scope",
            c.Infra.CodegenConformScope.ALL.value,
        ]
        tm.that(main(arguments), eq=0)
        request = m.Infra.CodegenConformRequest(
            root=root,
            what=surface,
            scope=c.Infra.CodegenConformScope.ALL,
        )
        receipt = tm.ok(
            codegen.FlextInfraMiseArtifactsVerification.publication_current(request),
        )
        tm.ok(receipt.completed)
        tm.that(
            {
                path
                for path in receipt.written_files
                if path.is_relative_to(workflow_root)
            },
            eq=expected,
        )
        tm.that(
            {
                output.path
                for batch in receipt.batches
                for output in batch.outputs
                if output.path.is_relative_to(workflow_root)
            },
            eq=expected,
        )
        tm.that(receipt.pending_files, empty=True)
        for path in expected:
            tm.ok(path.is_file())
            document = u.Cli.yaml_load_mapping(path)
            jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
            tm.ok(bool(jobs))
            for raw_job in jobs.values():
                job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_job)
                tm.ok("steps" in job or "uses" in job)
        tm.that(main(arguments), eq=0)
        converged = tm.ok(
            codegen.FlextInfraMiseArtifactsVerification.publication_current(request),
        )
        tm.that(
            tuple(
                path
                for path in converged.written_files
                if path.is_relative_to(workflow_root)
            ),
            empty=True,
        )
        tm.that(
            {
                output.path
                for batch in converged.batches
                for output in batch.outputs
                if output.path.is_relative_to(workflow_root)
            },
            eq=expected,
        )
