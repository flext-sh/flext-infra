"""The TYPE_CHECKING scaffold cleaner honors its guard-survival contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest

from tests import tm, u


class TestsFlextInfraOrphanImport:
    """Strip the guard import only when no read of the name survives."""

    @staticmethod
    @pytest.mark.parametrize("guard", ["TYPE_CHECKING", "typing.TYPE_CHECKING"])
    def test_guarded_import_survives_a_populated_block(guard: str) -> None:
        """A populated TYPE_CHECKING block keeps its guarded import intact."""
        source = (
            "from typing import TYPE_CHECKING\n"
            "\n"
            f"if {guard}:\n"
            "    from collections.abc import Sequence\n"
            "\n"
            "def read() -> Sequence[int]:\n"
            "    raise NotImplementedError\n"
        )
        tm.that(u.Infra.strip_type_checking_scaffold(source), eq=source)

    @staticmethod
    def test_multi_name_import_keeps_the_surviving_names() -> None:
        """A populated guard block retains its whole multi-name import line."""
        source = (
            "from typing import TYPE_CHECKING, ClassVar\n"
            "\n"
            "if TYPE_CHECKING:\n"
            "    from collections.abc import Sequence\n"
            "\n"
            "class Row:\n"
            "    table: ClassVar[str]\n"
        )
        tm.that(u.Infra.strip_type_checking_scaffold(source), eq=source)

    @staticmethod
    def test_orphan_import_drops_after_the_block_is_gone() -> None:
        """An orphan import with no surviving guard block is stripped."""
        source = (
            "from typing import TYPE_CHECKING\n\ndef read() -> int:\n    return 0\n"
        )
        tm.that(u.Infra.strip_type_checking_scaffold(source), lacks="TYPE_CHECKING")

    @staticmethod
    def test_empty_guard_block_and_its_import_disappear_together() -> None:
        """An empty guard block goes first, then its now-orphan import."""
        source = (
            "from typing import TYPE_CHECKING, ClassVar\n"
            "\n"
            "if TYPE_CHECKING:\n"
            "    pass\n"
            "\n"
            "class Row:\n"
            "    table: ClassVar[str]\n"
        )
        stripped = u.Infra.strip_type_checking_scaffold(source)
        tm.that(stripped, lacks="TYPE_CHECKING")
        tm.that(stripped, has="from typing import ClassVar")
