"""Contract tests for the generated submodule setup shell recipe."""

from __future__ import annotations

import pathlib
import re

from flext_tests import tm

_RECIPE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src/flext_infra/templates/project/base/submodule_setup_recipe.j2"
)


class TestsSubmoduleRecipeShell:
    """A Make recipe is one shell command joined by backslash continuations.

    A comment line inside the recipe that does not itself end with a
    backslash terminates the continuation: everything after it becomes a
    separate shell line, so the enclosing ``if``/``else`` loses its body and
    the shell aborts with "end of file unexpected (expecting fi)".
    """

    @staticmethod
    def _recipe_body() -> list[str]:
        """Return only the lines that belong to the shell recipe body."""
        text = _RECIPE.read_text(encoding="utf-8")
        body: list[str] = []
        started = False
        for line in text.splitlines():
            if re.match(r"^\s*\{%", line) or not line.strip():
                continue
            if line.startswith("\t"):
                started = True
            if started:
                body.append(line)
        return body

    def test_every_comment_inside_the_recipe_keeps_the_continuation(self) -> None:
        """No comment inside the recipe drops the trailing backslash."""
        body = self._recipe_body()
        offenders = [
            line.strip()
            for line in body[:-1]
            if line.strip().startswith("#") and not line.rstrip().endswith("\\")
        ]

        tm.that(offenders, eq=[])


__all__: tuple[str, ...] = ()
