"""Tests for the canonical make-verb constants + WHAT phase map.

Asserts the public ``c.Infra`` surface: the 8 canonical workspace verbs and the
WHAT_PHASES map that absorbs the retired verbs as phases.
"""

from __future__ import annotations

from flext_tests import tm

from flext_infra import c
from tests import t

_CANONICAL_VERBS = frozenset(
    {"boot", "build", "check", "test", "val", "ship", "clean", "help"},
)
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
    def test_core_verbs_are_canonical_eight(self) -> None:
        verbs = frozenset(verb for verb, _ in c.Infra.WORKSPACE_CORE_VERBS)
        tm.that(verbs == _CANONICAL_VERBS, eq=True)

    def test_retired_verbs_absent_from_surface(self) -> None:
        surface = {verb for verb, _ in c.Infra.WORKSPACE_CORE_VERBS}
        surface |= {verb for verb, _ in c.Infra.WORKSPACE_GIT_VERBS}
        tm.that(_RETIRED_VERBS.isdisjoint(surface), eq=True)

    def test_what_phases_absorb_retired_verbs(self) -> None:
        phases = c.Infra.WHAT_PHASES
        tm.that("format" in phases["check"], eq=True)
        tm.that("pol" in phases["check"], eq=True)
        tm.that("scan" in phases["check"], eq=True)
        tm.that("gen" in phases["build"], eq=True)
        tm.that("save" in phases["ship"], eq=True)
        tm.that("loc-delta" in phases["val"], eq=True)

    def test_what_variable_default_declared(self) -> None:
        names = {name for name, _ in c.Infra.WORKSPACE_VARIABLE_DEFAULTS}
        tm.that("WHAT" in names, eq=True)


__all__: t.StrSequence = []
