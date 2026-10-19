"""Tests for scaffolder generated code validity and naming conventions.

Validates AST parseability and {Prefix}{Suffix} class naming convention
for both src/ and tests/ generated modules.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

import pytest

from flext_infra.codegen.scaffolder import FlextInfraCodegenScaffolder
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import t


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

    class TestsGeneratedTopologyContracts:
        """Generated topology modules compile and follow the naming contract."""

        @pytest.mark.parametrize(
            ("with_all_modules", "validate"),
            [
                pytest.param(
                    False,
                    partial(
                        _validate_modules_parse,
                        modules=tuple(row[0] for row in c.Infra.SRC_MODULES),
                    ),
                    id="src-parses",
                ),
                pytest.param(
                    True,
                    partial(
                        _validate_modules_parse,
                        modules=tuple(row[0] for row in c.Infra.TESTS_MODULES),
                    ),
                    id="tests-parses",
                ),
                pytest.param(
                    False,
                    partial(
                        _validate_class_names,
                        filename_to_expected_class={
                            "constants.py": "TestProjectConstants",
                            "typings.py": "TestProjectTypes",
                            "protocols.py": "TestProjectProtocols",
                            "models.py": "TestProjectModels",
                            "utilities.py": "TestProjectUtilities",
                        },
                    ),
                    id="src-class-names",
                ),
                pytest.param(
                    True,
                    partial(
                        _validate_class_names,
                        filename_to_expected_class={
                            "constants.py": "TestsTestProjectConstants",
                            "typings.py": "TestsTestProjectTypes",
                            "protocols.py": "TestsTestProjectProtocols",
                            "models.py": "TestsTestProjectModels",
                            "utilities.py": "TestsTestProjectUtilities",
                        },
                    ),
                    id="tests-class-names",
                ),
            ],
        )
        def test_generated_topology_satisfies_declared_contract(
            self,
            tmp_path: Path,
            *,
            with_all_modules: bool,
            validate: Callable[[Path], None],
        ) -> None:
            """Scaffold one topology and prove its declared module contract."""
            project = u.Tests.create_scaffolder_test_project(
                tmp_path=tmp_path,
                with_all_modules=with_all_modules,
            )
            target = (
                project / "tests"
                if with_all_modules
                else project / "src" / "test_project"
            )
            if with_all_modules:
                target.mkdir()
            scaffolder = FlextInfraCodegenScaffolder(repository_root=tmp_path)
            _ = scaffolder.run(
                projects=[u.Tests.create_project_info(project, name=project.name)]
            )
            validate(target)

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
