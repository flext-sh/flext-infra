"""Tests for the WHAT= phase resolver (u.Infra.resolve_what), SSOT for phases.

Empty phase expands to all phases of the verb; a valid phase resolves to itself;
an unknown phase is a usage failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra import u

if TYPE_CHECKING:
    from tests import t


class TestResolveWhat:
    def test_empty_phase_expands_to_all(self) -> None:
        result = u.Infra.resolve_what("check", "")
        tm.ok(result)
        tm.that("format" in result.value, eq=True)
        tm.that("loc-cap" in result.value, eq=True)

    def test_valid_phase_resolves_to_single(self) -> None:
        result = u.Infra.resolve_what("check", "format")
        tm.ok(result)
        tm.that(tuple(result.value), eq=("format",))

    def test_unknown_phase_is_usage_failure(self) -> None:
        result = u.Infra.resolve_what("check", "bogus")
        tm.fail(result)
        tm.that("bogus" in (result.error or ""), eq=True)

    def test_verb_without_phases_is_empty(self) -> None:
        result = u.Infra.resolve_what("clean", "")
        tm.ok(result)
        tm.that(tuple(result.value), eq=())


__all__: t.StrSequence = []
