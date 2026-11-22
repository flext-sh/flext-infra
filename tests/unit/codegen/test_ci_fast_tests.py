"""Verify the generated CI approves setup, the primary check and the fast tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, tm, u


class TestsFlextInfraCiFastTests:
    """Keep the fast tests as one CI approval row, ordered after the check."""

    ci_template = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows/ci.yml.j2"
    )

    def test_ci_approves_setup_check_and_tests_in_order(self) -> None:
        """Operator decision 2026-11-22: CI always runs the fast tests."""
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="flext-demo",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="0.12.0-dev",
            ci_trigger_branches=tuple(
                config.Infra.codegen.branch_policy.ci_trigger_branches
            ),
        )
        rendered = tm.ok(u.Cli.template_render(self.ci_template, spec))
        setup = rendered.find("make setup (blocking)")
        check = rendered.find("make check CHECK_PHASE=primary (blocking)")
        tests = rendered.find("make tests (blocking)")
        tm.that(setup, ne=-1)
        tm.that(check > setup, truth=True)
        tm.that(tests > check, truth=True)
        tm.that(rendered, lacks="make tests-full")
