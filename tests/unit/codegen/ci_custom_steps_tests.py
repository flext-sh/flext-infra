"""A project extends its generated CI through its own custom-steps file.

The generator injects the declared block verbatim and never interprets it, so a
project adds a step its pipeline needs — a credential, a service, a probe —
without the generator carrying that project's concerns. This is the CI
counterpart of ``custom.mk``.
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import c, config, m


class TestsFlextInfraCodegenCiCustomSteps:
    """The declared contract of the project-owned CI extension point."""

    @staticmethod
    def _render_spec(*, custom_steps: str) -> m.Infra.GithubWorkflowRenderSpec:
        """Build the common strictly typed workflow rendering contract.

        The render spec carries many derived SSOT fields; the two under test
        (``custom_steps`` and the extension filename) are the only ones a
        project can vary, so every other field is sourced from the canonical
        config the production renderer reads.
        """
        codegen = config.Infra.codegen
        return m.Infra.GithubWorkflowRenderSpec(
            dist="fixture-engine",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            gascity_enabled=True,
            repository_branch="develop",
            ci_trigger_branches=("develop", "main"),
            python_version=codegen.toolchain.python_version,
            state_directory_name=codegen.toolchain.state_directory_name,
            github_actions=codegen.github_actions,
            make=codegen.make,
            workspace_repositories=(),
            checkout_submodules=codegen.checkout_submodules,
            custom_steps=custom_steps,
        )

    def test_a_project_declaring_nothing_changes_nothing(self) -> None:
        """The extension is absent by default, so generation is unaffected."""
        spec = self._render_spec(custom_steps="")

        tm.that(spec.custom_steps, eq="")

    def test_declared_steps_reach_the_workflow_verbatim(self) -> None:
        """The block is carried as text; the generator never parses it."""
        block = "      - name: Authenticate\n        run: echo declared"
        spec = self._render_spec(custom_steps=block)

        tm.that(spec.custom_steps, eq=block)

    def test_the_extension_file_sits_beside_the_workflows(self) -> None:
        """GitHub parses everything inside ``workflows``; a step list is not one.

        Placing the extension there would surface as a permanent workflow syntax
        error in the repository's Actions tab.
        """
        location = Path(c.Infra.CUSTOM_CI_STEPS_FILENAME)

        tm.that(location.parts[0], eq=".github")
        tm.that("workflows" in location.parts, eq=False)
        tm.that(location.suffix, eq=".yml")


__all__: list[str] = ["TestsFlextInfraCodegenCiCustomSteps"]
