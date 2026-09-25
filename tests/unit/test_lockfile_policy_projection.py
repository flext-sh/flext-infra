"""Validate lockfile ignore behavior against the configured generation policy."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import c, config
from flext_infra.codegen.conform import FlextInfraCodegenConform
from tests import u


class TestsFlextInfraLockfilePolicyProjection:
    """The generated ignore file preserves the policy declared for each profile."""

    @pytest.mark.parametrize("profile", tuple(c.Infra.MakeProfile))
    def test_lockfile_tracking_matches_configured_policy(
        self, profile: c.Infra.MakeProfile
    ) -> None:
        """Use Git to compare configured rules with the rendered artifact."""
        codegen = config.Infra.codegen
        declared = "\n".join(
            pattern
            for section in codegen.gitignore_sections
            if not section.profiles or profile in section.profiles
            for pattern in section.patterns
        )
        rendered = tm.ok(
            FlextInfraCodegenConform.render_project_gitignore(
                codegen, profile=profile, project_name="fixture-project"
            )
        )

        tm.that(
            u.Tests.is_tracked_under(rendered, c.Infra.UV_LOCK_FILENAME),
            eq=u.Tests.is_tracked_under(declared, c.Infra.UV_LOCK_FILENAME),
        )
