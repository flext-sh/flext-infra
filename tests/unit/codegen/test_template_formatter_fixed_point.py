"""Generated template formatter fixed-point contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import m, u
from flext_tests import tm

_TEMPLATES = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
)


class TestsTemplateFormatterFixedPoint:
    def test_standalone_pyproject_template_does_not_declare_empty_workspace(
        self,
    ) -> None:
        """Keep standalone projects eligible for a real parent uv workspace."""
        template = (_TEMPLATES / "pyproject.toml.j2").read_text(encoding="utf-8")

        tm.that(template, lacks="[tool.uv.workspace]")

    def test_dependabot_render_has_one_terminal_newline(self) -> None:
        empty = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / ".github/dependabot.yml.j2",
                m.Infra.GithubWorkflowRenderSpec.model_construct(
                    dist="demo",
                    workspace_repositories=(),
                ),
            )
        )
        repository = m.Infra.RepositoryRef.model_construct(
            package=True, path=Path("member")
        )
        populated = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / ".github/dependabot.yml.j2",
                m.Infra.GithubWorkflowRenderSpec.model_construct(
                    dist="demo",
                    workspace_repositories=(repository,),
                ),
            )
        )

        for rendered in (empty, populated):
            tm.that(rendered.endswith("\n") and not rendered.endswith("\n\n"), eq=True)

    def test_dependabot_projects_devcontainers_only_when_one_exists(self) -> None:
        without = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / ".github/dependabot.yml.j2",
                m.Infra.GithubWorkflowRenderSpec.model_construct(
                    dist="demo",
                    workspace_repositories=(),
                    has_devcontainer=False,
                ),
            )
        )
        with_devcontainer = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / ".github/dependabot.yml.j2",
                m.Infra.GithubWorkflowRenderSpec.model_construct(
                    dist="demo",
                    workspace_repositories=(),
                    has_devcontainer=True,
                ),
            )
        )

        tm.that(without, lacks="devcontainers")
        tm.that(with_devcontainer, has="package-ecosystem: devcontainers")
        for rendered in (without, with_devcontainer):
            tm.that(rendered, has="package-ecosystem: pip")


__all__: tuple[str, ...] = ()
