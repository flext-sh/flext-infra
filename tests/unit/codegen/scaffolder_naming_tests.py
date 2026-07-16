"""Tests for scaffolder generated code validity and naming conventions.

Validates AST parseability and {Prefix}{Suffix} class naming convention
for both src/ and tests/ generated modules.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from tests import c, m, t, u


def _parse_class_names(source: str) -> t.StrSequence:
    """Extract all class names from Python source via the codegen regex authority.

    Single Responsibility: detect class definitions only.

    Returns:
        The class names declared in the source text.
    """
    return tuple(map(str, c.Infra.DETECTION_CLASS_DECL_RE.findall(source)))


def _validate_modules_parse(base_dir: Path, modules: t.StrSequence) -> None:
    """Validate that all modules in base_dir compile as valid Python.

    Utility: eliminates duplicate syntax validation logic.
    """
    for mod in modules:
        source = (base_dir / mod).read_text(encoding="utf-8")
        compiled = compile(source, str(base_dir / mod), "exec")
        tm.that(compiled, none=False)


def _validate_class_names(
    base_dir: Path, filename_to_expected_class: t.StrMapping
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


def _project_info(
    project: Path, *, package_name: str = "test_project"
) -> p.Infra.ProjectInfo:
    return u.Tests.create_project_info(
        project, name=project.name, package_name=package_name
    )


class TestGeneratedFilesAreValidPython:
    """Verify that scaffolded source and test modules compile."""

    def test_generated_src_modules_parse_successfully(self, tmp_path: Path) -> None:
        """Compile every scaffolded production module."""
        project = u.Tests.create_scaffolder_test_project(
            tmp_path=tmp_path, with_all_modules=False
        )
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        _ = scaffolder.run(projects=[_project_info(project)])
        pkg = project / "src" / "test_project"
        _validate_modules_parse(pkg, u.Tests.src_module_files())

    def test_generated_tests_modules_parse_successfully(self, tmp_path: Path) -> None:
        """Compile every scaffolded test module."""
        project = u.Tests.create_scaffolder_test_project(
            tmp_path=tmp_path, with_all_modules=True
        )
        tests_dir = project / "tests"
        tests_dir.mkdir()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        _ = scaffolder.run(projects=[_project_info(project)])
        _validate_modules_parse(tests_dir, u.Tests.src_module_files())


class TestGeneratedClassNamingConvention:
    """Verify canonical class names emitted by the scaffolder."""

    def test_src_class_names_use_prefix_suffix(self, tmp_path: Path) -> None:
        """Preserve the project prefix and facade suffix in source classes."""
        project = u.Tests.create_scaffolder_test_project(
            tmp_path=tmp_path, with_all_modules=False
        )
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        _ = scaffolder.run(projects=[_project_info(project)])
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

    def test_tests_class_names_use_tests_prefix_suffix(self, tmp_path: Path) -> None:
        """Prefix scaffolded test facade classes with Tests."""
        project = u.Tests.create_scaffolder_test_project(
            tmp_path=tmp_path, with_all_modules=True
        )
        tests_dir = project / "tests"
        tests_dir.mkdir()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        _ = scaffolder.run(projects=[_project_info(project)])
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
        """Return an empty result when no package prefix exists."""
        project = tmp_path / "empty-project"
        project.mkdir()
        (project / "Makefile").touch()
        scaffolder = FlextInfraCodegenScaffolder(workspace_root=tmp_path)
        [result] = scaffolder.run(
            projects=[
                u.Tests.create_project_info(
                    project, name="empty-project", package_name=""
                )
            ]
        )
        tm.that(result.files_created, empty=True)
        tm.that(result.files_skipped, empty=True)
        tm.that(result.project, eq="empty-project")
