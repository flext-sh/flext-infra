"""Every generated recipe remains scoped to its repository-owned root."""

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
    """The gen recipe delegates apply and fixed-point check to one owner."""
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
    assert "WORKSPACE_ROOT" not in text
    assert "INIT_FLEXT_INFRA" not in text


__all__: tuple[str, ...] = ()
