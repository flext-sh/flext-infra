"""Setup provisions an environment in every checkout, including worktrees.

A member delegates provisioning to the principal because the uv workspace venv
lives at ``RUNTIME_ROOT``, not in the member. That delegation is only meaningful
when the principal is a *different* checkout.

In an isolated ``git worktree`` of a member there is no superproject, so
``WORKSPACE_ROOT`` falls back to the worktree itself and ``RUNTIME_ROOT`` equals
``PROJECT_ROOT`` -- while ``MAKE_PROFILE`` stays ``workspace-member`` because it
is baked in at generation time. The recipe then runs
``make -C <itself> _builtin_setup_environment``: recursion onto the same target,
which Make considers already satisfied. ``setup`` exits 0 having created
nothing, and the next verb fails with "missing environment interpreter ...;
make setup creates it".

That is evidence failure, not just a missing venv: the verb reports success for
work it did not do. It also blocks the delivery flow outright -- a worktree that
cannot provision cannot run a gate, so no commit can pass the hook and no PR can
be opened from it.

Delegation must therefore be guarded by the principal actually being elsewhere.
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
    / "Makefile.j2"
)


def _template_text() -> str:
    """Return the generated-Makefile template source."""
    return _TEMPLATE.read_text(encoding="utf-8")


def _delegating_recipes() -> list[str]:
    """Return each whole recipe that re-enters Make at ``RUNTIME_ROOT``.

    The guard and the delegation sit on different lines of one shell recipe,
    so the unit of inspection is the recipe, not the line.
    """
    recipes: list[str] = []
    current: list[str] = []
    for line in _template_text().splitlines():
        if line.startswith("\t"):
            current.append(line.strip())
            continue
        if current:
            recipes.append("\n".join(current))
            current = []
    if current:
        recipes.append("\n".join(current))
    return [
        recipe
        for recipe in recipes
        if re.search(r"\$\(MAKE\)\s+-C\s+\"\$\(RUNTIME_ROOT\)\"", recipe)
    ]


def test_environment_delegation_cannot_target_the_calling_checkout() -> None:
    """Delegating to ``RUNTIME_ROOT`` is guarded against self-recursion.

    Without the guard, a checkout whose principal resolves to itself delegates
    to itself, provisions nothing, and still reports success.
    """
    unguarded = [
        recipe for recipe in _delegating_recipes() if "$(PROJECT_ROOT)" not in recipe
    ]

    assert not unguarded, (
        "setup delegates to RUNTIME_ROOT without proving it differs from "
        f"PROJECT_ROOT, so a worktree delegates to itself: {unguarded}"
    )


def test_every_profile_reaches_the_provisioning_recipe() -> None:
    """No profile may leave ``SETUP_ENVIRONMENT_RECIPE`` unreachable.

    Whatever the profile, a checkout that has no usable interpreter must end up
    running the recipe that creates one.
    """
    text = _template_text()
    profile_branches = len(
        re.findall(r"^ifeq \(\$\(MAKE_PROFILE\)", text, re.MULTILINE)
    )
    recipe_uses = len(re.findall(r"\$\(SETUP_ENVIRONMENT_RECIPE\)", text))

    assert recipe_uses >= profile_branches, (
        f"{profile_branches} profile branches but only {recipe_uses} reach the "
        "provisioning recipe"
    )


__all__: tuple[str, ...] = ()
