"""Import-law engine: tests tier root fixed points.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests import c, tm, u
from tests.unit.refactor.import_normalization_support import (
    TestsFlextInfraRefactorImportNormalizationSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalizationTestsRoot(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """The tests tier root and its family letters reach a fixed point."""

    @classmethod
    @c.Tests.MARK.slow
    def test_tests_family_letter_binds_upstream_not_tier_root(
        cls, tmp_path: Path
    ) -> None:
        """A tests family module keeps its own letter from the upstream facade."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"u": ".utilities"})
        (tier / "utilities.py").write_text(
            "from demo_pkg import u as upstream_u\n"
            "class u(upstream_u):\n"
            "    pass\n"
            "__all__: list[str] = ['u']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        cls._lazy_init(tier / "_utilities", {"DemoTools": ".tools"})
        target = tier / "_utilities" / "tools.py"
        source = (
            "from demo_pkg import u\n"
            "\n"
            "\n"
            "def render(value: str) -> str:\n"
            "    return u.render(value)\n"
        )
        first = tm.ok(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=target,
                source=source,
            )
        )
        second = tm.ok(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=target,
                source=first,
            )
        )
        tm.that(first, has="from demo_pkg import u")
        tm.that(first, lacks="from tests import u")
        tm.that(second, eq=first)
