"""The TYPE_CHECKING scaffold cleaner honors its guard-survival contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraOrphanImport:
    """Strip the guard import only when no read of the name survives."""

    @staticmethod
    def _strip(tmp_path: Path, source: str) -> str:
        """Strip one real module's scaffold through its native source module.

        Returns:
            The candidate text the scaffold cleaner proposes.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "scaffold.py"
        path.write_text(source, encoding="utf-8")
        with u.Infra.facade_source_project(root) as (project, _sources):
            module = u.Infra.require_source_module(
                project.get_pymodule(
                    project.get_resource(path.relative_to(root).as_posix())
                )
            )
            stripped = tm.ok(u.Infra.strip_type_checking_scaffold(module))
        tm.that(path.read_text(encoding="utf-8"), eq=source)
        return stripped

    @staticmethod
    @c.Tests.MARK.parametrize("guard", ["TYPE_CHECKING", "typing.TYPE_CHECKING"])
    def test_guarded_import_survives_a_populated_block(
        tmp_path: Path, guard: str
    ) -> None:
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
        tm.that(TestsFlextInfraOrphanImport._strip(tmp_path, source), eq=source)

    @staticmethod
    def test_multi_name_import_keeps_the_surviving_names(tmp_path: Path) -> None:
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
        tm.that(TestsFlextInfraOrphanImport._strip(tmp_path, source), eq=source)

    @staticmethod
    def test_orphan_import_drops_after_the_block_is_gone(tmp_path: Path) -> None:
        """An orphan import with no surviving guard block is stripped."""
        source = (
            "from typing import TYPE_CHECKING\n\ndef read() -> int:\n    return 0\n"
        )
        tm.that(
            TestsFlextInfraOrphanImport._strip(tmp_path, source),
            lacks="TYPE_CHECKING",
        )

    @staticmethod
    def test_empty_guard_block_and_its_import_disappear_together(
        tmp_path: Path,
    ) -> None:
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
        stripped = TestsFlextInfraOrphanImport._strip(tmp_path, source)
        tm.that(stripped, lacks="TYPE_CHECKING")
        tm.that(stripped, has="from typing import ClassVar")
