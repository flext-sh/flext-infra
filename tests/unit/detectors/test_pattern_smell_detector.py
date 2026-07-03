"""Unit tests for the pattern smell detector.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests.models import m
from tests.typings import t

from flext_infra.detectors.pattern_smell_detector import FlextInfraPatternSmellDetector


class TestsFlextInfraPatternSmellDetector:
    """Behavior contract for FlextInfraPatternSmellDetector."""

    @staticmethod
    def _kinds(
        file_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> set[str]:
        violations = FlextInfraPatternSmellDetector.detect_file(
            m.Infra.DetectorContext(
                file_path=file_path,
                rope_project=rope_project,
            ),
        )
        return {v.kind for v in violations}

    def test_detects_typing_list_import(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\n"
            "from typing import List\n"
            "x: List[int] = []\n",
            encoding="utf-8",
        )
        assert "typing_list_import" in self._kinds(sample, rope_project)

    def test_detects_typing_list_attr(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\n"
            "import typing\n"
            "x: typing.List[int] = []\n",
            encoding="utf-8",
        )
        assert "typing_list_attr" in self._kinds(sample, rope_project)

    def test_detects_direct_pydantic_import(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nfrom pydantic import BaseModel\n",
            encoding="utf-8",
        )
        assert "direct_pydantic_import" in self._kinds(sample, rope_project)

    def test_detects_direct_structlog_import(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\n"
            "import structlog\n"
            "logger = structlog.get_logger()\n",
            encoding="utf-8",
        )
        assert "direct_structlog_import" in self._kinds(sample, rope_project)

    def test_detects_direct_oracledb_import(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nimport oracledb\n",
            encoding="utf-8",
        )
        assert "direct_oracledb_import" in self._kinds(sample, rope_project)

    def test_detects_direct_ldap3_import(
        self,
        tmp_path: Path,
        rope_project: t.Infra.RopeProject,
    ) -> None:
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nfrom ldap3 import Server\n",
            encoding="utf-8",
        )
        assert "direct_ldap3_import" in self._kinds(sample, rope_project)
