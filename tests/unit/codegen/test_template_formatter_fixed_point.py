"""Generated template formatter fixed-point contracts."""

from __future__ import annotations

from pathlib import Path

from flext_infra import config, m, u
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
    def test_dependabot_render_has_one_terminal_newline(self) -> None:
        empty = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / ".github/dependabot.yml.j2",
                m.Infra.GithubWorkflowRenderSpec.model_construct(
                    dist="demo",
                    workspace_repositories=(),
                    dependency_cooldown_days=(
                        config.Infra.codegen.toolchain.dependency_cooldown_days
                    ),
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
                    dependency_cooldown_days=(
                        config.Infra.codegen.toolchain.dependency_cooldown_days
                    ),
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
                    dependency_cooldown_days=(
                        config.Infra.codegen.toolchain.dependency_cooldown_days
                    ),
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
                    dependency_cooldown_days=(
                        config.Infra.codegen.toolchain.dependency_cooldown_days
                    ),
                ),
            )
        )

        tm.that(without, lacks="devcontainers")
        tm.that(with_devcontainer, has="package-ecosystem: devcontainers")
        for rendered in (without, with_devcontainer):
            tm.that(rendered, has="package-ecosystem: pip")

    def test_sgconfig_render_has_one_terminal_newline(self) -> None:
        populated = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / "sgconfig.yml.j2",
                m.Infra.SgconfigRenderSpec(rule_dirs=("rules",), test_dirs=("tests",)),
            )
        )
        empty = tm.ok(
            u.Cli.template_render(
                _TEMPLATES / "sgconfig.yml.j2",
                m.Infra.SgconfigRenderSpec(rule_dirs=("rules",), test_dirs=()),
            )
        )

        for rendered in (populated, empty):
            tm.that(rendered.endswith("\n") and not rendered.endswith("\n\n"), eq=True)


__all__: tuple[str, ...] = ()
