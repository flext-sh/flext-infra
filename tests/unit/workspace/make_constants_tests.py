"""Tests for registry-owned Make selectors and variables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t


class TestMakeConstants:
    def test_handler_registry_owns_every_selector(self) -> None:
        """Every selector is owned by exactly one typed public verb record."""
        verbs = config.Infra.codegen.make.verbs

        tm.that({verb.name for verb in verbs}, len=len(verbs))
        for verb in verbs:
            tm.that(verb.handlers, empty=False)
            tm.that(verb.default_what in verb.handlers, eq=True)


__all__: t.StrSequence = []
