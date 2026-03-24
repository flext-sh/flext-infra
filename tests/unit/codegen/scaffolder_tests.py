"""Tests for FlextInfraCodegenScaffolder service.

Validates module scaffolding for src/ and tests/ directories,
idempotency, and basic scaffold operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraCodegenScaffolder, t
from tests import (
    FlextInfraCodegenTestProjectFactory,
)

_SRC_MODULE_FILES = FlextInfraCodegenTestProjectFactory.SRC_MODULE_FILES


def _create_test_project(tmp_path: Path, *, with_all_modules: bool = True) -> Path:
    return FlextInfraCodegenTestProjectFactory.create_scaffolder_test_project(
        tmp_path=tmp_path,
        with_all_modules=with_all_modules,
    )


class TestScaffoldProjectNoop:
    def test_all_modules_present_creates_nothing(self, tmp_path: Path) -> None:
        project = _create_test_project(tmp_path, with_all_modules=True)
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        result = scaffolder.scaffold_project(project)
        tm.that(result.files_created, eq=[])
        tm.that(len(result.files_skipped), eq=5)
        tm.that(result.project, eq="test-project")


class TestScaffoldProjectCreatesSrcModules:
    def test_creates_missing_src_modules(self, tmp_path: Path) -> None:
        project = _create_test_project(tmp_path, with_all_modules=False)
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        result = scaffolder.scaffold_project(project)
        tm.that(len(result.files_created), eq=5)
        pkg = project / "src" / "test_project"
        for mod in _SRC_MODULE_FILES:
            tm.that((pkg / mod).exists(), eq=True)

    def test_creates_only_missing_modules(self, tmp_path: Path) -> None:
        project = _create_test_project(tmp_path, with_all_modules=False)
        pkg = project / "src" / "test_project"
        (pkg / "constants.py").write_text(
            "class TestProjectConstants:\n    pass\n",
        )
        (pkg / "models.py").write_text("class TestProjectModels:\n    pass\n")
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        result = scaffolder.scaffold_project(project)
        tm.that(len(result.files_created), eq=3)
        tm.that(len(result.files_skipped), eq=2)
        created_names = sorted(Path(f).name for f in result.files_created)
        tm.that(created_names, eq=["protocols.py", "typings.py", "utilities.py"])


class TestScaffoldProjectCreatesTestsModules:
    def test_creates_tests_modules_when_tests_dir_exists(
        self,
        tmp_path: Path,
    ) -> None:
        project = _create_test_project(tmp_path, with_all_modules=True)
        tests_dir = project / "tests"
        tests_dir.mkdir()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        result = scaffolder.scaffold_project(project)
        tests_created = [f for f in result.files_created if "tests" in f]
        tm.that(len(tests_created), eq=5)
        for mod in _SRC_MODULE_FILES:
            tm.that((tests_dir / mod).exists(), eq=True)

    def test_skips_tests_modules_when_no_tests_dir(
        self,
        tmp_path: Path,
    ) -> None:
        project = _create_test_project(tmp_path, with_all_modules=True)
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        result = scaffolder.scaffold_project(project)
        tests_created = [f for f in result.files_created if "tests" in f]
        tm.that(tests_created, eq=[])


class TestScaffoldProjectIdempotency:
    def test_second_run_is_noop(self, tmp_path: Path) -> None:
        project = _create_test_project(tmp_path, with_all_modules=False)
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        first_result = scaffolder.scaffold_project(project)
        second_result = scaffolder.scaffold_project(project)
        tm.that(len(first_result.files_created), eq=5)
        tm.that(second_result.files_created, eq=[])
        tm.that(len(second_result.files_skipped), eq=5)


__all__: t.StrSequence = []
