"""A project extends its generated CI through its own custom-steps file.

The generator injects the declared block verbatim and never interprets it, so a
project adds a step its pipeline needs — a credential, a service, a probe —
without the generator carrying that project's concerns. This is the CI
counterpart of ``custom.mk``.

Premise (regression of 39982c92ef): the renderer kept reading the block into
``custom_steps`` while the merge dropped its injection from ``ci.yml.j2``, so
cosmos-charts lost its declared GitOps checkout and its CI tests failed with
"no GitOps values directory declared". The contract is therefore asserted on
the rendered workflow, never on the render model.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import c
from tests import tm, u


class TestsFlextInfraCodegenCiCustomSteps:
    """The declared contract of the project-owned CI extension point."""

    ci_template = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/workflows/ci.yml.j2"
    )
    block = "      - name: Declared project step\n        run: echo declared"

    @classmethod
    def _render_ci(cls, *, custom_steps: str) -> str:
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="fixture-project",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="develop",
            ci_trigger_branches=u.CodegenTestSupport.Ci.ci_trigger_branches(
                "develop",
            ),
            overrides=u.CodegenTestSupport.Ci.WorkflowRenderOverrides(
                custom_steps=custom_steps,
            ),
        )
        return tm.ok(u.Cli.template_render(cls.ci_template, spec))

    def test_declared_steps_reach_every_installing_job_before_setup(self) -> None:
        """The block lands verbatim in the ci and release-plan jobs, pre-install."""
        rendered = self._render_ci(custom_steps=self.block)

        tm.that(rendered.count(self.block), eq=2)
        jobs = rendered.split("\n  release-plan:\n")
        tm.that(jobs, len=2)
        for job in jobs:
            tm.that(job, has=self.block)
            # Before the toolchain installer, so a declared credential or
            # input is present when setup and every gate run.
            tm.that(
                job.index(self.block) < job.index("name: Install the mise release"),
                eq=True,
            )

    def test_a_project_declaring_nothing_changes_nothing(self) -> None:
        """Without a custom-steps file the workflow carries no project block."""
        rendered = self._render_ci(custom_steps="")

        tm.that(rendered, lacks="Project-owned steps")

    @staticmethod
    def test_the_extension_file_sits_beside_the_workflows() -> None:
        """GitHub parses everything inside ``workflows``; a step list is not one.

        Placing the extension there would surface as a permanent workflow syntax
        error in the repository's Actions tab.
        """
        location = Path(c.Infra.CUSTOM_CI_STEPS_FILENAME)

        tm.that(location.parts[0], eq=".github")
        tm.fail("workflows" in location.parts)
        tm.that(location.suffix, eq=".yml")
