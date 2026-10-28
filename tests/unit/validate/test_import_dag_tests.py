"""Behavior tests for the strict test import DAG guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

import pytest

from flext_infra.validate.test_import_dag import FlextInfraValidateTestImportDag
from tests import c, tm

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m, p


class TestsFlextInfraImportDag:
    """Verify allowed and forbidden package-test import edges."""

    @staticmethod
    def _project(tmp_path: Path, files: Mapping[str, str]) -> Path:
        project = tmp_path / "sample"
        (project / c.PYPROJECT_FILENAME).parent.mkdir(parents=True, exist_ok=True)
        (project / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "sample"\nversion = "0.0.1"\n',
            encoding="utf-8",
        )
        for relative, source in files.items():
            target = project / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        return project

    @pytest.mark.parametrize(
        ("source", "imported"),
        [
            ("tests/typings.py", "from tests.constants import C\n"),
            ("tests/protocols.py", "from tests.typings import T\n"),
            ("tests/models.py", "from tests.protocols import P\n"),
            ("tests/utilities.py", "from tests.models import M\n"),
            ("tests/constants.py", "from tests import c, r\n"),
            ("tests/models.py", "from tests.fixtures.users import user\n"),
            ("tests/__init__.py", "from tests.conftest import fixture\n"),
            ("src/sample/api.py", "from tests import c, r, u\n"),
        ],
    )
    def test_forbidden_edges_fail(
        self,
        tmp_path: Path,
        source: str,
        imported: str,
    ) -> None:
        """Test forbidden edges fail."""
        project = self._project(tmp_path, {source: imported})
        report: m.Infra.ValidationReport = tm.ok(
            FlextInfraValidateTestImportDag().build_report(project),
        )
        tm.fail(report.passed)

    @pytest.mark.parametrize(
        ("source", "case"),
        [
            ("tests/unit/test_behavior.py", "absolute"),
            ("tests/unit/test_behavior.py", "relative"),
            ("tests/conftest.py", "plugin"),
        ],
    )
    def test_artifact_imports_fail_from_every_test_layer(
        self,
        tmp_path: Path,
        fixture_tree: p.Tests.FixtureTree,
        source: str,
        case: str,
    ) -> None:
        """Reject imports of artifact data from ordinary tests and conftest."""
        scenario = fixture_tree("artifact-imports", destination=tmp_path / "scenarios")
        project = self._project(
            tmp_path,
            {source: (scenario / f"{case}.py").read_text(encoding=c.DEFAULT_ENCODING)},
        )
        report: m.Infra.ValidationReport = tm.ok(
            FlextInfraValidateTestImportDag().build_report(project),
        )
        tm.fail(report.passed)

    @pytest.mark.parametrize("name", ["__init__.py", "conftest.py"])
    def test_artifact_wiring_is_rejected_without_parsing(
        self, tmp_path: Path, name: str
    ) -> None:
        """Reject package and pytest wiring using only its path."""
        project = self._project(
            tmp_path,
            {f"tests/fixtures/scenario/{name}": "invalid Python artifact"},
        )
        report: m.Infra.ValidationReport = tm.ok(
            FlextInfraValidateTestImportDag().build_report(project),
        )
        tm.fail(report.passed)

    def test_python_artifacts_are_data_without_source_parsing(
        self, tmp_path: Path
    ) -> None:
        """Ignore root and nested Python artifacts without decoding their bytes."""
        project = self._project(tmp_path, {"src/sample/api.py": "value = 1\n"})
        for relative in ("tests/fixtures/input.py", "tests/fixtures/scenario/input.py"):
            artifact = project / relative
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_bytes(b"\xff\xfe\x00")
        report: m.Infra.ValidationReport = tm.ok(
            FlextInfraValidateTestImportDag().build_report(project),
        )
        tm.ok(report.passed)

    def test_forward_facets_and_type_checking_reverse_edges_pass(
        self,
        tmp_path: Path,
    ) -> None:
        """Test forward facets and type checking reverse edges pass."""
        project = self._project(
            tmp_path,
            {
                "tests/constants.py": "from tests.typings import t\n",
                "tests/typings.py": "from tests.protocols import p\n",
                "tests/protocols.py": "from tests.models import m\n",
                "tests/models.py": "from tests.utilities import u\n",
                "tests/utilities.py": (
                    "from __future__ import annotations\n"
                    "from typing import TYPE_CHECKING\n"
                    "if TYPE_CHECKING:\n"
                    "    from tests.constants import c\n"
                ),
            },
        )
        report: m.Infra.ValidationReport = tm.ok(
            FlextInfraValidateTestImportDag().build_report(project),
        )
        tm.ok(report.passed)
