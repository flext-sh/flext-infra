"""Generated template formatter fixed-point contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, config

from ... import m, t, tm, u


class TestsFlextInfraTemplateFormatterFixedPoint:
    """Verify generated template formatter fixed-point contracts."""

    _TEMPLATES = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "flext_infra"
        / "templates"
        / "project"
        / "base"
    )

    @staticmethod
    def _render_spec(
        *,
        workspace_repositories: t.VariadicTuple[m.Infra.RepositoryRef] = (),
        has_devcontainer: bool = False,
    ) -> m.Infra.GithubWorkflowRenderSpec:
        """Build the common strictly typed workflow rendering contract.

        Only the two fields under test vary across the assertions; every
        other field is sourced from the canonical config the production
        renderer reads, so the context matches the SSOT the renderer uses
        instead of freezing today's values.
        """
        codegen = config.Infra.codegen
        return m.Infra.GithubWorkflowRenderSpec(
            dist="demo",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            gascity_enabled=True,
            repository_branch="develop",
            ci_trigger_branches=("develop", "main"),
            python_version=codegen.toolchain.python_version,
            state_directory_name=codegen.toolchain.state_directory_name,
            github_actions=codegen.github_actions,
            make=codegen.make,
            workspace_repositories=workspace_repositories,
            has_devcontainer=has_devcontainer,
            checkout_submodules=codegen.checkout_submodules,
        )

    def test_standalone_pyproject_template_does_not_declare_empty_workspace(
        self,
    ) -> None:
        """Keep standalone projects eligible for a real parent uv workspace."""
        template = (self._TEMPLATES / "pyproject.toml.j2").read_text(encoding="utf-8")

        tm.that(template, lacks="[tool.uv.workspace]")

    def test_dependabot_render_has_one_terminal_newline(self) -> None:
        empty = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2", self._render_spec()
            )
        )
        repository = u.Tests.repository_ref("member", path=Path("member"))
        populated = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._render_spec(workspace_repositories=(repository,)),
            )
        )

        for rendered in (empty, populated):
            tm.that(rendered.endswith("\n") and not rendered.endswith("\n\n"), eq=True)

    def test_dependabot_projects_devcontainers_only_when_one_exists(self) -> None:
        without = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._render_spec(has_devcontainer=False),
            )
        )
        with_devcontainer = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._render_spec(has_devcontainer=True),
            )
        )

        tm.that(without, lacks="devcontainers")
        tm.that(with_devcontainer, has="package-ecosystem: devcontainers")
        for rendered in (without, with_devcontainer):
            tm.that(rendered, has="package-ecosystem: pip")


__all__: list[str] = ["TestsFlextInfraTemplateFormatterFixedPoint"]
