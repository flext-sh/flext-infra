"""Tests for scaffolder generated code validity and naming conventions.

Validates AST parseability and {Prefix}{Suffix} class naming convention
for both src/ and tests/ generated modules.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraCodegenScaffolder
from tests import (
    FlextInfraCodegenTestProjectFactory,
    t,
)

_SRC_MODULE_FILES = FlextInfraCodegenTestProjectFactory.SRC_MODULE_FILES


def _parse_class_names(source: str) -> t.StrSequence:
    """Extract all class names from Python source code via AST.

    Single Responsibility: parse and extract class definitions only.
    """
    tree = ast.parse(source)
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def _validate_modules_parse(base_dir: Path, modules: t.StrSequence) -> None:
    """Validate that all modules in base_dir parse as valid Python AST.

    Utility: eliminates duplicate parse validation logic.
    """
    for mod in modules:
        source = (base_dir / mod).read_text(encoding="utf-8")
        tree = ast.parse(source)
        tm.that(type(tree).__name__, eq="Module")


def _validate_class_names(
    base_dir: Path,
    filename_to_expected_class: t.StrMapping,
) -> None:
    """Validate expected class names exist in modules.

    Utility: eliminates duplicate class name extraction and validation.
    """
    for filename, expected_class in filename_to_expected_class.items():
        source = (base_dir / filename).read_text(encoding="utf-8")
        class_names = _parse_class_names(source)
        tm.that(
            expected_class in class_names,
            eq=True,
            msg=f"{filename} should contain {expected_class}",
        )


class TestGeneratedFilesAreValidPython:
    def test_generated_src_modules_parse_successfully(
        self,
        tmp_path: Path,
    ) -> None:
        project = FlextInfraCodegenTestProjectFactory.create_scaffolder_test_project(
            tmp_path=tmp_path,
            with_all_modules=False,
        )
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        scaffolder.scaffold_project(project)
        pkg = project / "src" / "test_project"
        _validate_modules_parse(pkg, _SRC_MODULE_FILES)

    def test_generated_tests_modules_parse_successfully(
        self,
        tmp_path: Path,
    ) -> None:
        project = FlextInfraCodegenTestProjectFactory.create_scaffolder_test_project(
            tmp_path=tmp_path,
            with_all_modules=True,
        )
        tests_dir = project / "tests"
        tests_dir.mkdir()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        scaffolder.scaffold_project(project)
        _validate_modules_parse(tests_dir, _SRC_MODULE_FILES)


class TestGeneratedClassNamingConvention:
    def test_src_class_names_use_prefix_suffix(self, tmp_path: Path) -> None:
        project = FlextInfraCodegenTestProjectFactory.create_scaffolder_test_project(
            tmp_path=tmp_path,
            with_all_modules=False,
        )
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        scaffolder.scaffold_project(project)
        pkg = project / "src" / "test_project"
        _validate_class_names(
            pkg,
            {
                "constants.py": "TestProjectConstants",
                "typings.py": "TestProjectTypes",
                "protocols.py": "TestProjectProtocols",
                "models.py": "TestProjectModels",
                "utilities.py": "TestProjectUtilities",
            },
        )

    def test_tests_class_names_use_tests_prefix_suffix(
        self,
        tmp_path: Path,
    ) -> None:
        project = FlextInfraCodegenTestProjectFactory.create_scaffolder_test_project(
            tmp_path=tmp_path,
            with_all_modules=True,
        )
        tests_dir = project / "tests"
        tests_dir.mkdir()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        scaffolder.scaffold_project(project)
        _validate_class_names(
            tests_dir,
            {
                "constants.py": "TestsTestProjectConstants",
                "typings.py": "TestsTestProjectTypes",
                "protocols.py": "TestsTestProjectProtocols",
                "models.py": "TestsTestProjectModels",
                "utilities.py": "TestsTestProjectUtilities",
            },
        )

    def test_no_prefix_returns_empty_result(self, tmp_path: Path) -> None:
        project = tmp_path / "empty-project"
        project.mkdir()
        (project / "Makefile").touch()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        result = scaffolder.scaffold_project(project)
        tm.that(result.files_created, eq=[])
        tm.that(result.files_skipped, eq=[])
        tm.that(result.project, eq="empty-project")
