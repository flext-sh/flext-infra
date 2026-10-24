"""Behavior tests for the repository Beads identity.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import m, t, tm, u


class TestsFlextInfraRepositoryBeadsIdentity:
    """Prove the typed Beads identity of a repository and its workspace members."""

    @staticmethod
    def _beads_fixture_root(tmp_path: Path, directory: str) -> Path:
        """Initialize one governed checkout carrying the canonical Beads identity.

        Returns:
            The resulting ``Path``.

        """
        return u.Tests.WorktreeFixture.governed_workspace(
            tmp_path,
            directory,
            distribution=f"fixture-{directory}",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture-database",
                issue_prefix="fixture-prefix",
            ),
        )

    @staticmethod
    def _beads_fixture_payload() -> t.MutableMappingKV[str, t.JsonValue]:
        """Return the canonical Beads identity payload a fixture checkout declares.

        Returns:
            The canonical Beads identity payload a fixture checkout declares.

        """
        return {
            "version": 1,
            "workspace": "fixture-workspace",
            "database": "fixture-database",
            "issue_prefix": "fixture-prefix",
        }

    @staticmethod
    def test_loads_typed_beads_identity_from_the_repository_itself(
        tmp_path: Path,
    ) -> None:
        """Parse required identity and project extensions into one typed model."""
        root = tmp_path / "project"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-project",
            beads=u.Tests.BeadsIdentity(
                workspace="fixture-workspace",
                database="fixture-database",
                issue_prefix="fixture-prefix",
            ),
            custom_issue_types=("incident",),
        )

        beads = tm.ok(FlextInfraWorkspaceDetector.load_beads_spec(root))
        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(type(beads), eq=m.Infra.BeadsProjectSpec)
        tm.that(
            beads.model_dump(mode="json"),
            eq={
                "version": 1,
                "workspace": "fixture-workspace",
                "database": "fixture-database",
                "issue_prefix": "fixture-prefix",
                "ownership_command_prefix": [],
                "ownership_command_cwd": None,
                "custom_issue_types": ["incident"],
            },
        )
        tm.that(workspace.beads, eq=beads)

    @pytest.mark.parametrize(
        "missing_field",
        ["version", "workspace", "database", "issue_prefix"],
    )
    def test_beads_identity_requires_every_declared_field(
        self,
        tmp_path: Path,
        missing_field: str,
    ) -> None:
        """Reject partial identity instead of inferring a value elsewhere."""
        root = self._beads_fixture_root(tmp_path, missing_field)
        payload = self._beads_fixture_payload()
        del payload[missing_field]
        tm.ok(u.Cli.yaml_dump(root / "config" / "beads.yaml", payload))

        result = FlextInfraWorkspaceDetector.load_beads_spec(root)

        tm.fail(result, has=missing_field)

    @pytest.mark.parametrize(
        ("field", "invalid_value"),
        [
            pytest.param("version", 2, id="unknown-version"),
            pytest.param("workspace", "", id="empty-workspace"),
            pytest.param("database", ["not", "a", "scalar"], id="database-list"),
            pytest.param("issue_prefix", None, id="null-prefix"),
            pytest.param(
                "custom_issue_types",
                ["incident", "incident"],
                id="duplicate-custom-type",
            ),
        ],
    )
    def test_beads_identity_rejects_malformed_values(
        self,
        tmp_path: Path,
        field: str,
        invalid_value: t.JsonValue,
    ) -> None:
        """Fail closed on values outside the typed local contract."""
        root = self._beads_fixture_root(tmp_path, field)
        payload = self._beads_fixture_payload()
        payload["custom_issue_types"] = list[t.JsonValue]()
        payload[field] = invalid_value
        tm.ok(u.Cli.yaml_dump(root / "config" / "beads.yaml", payload))

        result = FlextInfraWorkspaceDetector.load_beads_spec(root)

        tm.fail(result, has=field)

    @staticmethod
    def test_workspace_members_inherit_a_single_ledger_identity(
        tmp_path: Path,
    ) -> None:
        """Reject member-local identities and retain exactly the root ledger."""
        root = tmp_path / "workspace"
        u.Tests.WorktreeFixture.initialize_governed_project(
            root,
            "fixture-workspace",
            beads=u.Tests.BeadsIdentity(
                workspace="root-workspace",
                database="root-database",
                issue_prefix="root-prefix",
            ),
        )
        identities = {
            "fixture-alpha": ("alpha-workspace", "alpha-database", "alpha-prefix"),
            "fixture-beta": ("beta-workspace", "beta-database", "beta-prefix"),
        }
        for project_name, identity in identities.items():
            u.Tests.WorktreeFixture.initialize_governed_project(
                root / project_name,
                project_name,
                beads=u.Tests.BeadsIdentity(
                    workspace=identity[0],
                    database=identity[1],
                    issue_prefix=identity[2],
                ),
                beads_owner=False,
            )
            u.Tests.WorktreeFixture.link_member_beads(
                root / project_name,
                root,
                workspace_name="root-workspace",
                database="root-database",
                issue_prefix="root-prefix",
            )
        u.Tests.WorktreeFixture.write_gitmodules(root, tuple(identities))

        workspace = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(
            tuple(project.path.as_posix() for project in workspace.subprojects),
            eq=tuple(identities),
        )
        tm.that(u.Tests.required_beads(workspace).workspace, eq="root-workspace")
        for project_name in identities:
            beads = tm.ok(
                FlextInfraWorkspaceDetector.load_beads_spec(root / project_name),
            )
            tm.that(beads.workspace, eq="root-workspace")
            tm.that(beads.database, eq="root-database")
            tm.that(beads.issue_prefix, eq="root-prefix")
            tm.ok((root / project_name / ".beads").is_symlink())
