"""Topology comes from each repository, never from an internal project registry.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.workspace import FlextInfraWorkspaceDetector
from tests import c, tm, u


class TestsFlextInfraDetectorOwnsNoProjectRegistry:
    """Prove derivation never consults a flext-infra-owned project catalog."""

    @pytest.mark.parametrize(
        ("value", "managed"),
        [("yes", True), ("on", True), ("off", False), ("0", False)],
    )
    def test_management_values_follow_native_git_boolean_grammar(
        self,
        tmp_path: Path,
        value: str,
        *,
        managed: bool,
    ) -> None:
        """Git's supported boolean spellings retain their native meanings."""
        root = u.Tests.WorktreeFixture.self_named_project(
            tmp_path / "native-boolean",
            "native-boolean",
        )
        repository = u.Tests.repository_ref("member")
        tm.ok(
            u.Cli.files_write_text(
                root / c.Infra.GITMODULES,
                '[submodule "member"]\n'
                "    path = member\n"
                f"    url = {repository.url}\n"
                f"    flext-managed = {value}\n",
            ),
        )

        declarations = tm.ok(u.Infra.git_submodule_declarations(root))

        tm.that(declarations[0].managed, eq=managed)

    def test_malformed_management_flag_preserves_the_native_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Invalid management input cannot silently exclude a repository."""
        root = u.Tests.WorktreeFixture.self_named_project(
            tmp_path / "invalid-boolean",
            "invalid-boolean",
        )
        repository = u.Tests.repository_ref("member")
        tm.ok(
            u.Cli.files_write_text(
                root / c.Infra.GITMODULES,
                '[submodule "member"]\n'
                "    path = member\n"
                f"    url = {repository.url}\n"
                "    flext-managed = invalid-boolean\n",
            ),
        )

        declarations = u.Infra.git_submodule_declarations(root)

        tm.that(declarations.failure, eq=True)
        tm.that(declarations.exception is not None, eq=True)

    def test_changed_git_participation_is_observed_without_a_catalog(
        self,
        tmp_path: Path,
    ) -> None:
        """A changed Git declaration updates discovery in the same process."""
        root = u.Tests.WorktreeFixture.self_named_project(
            tmp_path / "declaration-owner",
            "declaration-owner",
        )
        relative = Path("external") / "library"
        repository = u.Tests.repository_ref(relative.name)
        branch = config.Infra.codegen.branch_policy.integration_branch_preference[0]
        declaration = (
            f'[submodule "{relative.as_posix()}"]\n'
            f"    path = {relative.as_posix()}\n"
            f"    url = {repository.url}\n"
            f"    branch = {branch}\n"
            "    flext-managed = false\n"
        )
        modules = root / c.Infra.GITMODULES
        tm.ok(u.Cli.files_write_text(modules, declaration))

        excluded = u.Infra.repository_nonparticipant_paths(root)
        targets = tm.ok(
            u.Infra.repository_operation_targets(
                root,
                c.Infra.CodegenConformScope.ALL,
            ),
        )

        tm.that(excluded, eq=frozenset({relative.as_posix()}))
        tm.that(tuple(target.root for target in targets), eq=(root, root / relative))
        tm.ok(
            u.Cli.files_write_text(
                modules,
                declaration.replace(
                    "flext-managed = false",
                    "flext-managed = true",
                ),
            ),
        )
        tm.that(u.Infra.repository_nonparticipant_paths(root), empty=True)

    def test_unknown_project_derives_its_own_identity(self, tmp_path: Path) -> None:
        """A repository absent from any catalog still derives from itself."""
        root = u.Tests.WorktreeFixture.self_named_project(
            tmp_path / "totally-unknown-project",
            "totally-unknown",
        )

        spec = tm.ok(FlextInfraWorkspaceDetector.load_workspace_spec(root))

        tm.that(spec.repository.name, eq="totally-unknown")
        # The workspace identity is the repository's own declared beads
        # projection, never a flext-infra catalog entry.
        tm.that(spec.name, eq=u.Tests.required_beads(spec).workspace)
        tm.that(spec.repository.path, eq=Path())
        tm.that(spec.subprojects, empty=True)
        tm.that(u.Tests.required_beads(spec).workspace, eq="totally-unknown-workspace")
