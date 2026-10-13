"""Soundness contracts for the rendered Makefile bootstrap recipes.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATES = Path(__file__).parents[3] / "src" / "flext_infra" / "templates"
_ASSIGNMENT = re.compile(r"(?<![-=!<>])\b([a-z_][a-z0-9_]*)=(?!=)")
_USE = re.compile(r"\$\$([a-z_][a-z0-9_]*)")
_TRAP_BODY = re.compile(r"trap '.*?' EXIT", re.DOTALL)
_FUNCTION_BODY = re.compile(r"\b[a-z_][a-z0-9_]*\(\) \{.*?\n\t?\};", re.DOTALL)


def _scannable(recipe: str) -> str:
    """Strip deferred-execution bodies: traps and shell function definitions.

    Their reads execute when the enclosing flow has already assigned the
    receipt variables (the trap fires at exit; a function body runs at its
    call site), so a sequential scan must not mistake those deferred reads
    for straight-line uses.

    Args:
        recipe: The shell recipe text to scan for use-before-assignment violations.

    Returns:
        The tuple of violations found in the recipe, each formatted as "variable
          (line: ...)".
    """
    text = _TRAP_BODY.sub("trap '...' EXIT", recipe)
    return _FUNCTION_BODY.sub("function ... { };", text)


def _scan_sequential_use_before_assignment(recipe: str) -> tuple[str, ...]:
    """Return shell variables read before any assignment inside one recipe.

    The recipe runs under ``sh -u`` (operator 2026-10-13 emission postmortem:
    the rendered Makefile referenced ``mise_lock_usable`` and ``mise_lock``
    before assigning them, so every ``make setup`` died before provisioning).
    The scan walks line-ordered shell text: any ``name=`` token makes the
    variable available from that line on (mid-line ``case`` assignments
    included); a ``$$name`` read before every such line is the defect this
    contract forbids.
    """
    bound: set[str] = set()
    violations: list[str] = []
    for line in _scannable(recipe).splitlines():
        bound.update(assigned.group(1) for assigned in _ASSIGNMENT.finditer(line))
        violations.extend(
            f"{name} (line: {line.strip()[:80]})"
            for name in _USE.findall(line)
            if name not in bound
        )
    return tuple(violations)


class TestsFlextInfraMakefileBootstrapSoundness:
    """Every emitted bootstrap variable is assigned before it is read."""

    def test_bootstrap_recipe_initializes_every_variable_it_reads(self) -> None:
        """The tool bootstrap recipe never reads an unassigned shell variable.

        Raises:
            AssertionError: If bootstrap recipe reads shell variables before assigning
                them.
        """
        recipe = (
            _TEMPLATES / "project" / "base" / ("tool_bootstrap_recipe.j2")
        ).read_text(encoding="utf-8")
        violations = _scan_sequential_use_before_assignment(recipe)
        if violations:
            message = (
                "bootstrap recipe reads shell variables before assigning "
                f"them ({len(violations)}): {violations[:8]}"
            )
            raise AssertionError(message)
        assert recipe

    def test_require_environment_heals_only_outside_ci(self) -> None:
        """The environment requirement re-applies the declared mode locally.

        Why: a checkout synced in the other install mode is recoverable state
        (the declared sync reapplies it); CI must stay a loud failure because
        its environment is exactly what the workflow provisioned.
        """
        makefile = (_TEMPLATES / "project" / "base" / "Makefile.j2").read_text(
            encoding="utf-8",
        )
        start = makefile.index("_builtin_require_environment:")
        block = makefile[start : makefile.index("\nendif", start)]
        tm_heals(block)


def tm_no_violations(violations: tuple[str, ...], recipe: str) -> None:
    """Fail with the named unassigned reads so the cure is one edit away.

    Raises:
        AssertionError: If bootstrap recipe reads shell variables before assigning them.
    """
    if violations:
        message = (
            "bootstrap recipe reads shell variables before assigning them "
            f"({len(violations)}): {violations[:6]}"
        )
        raise AssertionError(message)
    assert recipe


def tm_heals(block: str) -> None:
    """Assert the heal chain: verify, declared sync, editable rebind, re-verify."""
    for fragment in (
        "verify-environment",
        "sync --project",
        "--frozen",
        "pip install",
        "LOCAL_EDITABLE_FLAGS",
        "CI environments never heal",
    ):
        assert fragment in block, f"heal chain misses {fragment}"
