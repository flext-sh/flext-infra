"""The workspace CI template projection carries no stray blank lines.

Premise (flext-axg1k): the steps loop of ``ci-template/ci.yml.j2`` rendered a
double blank line after the checkout step and a blank line at EOF, so a
workspace consumer's own pre-commit whitespace check rejected its ``make gen``
output with "new blank line at EOF" and the consumer could not commit it.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodegenCiTemplateProjection:
    """The rendered workspace CI template is whitespace-clean."""

    template = (
        Path(__file__).resolve().parents[3]
        / "src/flext_infra/templates/project/base/.github/ci-template/ci.yml.j2"
    )

    @classmethod
    def _render(cls) -> str:
        spec = u.CodegenTestSupport.Ci.workflow_spec(
            dist="example-workspace",
            make_profile=c.Infra.MakeProfile.WORKSPACE,
            repository_branch="develop",
            ci_trigger_branches=("develop",),
        )
        return tm.ok(u.Cli.template_render(cls.template, spec))

    def test_projection_ends_with_exactly_one_newline(self) -> None:
        """The last step is the last line: no blank line follows it at EOF."""
        rendered = self._render()

        tm.that(rendered.endswith("\n"), eq=True)
        tm.that(rendered.endswith("\n\n"), eq=False)

    def test_steps_are_separated_by_single_blank_lines(self) -> None:
        """Every step, the checkout included, is set apart by one blank line."""
        rendered = self._render()

        tm.that(rendered, lacks="\n\n\n")
        tm.that(rendered, has="          fetch-depth: 0\n\n      - name: ")
