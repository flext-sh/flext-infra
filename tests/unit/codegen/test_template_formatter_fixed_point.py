"""Generated template formatter fixed-point contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c

from ... import m, tm, u
from ._support import CodegenTestSupport


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
    def _workflow_spec(
        *,
        workspace_repositories: t.VariadicTuple[m.Infra.RepositoryRef],
        has_devcontainer: bool,
    ) -> m.Infra.GithubWorkflowRenderSpec:
        spec = CodegenTestSupport.Ci.workflow_spec(
            dist="demo",
            make_profile=c.Infra.MakeProfile.STANDALONE,
            repository_branch="develop",
            ci_trigger_branches=CodegenTestSupport.Ci.CI_TRIGGER_BASELINE_BRANCHES,
        )
        return type(spec).model_validate({
            **spec.model_dump(),
            "workspace_repositories": workspace_repositories,
            "has_devcontainer": has_devcontainer,
        })

    def test_standalone_pyproject_template_does_not_declare_empty_workspace(
        self,
    ) -> None:
        """Keep standalone projects eligible for a real parent uv workspace."""
        template = (self._TEMPLATES / "pyproject.toml.j2").read_text(encoding="utf-8")

        tm.that(template, lacks="[tool.uv.workspace]")

    def test_dependabot_render_has_one_terminal_newline(self) -> None:
        empty = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._workflow_spec(workspace_repositories=(), has_devcontainer=False),
            )
        )
        repository = u.Tests.repository_ref("member", path=Path("member"))
        populated = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._workflow_spec(
                    workspace_repositories=(repository,), has_devcontainer=False
                ),
            )
        )

        for rendered in (empty, populated):
            tm.that(rendered.endswith("\n") and not rendered.endswith("\n\n"), eq=True)

    def test_dependabot_projects_devcontainers_only_when_one_exists(self) -> None:
        without = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._workflow_spec(workspace_repositories=(), has_devcontainer=False),
            )
        )
        with_devcontainer = tm.ok(
            u.Cli.template_render(
                self._TEMPLATES / ".github/dependabot.yml.j2",
                self._workflow_spec(workspace_repositories=(), has_devcontainer=True),
            )
        )

        tm.that(without, lacks="devcontainers")
        tm.that(with_devcontainer, has="package-ecosystem: devcontainers")
        for rendered in (without, with_devcontainer):
            tm.that(rendered, has="package-ecosystem: pip")


__all__: list[str] = ["TestsFlextInfraTemplateFormatterFixedPoint"]
