"""Validate the canonical typed Make verb registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t


class TestMakeConstants:
    """Validate the loaded registry without restating its configured values."""

    def test_verbs_and_selectors_are_unique(self) -> None:
        verbs = config.Infra.codegen.make.verbs
        names = tuple(verb.name for verb in verbs)

        tm.that(bool(verbs), eq=True)
        tm.that(len(names), eq=len(set(names)))
        for verb in verbs:
            tm.that(bool(verb.whats), eq=True)
            tm.that(len(verb.whats), eq=len(set(verb.whats)))
            tm.that(verb.default_what in verb.whats, eq=True)

    def test_apply_selectors_belong_to_their_verbs(self) -> None:
        make = config.Infra.codegen.make
        mutable_verbs: list[str] = []
        for verb in make.verbs:
            apply_whats = frozenset(verb.apply_whats)
            optional_apply_whats = frozenset(verb.optional_apply_whats)
            whats = frozenset(verb.whats)

            tm.that(apply_whats.issubset(whats), eq=True)
            tm.that(optional_apply_whats.issubset(whats), eq=True)
            tm.that(apply_whats.isdisjoint(optional_apply_whats), eq=True)
            if apply_whats or optional_apply_whats:
                mutable_verbs.append(verb.name)
            if apply_whats:
                tm.that(verb.apply_what in apply_whats, eq=True)
        tm.that(tuple(mutable_verbs), eq=make.mutable_verbs)
        tm.that(set(make.mutable_verbs).issubset(make.serialization.verbs), eq=True)


__all__: t.StrSequence = []
