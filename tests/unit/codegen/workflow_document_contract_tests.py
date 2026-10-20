"""Rendered GitHub workflows load through the canonical YAML boundary.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraWorkflowDocumentContract:
    """Generated workflows contain executable jobs in valid YAML documents."""

    @pytest.mark.slow
    def test_rendered_workflows_load_through_public_yaml_boundary(
        self,
        tmp_path: Path,
    ) -> None:
        """Read every rendered workflow with the same public YAML consumer."""
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

        plan = u.Tests.governed_project_plan(root)
        workflow_directory = root / ".github" / "workflows"
        workflows = tuple(
            item
            for item in plan.files
            if item.path.parent == workflow_directory
            and item.desired_content is not None
        )
        tm.that(bool(workflows), eq=True)
        for item in workflows:
            item.path.parent.mkdir(parents=True, exist_ok=True)
            item.path.write_bytes(tm.not_none(item.desired_content))
            document = u.Cli.yaml_load_mapping(item.path)
            jobs = u.Cli.JSON_MAPPING_ADAPTER.validate_python(document["jobs"])
            tm.that(bool(jobs), eq=True)
            for raw_job in jobs.values():
                job = u.Cli.JSON_MAPPING_ADAPTER.validate_python(raw_job)
                tm.that("steps" in job or "uses" in job, eq=True)
