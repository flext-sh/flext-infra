"""Tests for scaffolder generated code validity and naming conventions.

Validates AST parseability and {Prefix}{Suffix} class naming convention
for both src/ and tests/ generated modules.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


def _generate_tier(tmp_path: Path, *, tests_tier: bool) -> Path:
    """Scaffold a test project and return the generated src or tests package dir.

    Returns:
        The generated source package or tests directory of the test project.

    """
    project = u.Tests.create_scaffolder_test_project(
        tmp_path=tmp_path,
        with_all_modules=tests_tier,
    )
    if tests_tier:
        (project / "tests").mkdir()
    scaffolder = FlextInfraCodegenScaffolder(repository_root=tmp_path)
    _ = scaffolder.run(
        projects=[u.Tests.create_project_info(project, name=project.name)]
    )
    return project / "tests" if tests_tier else project / "src" / "test_project"


def _validate_modules_parse(base_dir: Path, modules: t.StrSequence) -> None:
    """Compile every module in ``base_dir`` as valid Python."""
    for mod in modules:
        source = (base_dir / mod).read_text(encoding="utf-8")
        _ = compile(source, str(base_dir / mod), "exec")


def _validate_class_names(
    base_dir: Path,
    filename_to_expected_class: t.StrMapping,
) -> None:
    """Validate expected class names exist in the generated modules."""
    for filename, expected_class in filename_to_expected_class.items():
        source = (base_dir / filename).read_text(encoding="utf-8")
        class_names = c.Infra.DETECTION_CLASS_DECL_RE.findall(source)
        tm.that(
            expected_class in class_names,
            eq=True,
            msg=f"{filename} should contain {expected_class}",
        )


class TestsFlextInfraCodegenScaffolderNaming:
    """Test suite for scaffolder generated code validity and naming conventions."""

    class TestsGeneratedFilesAreValidPython:
        """Generated source and test modules compile as Python."""

        @pytest.mark.parametrize(
            ("tests_tier", "rows"),
            [(False, c.Infra.SRC_MODULES), (True, c.Infra.TESTS_MODULES)],
            ids=["src", "tests"],
        )
        def test_generated_modules_parse_successfully(
            self,
            tmp_path: Path,
            tests_tier: bool,
            rows: t.VariadicTuple[t.Quad[str, str, str, str]],
        ) -> None:
            """Compile every generated facade module of the selected tier."""
            _validate_modules_parse(
                _generate_tier(tmp_path, tests_tier=tests_tier),
                tuple(row[0] for row in rows),
            )

    class TestsGeneratedClassNamingConvention:
        """Generated class names follow the canonical prefix and suffix contract."""

        @pytest.mark.parametrize(
            ("tests_tier", "prefix"),
            [(False, "TestProject"), (True, "TestsTestProject")],
            ids=["src", "tests"],
        )
        def test_class_names_use_prefix_suffix(
            self,
            tmp_path: Path,
            tests_tier: bool,
            prefix: str,
        ) -> None:
            """Use the tier prefix on generated facade classes."""
            _validate_class_names(
                _generate_tier(tmp_path, tests_tier=tests_tier),
                {
                    "constants.py": f"{prefix}Constants",
                    "typings.py": f"{prefix}Types",
                    "protocols.py": f"{prefix}Protocols",
                    "models.py": f"{prefix}Models",
                    "utilities.py": f"{prefix}Utilities",
                },
            )

        @staticmethod
        def test_no_prefix_returns_empty_result(tmp_path: Path) -> None:
            """Skip generation when no package prefix is available."""
            project = tmp_path / "empty-project"
            project.mkdir()
            (project / "Makefile").touch()
            scaffolder = FlextInfraCodegenScaffolder(repository_root=tmp_path)
            [result] = scaffolder.run(
                projects=[
                    u.Tests.create_project_info(
                        project, name=project.name, package_name=""
                    )
                ],
            )
            tm.that(result.files_created, empty=True)
            tm.that(result.files_skipped, empty=True)
            tm.that(result.project, eq="empty-project")
