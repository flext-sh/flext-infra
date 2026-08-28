"""Verify ci.yml branch-trigger generation matches the declared baseline."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u as cli_u
from flext_infra import config, m
from flext_tests import tm


_CI_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "src/flext_infra/templates/project/base/.github/workflows/ci.yml.j2"
)


def _render_ci(*, repository_branch: str) -> str:
    codegen = config.Infra.codegen
    spec = m.Infra.GithubWorkflowRenderSpec(
        dist="mcb",
        repository_branch=repository_branch,
        ci_trigger_branches=tuple(dict.fromkeys((repository_branch, "main"))),
        python_version=codegen.toolchain.python_version,
        dependency_cooldown_days=codegen.toolchain.dependency_cooldown_days,
        github_actions=codegen.github_actions,
        make=codegen.make,
        workspace_repositories=(),
        checkout_submodules=codegen.checkout_submodules,
    )
    return tm.ok(cli_u.Cli.template_render(_CI_TEMPLATE, spec))


def _trigger_section(rendered: str) -> str:
    return rendered.split('"on":', maxsplit=1)[1].split(
        "# End SECTION: triggers", maxsplit=1
    )[0]


def _branch_count(triggers: str, branch: str) -> int:
    return triggers.splitlines().count(f"      - {branch}")


def test_ci_triggers_include_declared_integration_and_main() -> None:
    integration_branch = "0.12.0-dev"

    triggers = _trigger_section(_render_ci(repository_branch=integration_branch))

    tm.that(_branch_count(triggers, integration_branch), eq=2)
    tm.that(_branch_count(triggers, "main"), eq=2)


def test_ci_triggers_deduplicate_main_integration_branch() -> None:
    triggers = _trigger_section(_render_ci(repository_branch="develop"))

    tm.that(_branch_count(triggers, "develop"), eq=2)
    tm.that(_branch_count(triggers, "main"), eq=2)


__all__: tuple[str, ...] = ()
