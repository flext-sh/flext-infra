"""Unit tests for the cast-remover transformer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from flext_tests import tm

from flext_infra.transformers.cast_remover import FlextInfraRefactorCastRemover


def _transform(source: str) -> tuple[str, Sequence[str]]:
    """Apply the cast remover to source text."""
    transformer = FlextInfraRefactorCastRemover()
    result: tuple[str, Sequence[str]] = transformer.apply_to_source(source)
    return result


class TestsFlextInfraTransformersCastRemover:
    """Behavior contract for FlextInfraRefactorCastRemover."""

    def test_bare_cast_is_removed(self) -> None:
        source = "from typing import cast\n\nx: int = cast(int, '42')\n"
        code, changes = _transform(source)
        tm.that(code, lacks="cast(")
        tm.that(code, has="'42'")
        tm.that(len(changes), eq=1)

    def test_typing_cast_is_removed(self) -> None:
        source = "import typing\n\nx: int = typing.cast(int, '42')\n"
        code, changes = _transform(source)
        tm.that(code, lacks="typing.cast(")
        tm.that(code, has="'42'")
        tm.that(len(changes), eq=1)

    def test_cast_in_return_statement(self) -> None:
        source = (
            "from typing import cast\n\ndef f() -> int:\n    return cast(int, 1 + 1)\n"
        )
        code, _changes = _transform(source)
        tm.that(code, lacks="cast(")
        tm.that(code, has="return 1 + 1")

    def test_no_cast_unchanged(self) -> None:
        source = "x: int = 42\n"
        code, changes = _transform(source)
        tm.that(code, eq=source)
        assert not changes

    def test_invalid_syntax_unchanged(self) -> None:
        source = "def foo(\n"
        code, changes = _transform(source)
        tm.that(code, eq=source)
        assert not changes
