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

    @staticmethod
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("class_stem", "bad-name"),
            ("class_stem", "class"),
            ("namespace", "nested.namespace"),
            ("namespace", "None"),
            ("alias", "bad alias"),
            ("alias", "for"),
            ("package_name", "bad-package"),
            ("package_name", "package..child"),
            ("upstream", "package.class"),
            ("upstream", "package; side_effect()"),
        ],
    )
    def test_project_code_identity_rejects_invalid_declarations(
        field: str,
        value: str,
    ) -> None:
        """Reject invalid code at the shared declaration boundary, before planning."""
        payload = u.Tests.project_spec("identity-project").model_dump()
        payload[field] = value

        with pytest.raises(ValueError, match="project declaration requires a Python"):
            m.Infra.ProjectSpec.model_validate(payload)

    @staticmethod
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("class_stem", "ProjectClass"),
            ("namespace", "Namespace"),
            ("alias", "project_alias"),
            ("package_name", "namespace.package"),
            ("upstream", "namespace.foundation"),
            ("constant_name", "distribution-with-hyphens"),
        ],
    )
    def test_project_identity_preserves_code_names_and_distribution_values(
        field: str,
        value: str,
    ) -> None:
        """Preserve valid identities and distinguish wire values from code names."""
        payload = u.Tests.project_spec("identity-project").model_dump()
        payload[field] = value

        project = m.Infra.ProjectSpec.model_validate(payload)

        tm.that(project.model_dump()[field], eq=value)

    @staticmethod
    def test_governance_profiles_retain_their_canonical_enum_identity(
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

                    tm.ok(declaration.kind is kind)
                    tm.ok(declaration.state is state)
                    tm.ok(declaration.codegen is codegen)

    @staticmethod
    @pytest.mark.parametrize("read_only", [False, True])
    def test_own_declarations_survive_public_model_roundtrip(
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

        # A portable declaration compares through the same public JSON boundary
        # it traveled: ``Sequence[str]`` contracts read back as lists, so the
        # expected values are canonicalized identically before equality.
        tm.that(
            portable.project,
            eq=m.Infra.ProjectSpec.model_validate_json(project.model_dump_json()),
        )
        tm.that(portable.integration, eq=integration)
        tm.that(
            tuple(portable.namespace_scan_dirs),
            eq=tuple(legacy.namespace_scan_dirs),
        )
        tm.that(portable.read_only, eq=read_only)

    @staticmethod
    def test_own_policy_overlay_never_poisons_the_project_metadata(
        tmp_path: Path,
    ) -> None:
        """The overlay's project selector is admission, never delta content.

        Why (aihub-l42it.11): the matching overlay dumped its selector string
        over the delta's ``project`` key, so any manifest carrying both a
        project block and an own-policy overlay failed the migration with
        ``project: Input should be a valid dictionary``.
        """
        repository = u.Tests.repository_ref(tmp_path.name)
        project = u.Tests.project_spec(repository.distribution)
        overlay = m.Infra.RepositoryPolicyOverlaySpec(
            project=repository.distribution,
            beads_enabled=False,
            ci_enabled=True,
        )
        legacy = m.Infra.WorkspaceManifestSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=repository.name,
            repository=repository,
            project=project,
            repository_policy_overlays=(overlay,),
        )

        declaration = tm.ok(u.Infra.repository_declaration_delta(legacy))

        tm.that(
            declaration.project,
            eq=m.Infra.ProjectSpec.model_validate_json(project.model_dump_json()),
        )
        tm.fail(declaration.beads_enabled)
        tm.ok(declaration.ci_enabled)

    @staticmethod
    def test_foreign_members_do_not_change_own_declaration(
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
