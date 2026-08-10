"""Generated template formatter fixed-point contracts."""

from __future__ import annotations

from pathlib import Path
from typing import override

from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja2.runtime import Undefined
from jinja2.utils import select_autoescape
from flext_tests import tm

_TEMPLATES = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
)


class PartialContextUndefined(Undefined):
    @override
    def __getattr__(self, name: str) -> PartialContextUndefined:
        return self

    @override
    def __getitem__(self, name: str) -> PartialContextUndefined:
        return self


_ENVIRONMENT = Environment(
    loader=FileSystemLoader(_TEMPLATES),
    autoescape=select_autoescape(),
    undefined=PartialContextUndefined,
    keep_trailing_newline=True,
)


class TestsTemplateFormatterFixedPoint:
    def test_dependabot_render_has_one_terminal_newline(self) -> None:
        rendered = _ENVIRONMENT.get_template(".github/dependabot.yml.j2").render(
            dist="demo", workspace_repositories=()
        )

        tm.that(rendered.endswith("\n") and not rendered.endswith("\n\n"), eq=True)

    def test_makefile_empty_infra_source_root_has_no_trailing_space(self) -> None:
        rendered = _ENVIRONMENT.get_template("Makefile.j2").render(
            infra_source_root_rel="", workspace_members=(), workspace_repositories=()
        )

        tm.that(rendered, has="FLEXT_INFRA_SOURCE_ROOT_REL :=\n")

    def test_sgconfig_render_has_one_terminal_newline(self) -> None:
        rendered = _ENVIRONMENT.get_template("sgconfig.yml.j2").render(
            rule_dirs=("rules",), test_dirs=("tests",)
        )

        tm.that(rendered.endswith("\n") and not rendered.endswith("\n\n"), eq=True)


__all__: tuple[str, ...] = ()
