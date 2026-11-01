"""Import-law engine: a consumer follows a name its initializer stops publishing.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codemod import FlextInfraCodemodLoopPhaseImportNormalization
from tests import tm, u
from tests.unit.refactor.import_normalization_support import (
    TestsFlextInfraRefactorImportNormalizationSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalizationOwnerRoutes(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Planned initializers and consumer routes land in one mod candidate."""

    @classmethod
    def test_foreign_reexport_moves_to_its_declaring_distribution(
        cls, tmp_path: Path
    ) -> None:
        """A foreign class re-published by the root is imported from its owner."""
        project, package = cls._project(tmp_path)
        families = u.Infra.facade_families()
        cls._lazy_init(
            package,
            {
                **{
                    letter: f".{families[letter].module}"
                    for letter in ("c", "t", "m", "u")
                },
                "FlextConstants": "flext_core",
            },
        )
        consumer = package / "consumer.py"
        consumer.write_text(
            "from demo_pkg import FlextConstants\n\n\n"
            "class DemoConsumer:\n"
            "    BASE = FlextConstants\n\n\n"
            "__all__: list[str] = ['DemoConsumer']\n",
            encoding="utf-8",
        )

        tm.that(
            FlextInfraCodemodLoopPhaseImportNormalization.apply_files(
                project, (consumer,)
            ),
            eq=True,
        )

        rewritten = consumer.read_text(encoding="utf-8")
        tm.that(rewritten, has="from flext_core import FlextConstants")
        tm.that(rewritten, lacks="from demo_pkg import FlextConstants")
