"""Validate the typed handler projection from the canonical Make verbs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config
from flext_tests import tm

if TYPE_CHECKING:
    from tests import t


class TestMakeHandlerProjection:
    """Prove the public handler matrix is derived from the typed registry."""

    def test_handler_matrix_matches_verbs_in_declared_order(self) -> None:
        make = config.Infra.codegen.make
        expected = {verb.name: verb.whats for verb in make.verbs}

        tm.that(dict(make.handler_whats), eq=expected)
        tm.that(tuple(make.handler_whats), eq=tuple(expected))


__all__: t.StrSequence = []
