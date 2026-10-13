"""The orphan-import cleaner honors its guard-survival contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import libcst as cst

from flext_infra.codemod._batch_orphan_import import (
    FlextInfraOrphanImport,
    type_checking_guarded,
)
from tests import tm


class TestsFlextInfraOrphanImport:
    """Strip the guarded import only when no read of the name survives."""

    @staticmethod
    def _render(source: str) -> str:
        module = cst.parse_module(source)
        return module.visit(
            FlextInfraOrphanImport(guarded=type_checking_guarded(module))
        ).code

    def test_guarded_import_survives_a_populated_block(self) -> None:
        source = (
            "from typing import TYPE_CHECKING\n"
            "\n"
            "if TYPE_CHECKING:\n"
            "    from collections.abc import Sequence\n"
            "\n"
            "def read() -> Sequence[int]:\n"
            "    raise NotImplementedError\n"
        )
        tm.that(self._render(source), eq=source)

    def test_multi_name_import_keeps_the_surviving_names(self) -> None:
        source = (
            "from typing import TYPE_CHECKING, ClassVar\n"
            "\n"
            "if TYPE_CHECKING:\n"
            "    from collections.abc import Sequence\n"
            "\n"
            "class Row:\n"
            "    table: ClassVar[str]\n"
        )
        tm.that(self._render(source), eq=source)

    def test_orphan_import_drops_after_the_block_is_gone(self) -> None:
        source = (
            "from typing import TYPE_CHECKING\n\ndef read() -> int:\n    return 0\n"
        )
        tm.that(self._render(source), lacks="TYPE_CHECKING")

    def test_scanner_reads_the_guard_not_the_import(self) -> None:
        guarded = cst.parse_module(
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    pass\n"
        )
        orphan = cst.parse_module("from typing import TYPE_CHECKING\n")
        tm.that(type_checking_guarded(guarded), eq=True)
        tm.that(type_checking_guarded(orphan), eq=False)
