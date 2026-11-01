"""Import-law ordering converges with the formatter's import sorting.

Every normalized source is scenario data under ``tests/fixtures/import-order``.

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

    from tests import p


class TestsFlextInfraRefactorImportNormalizationOrder(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Observe module-level import ordering through ``normalize_import_source``.

    Premise (measured on a consumer ``make gen``): the import law sorted
    ``from x import y`` among ``import x`` statements and merged ``__future__``
    into the standard library, so every formatter-sorted authored module
    received a rewrite that the formatter's ``I001`` repair then undid. The
    law now orders exactly as the formatter does.
    """

    SCENARIO = "import-order"

    @classmethod
    def _scenario_sources(
        cls, fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> dict[str, str]:
        """Return every scenario source, materialized beside the project.

        Returns:
            The source text of each import-order case keyed by its stem.

        """
        scenarios = fixture_tree(cls.SCENARIO, destination=tmp_path / "scenarios")
        return {
            path.stem: path.read_text(encoding=c.DEFAULT_ENCODING)
            for path in scenarios.glob("*.py")
        }

    @classmethod
    def test_formatter_sorted_module_is_never_rewritten(
        cls, fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> None:
        """Straight imports before from-imports, ``__future__`` first: no edit."""
        project, package = cls._project(tmp_path)
        source = cls._scenario_sources(fixture_tree, tmp_path)["formatter-sorted"]

        normalized = u.Infra.normalize_import_source(
            project_root=project,
            file_path=package / "services" / "worker.py",
            source=source,
        )

        tm.ok(normalized, eq=source)

    @classmethod
    def test_unsorted_module_takes_the_formatter_order(
        cls, fixture_tree: p.Tests.FixtureTree, tmp_path: Path
    ) -> None:
        """A from-import ahead of a straight import moves behind it."""
        project, package = cls._project(tmp_path)
        sources = cls._scenario_sources(fixture_tree, tmp_path)

        normalized = u.Infra.normalize_import_source(
            project_root=project,
            file_path=package / "services" / "worker.py",
            source=sources["from-before-straight"],
        )

        tm.ok(normalized, eq=sources["formatter-sorted"])


__all__: list[str] = ["TestsFlextInfraRefactorImportNormalizationOrder"]
