"""The orphan-import cleaner honors its guard-survival contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import libcst as cst
import pytest

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

    @pytest.mark.parametrize("guard", ["TYPE_CHECKING", "typing.TYPE_CHECKING"])
    def test_guarded_import_survives_a_populated_block(self, guard: str) -> None:
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
        tm.that(self._render(source), eq=source)

    def test_multi_name_import_keeps_the_surviving_names(self) -> None:
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
        tm.that(self._render(source), eq=source)

    def test_orphan_import_drops_after_the_block_is_gone(self) -> None:
        """An orphan import with no surviving guard block is stripped."""
        source = (
            "from typing import TYPE_CHECKING\n\ndef read() -> int:\n    return 0\n"
        )
        tm.that(self._render(source), lacks="TYPE_CHECKING")

    @staticmethod
    def test_scanner_reads_the_guard_not_the_import() -> None:
        """Guard detection follows the block's presence, not the import's."""
        guarded = cst.parse_module(
            "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    pass\n"
        )
        orphan = cst.parse_module("from typing import TYPE_CHECKING\n")
        tm.ok(type_checking_guarded(guarded))
        tm.fail(type_checking_guarded(orphan))

    def test_unrelated_qualified_guard_does_not_retain_orphan_import(self) -> None:
        """Only typing owns the qualified guard recognized by the cleaner."""
        source = (
            "from typing import TYPE_CHECKING\nif unrelated.TYPE_CHECKING:\n    pass\n"
        )
        tm.fail(type_checking_guarded(cst.parse_module(source)))
        tm.that(self._render(source), lacks="from typing import TYPE_CHECKING")
