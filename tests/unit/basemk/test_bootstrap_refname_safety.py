"""The generated bootstrap must never expand a refname into shell text.

``SETUP_BRANCH`` is derived from ``git rev-parse --abbrev-ref HEAD``. Git
refnames legitimately allow characters the shell treats as syntax, so a
checkout named ``x;id`` or ``x$(id)`` turned ``git checkout -b "$(SETUP_BRANCH)"``
into command execution for anyone who ran ``make setup`` on that branch — a CI
runner checking out an attacker-proposed branch name is the realistic path.

The fix is structural: the recipe must validate the refname against a strict
allowlist before any command interpolates it.
"""

from __future__ import annotations

import re

from flext_infra import c
from flext_infra.basemk.renderer import FlextInfraBaseMkTemplateRenderer
from flext_tests import tm

# Lines that interpolate the branch into a command the shell parses.
_BRANCH_COMMAND = re.compile(
    r"^\s*(?!#).*\bgit\s+(checkout|switch|branch)\b.*\$\(SETUP_BRANCH\)",
    re.MULTILINE,
)


class TestsBootstrapRefnameSafety:
    """The bootstrap validates ``SETUP_BRANCH`` before interpolating it."""

    def test_bootstrap_validates_the_refname_before_use(self) -> None:
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer.render_bootstrap_include())

        tm.that(
            c.Infra.SETUP_BRANCH_GUARD in rendered,
            eq=True,
            msg=(
                "the bootstrap interpolates SETUP_BRANCH into git commands but "
                "declares no refname validation guard"
            ),
        )

    def test_every_branch_command_is_guarded(self) -> None:
        rendered = tm.ok(FlextInfraBaseMkTemplateRenderer.render_bootstrap_include())

        for match in _BRANCH_COMMAND.finditer(rendered):
            recipe = rendered[: match.end()]
            guard_at = recipe.rfind(c.Infra.SETUP_BRANCH_GUARD)
            tm.that(
                guard_at != -1,
                eq=True,
                msg=(
                    "unguarded refname interpolation reaches the shell: "
                    f"{match.group(0).strip()}"
                ),
            )


__all__ = ("TestsBootstrapRefnameSafety",)
