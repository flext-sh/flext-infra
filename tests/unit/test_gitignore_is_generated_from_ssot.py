"""Tests that this repository's ``.gitignore`` is reproducible from config.

The generator filters the shared policy by the repository profile. Workspace
roots receive the ordered whitelist while members receive only universal
ignore sections. This test follows that same typed topology instead of freezing
the workspace-root projection into every repository.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_tests import tm

from flext_infra import c, config, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import u as test_u


def _workspace_root() -> Path:
    """Return the workspace root that owns this checkout."""
    return Path(flext_infra.__file__).resolve().parents[2]


def _is_allowed_by_policy(relative_path: str) -> bool:
    """Return whether the shipped SSOT policy keeps *relative_path* trackable."""
    rendered = "\n".join(test_u.Tests.ignore_patterns_for(_workspace_root())) + "\n"
    return test_u.Tests.is_tracked_under(rendered, relative_path)


class TestsFlextInfraGitignoreIsGeneratedFromSsot:
    def test_every_managed_file_survives_the_ignore_policy(self) -> None:
        """No committed managed artifact is ignored by the shipped policy.

        Generation creates every catalog entry whose lifecycle contains
        ``generate`` and then verifies the tree through git. A whitelist that
        blocks one of those paths makes the transaction non-convergent.
        """
        committed = tuple(
            item
            for item in config.Infra.codegen.surfaces.entries
            if "generate" in item.operations
        )
        blocked = tuple(
            item.path for item in committed if not _is_allowed_by_policy(item.path)
        )

        tm.that(blocked, eq=())

    def test_declared_members_are_trackable_under_the_rendered_policy(self) -> None:
        """A member declared in the manifest is trackable in the rendered body.

        The workspace-root policy denies every top-level directory (``/*`` and
        ``/*/``), so a governed member only becomes trackable when the whitelist
        is DERIVED from the live topology. Arbitrary member paths are used —
        including a nested one, whose every ancestor must be unignored — so the
        contract holds for any manifest instead of freezing today's members.
        """
        members = ("probe-member", "nested/probe-member")
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name="probe-root",
            repository=test_u.Tests.repository_ref("probe-root"),
            members=tuple(
                test_u.Tests.repository_ref(
                    Path(item).name,
                    path=Path(item),
                    role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                )
                for item in members
            ),
        )
        rendered: str = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                config.Infra.codegen,
                profile=c.Infra.MakeProfile.WORKSPACE_ROOT,
                project_name="probe-root",
                workspace=workspace,
            )
        )

        blocked = tuple(
            member
            for member in members
            if not test_u.Tests.is_tracked_under(rendered, f"{member}/pyproject.toml")
        )

        tm.that(blocked, eq=())
