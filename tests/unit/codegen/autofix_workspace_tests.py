"""Tests for FlextInfraCodegenFixer workspace-level operations.

Validates project exclusion, empty src handling, and files_modified tracking.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from flext_infra import FlextInfraCodegenFixer, t
from tests import (
    FlextInfraCodegenTestProjectFactory,
)


def test_flexcore_excluded_from_run(tmp_path: Path) -> None:
    flexcore = tmp_path / "flexcore"
    flexcore.mkdir()
    (flexcore / "Makefile").touch()
    (flexcore / "pyproject.toml").write_text("[project]\nname='flexcore'\n")
    (flexcore / ".git").mkdir()
    pkg = flexcore / "src" / "flexcore"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").touch()
    (pkg / "typings.py").write_text("pass\n")
    (pkg / "constants.py").write_text("pass\n")
    (pkg / "base.py").write_text("import typing\nT = typing.TypeVar('T')\n")
    FlextInfraCodegenTestProjectFactory.create_project(
        tmp_path=tmp_path,
        name="test-proj",
        pkg_name="test_proj",
        files={
            "base.py": "import typing\nT = typing.TypeVar('T')\n"
            "class TestProjBase:\n    pass\n",
        },
    )
    fixer = FlextInfraCodegenFixer(tmp_path)
    results = fixer.run()
    project_names = [res.project for res in results]
    tm.that("flexcore" not in project_names, eq=True)
    tm.that(project_names, has="test-proj")


def test_project_without_src_returns_empty(tmp_path: Path) -> None:
    project = tmp_path / "no-src-proj"
    project.mkdir()
    (project / "Makefile").touch()
    (project / "pyproject.toml").write_text("[project]\nname='no-src-proj'\n")
    (project / ".git").mkdir()
    fixer = FlextInfraCodegenFixer(tmp_path)
    result = fixer.fix_project(project)
    tm.that(result.project, eq="no-src-proj")
    tm.that(result.violations_fixed, eq=[])
    tm.that(result.violations_skipped, eq=[])
    tm.that(result.files_modified, eq=[])


def test_files_modified_tracks_affected_files(tmp_path: Path) -> None:
    project = FlextInfraCodegenTestProjectFactory.create_project(
        tmp_path=tmp_path,
        name="test-proj",
        pkg_name="test_proj",
        files={
            "base.py": "from typing import Final\nMAX_RETRIES: Final = 3\n"
            "class TestProjBase:\n    pass\n",
        },
    )
    fixer = FlextInfraCodegenFixer(tmp_path)
    result = fixer.fix_project(project)
    tm.that(len(result.files_modified), eq=4)
    modified_str = " ".join(result.files_modified)
    tm.that(modified_str, contains="__init__.py")
    tm.that(modified_str, contains="base.py")
    tm.that(modified_str, contains="constants.py")
    tm.that(modified_str, contains="typings.py")


__all__: t.StrSequence = []
