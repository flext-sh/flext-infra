"""Every command in one verb recipe writes to the same root.

Scope follows the invocation point: run a verb at the workspace and it works
on the whole active workspace; run it in a project and it works on that
project alone.

The ``gen`` recipe broke that by mixing two criteria in the same body:
``codegen conform`` received ``PROJECT_ROOT`` while dependency stages received
``WORKSPACE_ROOT``. A ``gen`` invoked inside one
member therefore rewrote the ``pyproject.toml`` of every sibling -- measured as
"INFO: Updated <sibling>/pyproject.toml" for ~30 repositories, leaving each one
dirty without the caller ever touching it.

The damage compounds: ``gen`` runs inside ``check``, and ``check`` runs in the
pre-commit hook, so a single commit in any lane dirties every sibling.

At the workspace root ``PROJECT_ROOT`` already *is* the workspace, so a single
root keeps the fan-out where it belongs and restricts it everywhere else. No
new flag is needed -- one rule, applied consistently.
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


def _recipe_bodies() -> dict[str, list[str]]:
    """Return each ``_builtin_*`` target mapped to its recipe lines."""
    bodies: dict[str, list[str]] = {}
    current: str | None = None
    for line in _template_text().splitlines():
        target = re.match(r"^(_builtin_[a-z_]+):", line)
        if target:
            current = target.group(1)
            bodies[current] = []
            continue
        if current is None:
            continue
        if line.startswith("\t"):
            bodies[current].append(line.strip())
            continue
        current = None
    return bodies


def _mixed_scope_recipes() -> dict[str, list[str]]:
    """Return recipes whose commands disagree about which root they write to."""
    mixed: dict[str, list[str]] = {}
    for target, lines in _recipe_bodies().items():
        writes = [
            line
            for line in lines
            if "$(PROJECT_ROOT)" in line or "$(WORKSPACE_ROOT)" in line
        ]
        if not writes:
            continue
        uses_project = any("$(PROJECT_ROOT)" in line for line in writes)
        uses_workspace = any("$(WORKSPACE_ROOT)" in line for line in writes)
        if uses_project and uses_workspace:
            mixed[target] = writes
    return mixed


def test_no_recipe_mixes_project_and_workspace_roots() -> None:
    """One recipe never writes to two different roots.

    A command that escalates to ``WORKSPACE_ROOT`` beside one scoped to
    ``PROJECT_ROOT`` mutates siblings the caller never asked for.
    """
    mixed = _mixed_scope_recipes()

    assert not mixed, (
        f"recipes mix invocation scopes and escalate beyond the caller: {mixed}"
    )


def test_recipe_bodies_are_actually_parsed() -> None:
    """Guard the parser so the invariant above cannot pass vacuously."""
    bodies = _recipe_bodies()

    assert any(
        "$(PROJECT_ROOT)" in line for lines in bodies.values() for line in lines
    ), f"no PROJECT_ROOT command found in {_TEMPLATE}; parser is broken"


def test_gen_has_one_codegen_owner() -> None:
    """The gen recipe delegates each mode once to the conform owner.

    Apply verifies its own fixed point inside the conform transaction, so a
    second external check invocation would duplicate ownership.
    """
    text = _template_text()
    assert "CODEGEN_PROJECT_ARGS" not in text

    bodies = _recipe_bodies()
    expected_modes = {"_builtin_gen_check": ("check",), "_builtin_gen_all": ("apply",)}
    for target, modes in expected_modes.items():
        conform_lines = [line for line in bodies[target] if "codegen conform" in line]
        assert len(conform_lines) == len(modes)
        assert all(
            f"--mode {mode}" in line
            for line, mode in zip(conform_lines, modes, strict=True)
        )
        assert all('--root "$(PROJECT_ROOT)"' in line for line in conform_lines)
        assert all('--scope "$(CODEGEN_SCOPE)"' in line for line in conform_lines)
        assert all("deps modernize" not in line for line in bodies[target])
        assert all("deps extra-paths" not in line for line in bodies[target])


def test_gen_init_is_a_direct_hermetic_owner_route() -> None:
    """The narrow init selector never enters conform, hooks, or topology."""
    text = _template_text()
    init_lines = _recipe_bodies()["_builtin_gen_init"]
    init_commands = [line for line in init_lines if "codegen init" in line]

    assert len(init_commands) == 2
    assert all('--workspace "$(PROJECT_ROOT)"' in line for line in init_commands)
    assert all("codegen conform" not in line for line in init_lines)
    assert "$(filter-out setup gen,$(PUBLIC_VERBS)):" in text
    public_init = text.split("gen:\n", 1)[1].split("\n\n", 1)[0]
    init_branch = public_init.split("else", 1)[0]
    assert "_builtin_gen_init" in init_branch
    assert "_dispatch" not in init_branch
    assert "WORKSPACE_ROOT := $(PROJECT_ROOT)" in text
    assert "INIT_FLEXT_INFRA" not in text


def test_project_selector_resolves_members_from_workspace_root() -> None:
    text = _template_text()
    assert "override WORKSPACE := $(WORKSPACE_ROOT)/$(PROJECT)" in text
    assert "override WORKSPACE := $(PROJECT_ROOT)/$(PROJECT)" not in text


__all__: tuple[str, ...] = ()
