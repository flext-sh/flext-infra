"""Public repository declaration migration contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraRepositoryDeclarationDelta:
    """Preserve own declarations without projecting another repository's facts."""

    def test_governance_profiles_retain_their_canonical_enum_identity(
        self,
        tmp_path: Path,
    ) -> None:
        """Migration preserves every supported architecture and lifecycle boundary."""
        repository = u.Tests.repository_ref(tmp_path.name)
        for kind in c.Infra.ProjectKind:
            for state in c.Infra.RepositoryState:
                for codegen in c.Infra.CodegenKind:
                    legacy = m.Infra.WorkspaceManifestSpec(
                        version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                        name=repository.name,
                        repository=repository.model_copy(
                            update={"kind": kind, "state": state, "codegen": codegen},
                        ),
                    )

                    declaration = tm.ok(u.Infra.repository_declaration_delta(legacy))

                    tm.that(declaration.kind is kind, eq=True)
                    tm.that(declaration.state is state, eq=True)
                    tm.that(declaration.codegen is codegen, eq=True)

    @pytest.mark.parametrize("read_only", [False, True])
    def test_own_declarations_survive_public_model_roundtrip(
        self,
        tmp_path: Path,
        *,
        read_only: bool,
    ) -> None:
        """A portable declaration retains the input owner's own policy."""
        repository = u.Tests.repository_ref(tmp_path.name).model_copy(
            update={"read_only": read_only},
        )
        project = u.Tests.project_spec(repository.distribution)
        integration = m.Infra.WorkspaceIntegrationSpec(
            provider=repository.provider,
            branch=config.Infra.codegen.branch_policy.integration_branch,
        )
        legacy = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            project=project,
            integration=integration,
            namespace_scan_dirs=config.Infra.source_scan.roots,
        )

        declaration = tm.ok(u.Infra.repository_declaration_delta(legacy))
        portable = m.Infra.RepositoryDeltaSpec.model_validate_json(
            declaration.model_dump_json(),
        )

        tm.that(portable.project, eq=project)
        tm.that(portable.integration, eq=integration)
        tm.that(portable.namespace_scan_dirs, eq=legacy.namespace_scan_dirs)
        tm.that(portable.read_only, eq=read_only)

    def test_foreign_members_do_not_change_own_declaration(
        self,
        tmp_path: Path,
    ) -> None:
        """Changing composition does not change a repository's own configuration."""
        repository = u.Tests.repository_ref(tmp_path.name)
        legacy = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            project=u.Tests.project_spec(repository.distribution),
        )
        member = u.Tests.repository_ref(f"{tmp_path.name}-member").model_copy(
            update={"path": Path("member")},
        )

        before = tm.ok(u.Infra.repository_declaration_delta(legacy))
        after = tm.ok(
            u.Infra.repository_declaration_delta(
                legacy.model_copy(update={"members": (member,)}),
            ),
        )

        tm.that(after, eq=before)
