"""Fresh-import completeness: every exported pydantic class builds.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import shutil
from typing import TYPE_CHECKING

from flext_infra.validate import FlextInfraValidateFreshImport
from tests import tm, u

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


class TestsFlextInfraFreshImportCompleteness:
    """The export probe fails on unbuildable models and passes buildable ones."""

    @staticmethod
    def _completeness_report(
        tmp_path: Path,
        scenario: Path,
        runtime_root: Path,
    ) -> str | None:
        """Build a real project from ``scenario`` and probe its exports.

        The scenario's model module is placed in a generation-eligible
        workspace and its package initializer is produced by the lazy-init
        generator, exactly as ``make gen`` would.

        Returns:
            The first violation, or ``None`` when the probe passes.

        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        shutil.copy2(scenario / "models.py", package_root / "models.py")
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        report = tm.ok(
            FlextInfraValidateFreshImport(
                repository_root=repository_root,
                runtime_root=runtime_root,
            ).build_report(repository_roots=(repository_root,)),
        )
        return None if report.passed else report.violations[0]

    @staticmethod
    def test_unbuildable_model_fails(
        tmp_path: Path,
        fixture_tree: Callable[[str], Path],
        suite_runtime_root: Path,
    ) -> None:
        """A field type imported only for type checking fails the forced build."""
        violation = TestsFlextInfraFreshImportCompleteness._completeness_report(
            tmp_path,
            fixture_tree("pydantic-completeness") / "red",
            suite_runtime_root,
        )
        tm.that(violation, has="PydanticUndefinedAnnotation")
        tm.that(violation, has="Decimal")

    @staticmethod
    def test_deferred_family_models_build(
        tmp_path: Path,
        fixture_tree: Callable[[str], Path],
        suite_runtime_root: Path,
    ) -> None:
        """Deferred models, a sibling named through its family included, build."""
        violation = TestsFlextInfraFreshImportCompleteness._completeness_report(
            tmp_path,
            fixture_tree("pydantic-completeness") / "green",
            suite_runtime_root,
        )
        tm.that(violation, eq=None)

    @staticmethod
    def test_field_needing_arbitrary_types_fails(
        tmp_path: Path,
        fixture_tree: Callable[[str], Path],
        suite_runtime_root: Path,
    ) -> None:
        """A field type without a schema fails, naming the model and field."""
        violation = TestsFlextInfraFreshImportCompleteness._completeness_report(
            tmp_path,
            fixture_tree("pydantic-arbitrary") / "red",
            suite_runtime_root,
        )
        tm.that(violation, has="PydanticSchemaGenerationError")
        tm.that(violation, has="threading.Thread")
        tm.that(violation, has="FixtureArbitrary.worker needs")

    @staticmethod
    def test_field_declared_through_port_passes(
        tmp_path: Path,
        fixture_tree: Callable[[str], Path],
        suite_runtime_root: Path,
    ) -> None:
        """The same field declared through ``t.Port`` builds without the flag."""
        violation = TestsFlextInfraFreshImportCompleteness._completeness_report(
            tmp_path,
            fixture_tree("pydantic-arbitrary") / "green",
            suite_runtime_root,
        )
        tm.that(violation, eq=None)
