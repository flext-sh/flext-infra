"""Tests for the canonical workspace WHAT phase map.

Asserts the public ``c.Infra`` helper map used by legacy CLI helpers. Public
Make routing is owned by the registry discovered from ``scripts/cmd``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import c

if TYPE_CHECKING:
    from tests import t

_PHASED_VERBS = frozenset({"boot", "build", "check", "test", "val", "ship"})
_RETIRED_VERBS = frozenset({
    "scan",
    "fmt",
    "types",
    "pol",
    "cqrs",
    "pyre",
    "stubs",
    "gen",
    "mod",
    "up",
    "constraints",
    "sync",
    "docs",
    "save",
    "tag",
    "push",
    "pr",
    "rel",
    "stat",
    "imp",
})


class TestMakeConstants:
    def test_what_phase_verbs_are_canonical_subset(self) -> None:
        verbs = frozenset(c.Infra.WHAT_PHASES)
        tm.that(verbs == _PHASED_VERBS, eq=True)

    def test_retired_verbs_absent_from_surface(self) -> None:
        tm.that(_RETIRED_VERBS.isdisjoint(c.Infra.WHAT_PHASES), eq=True)

    def test_what_phases_absorb_retired_verbs(self) -> None:
        phases = c.Infra.WHAT_PHASES
        tm.that("format" in phases["check"], eq=True)
        tm.that("pol" in phases["check"], eq=True)
        tm.that("scan" in phases["check"], eq=True)
        tm.that("gen" in phases["build"], eq=True)
        tm.that("save" in phases["ship"], eq=True)

    def test_what_variable_default_declared(self) -> None:
        names = {name for name, _ in c.Infra.WORKSPACE_VARIABLE_DEFAULTS}
        tm.that("WHAT" in names, eq=True)


__all__: t.StrSequence = []
