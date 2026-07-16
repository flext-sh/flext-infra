"""Unit tests for declarative Rope static-rule enforcement.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import config, u
from tests import m
from flext_tests import tm

from pathlib import Path

from tests import p, t



class TestsFlextInfraPatternSmellDetector:
    """Behavior contract for the public declarative Rope rule engine."""

    @staticmethod
    def _kinds(file_path: Path, rope_project: t.Infra.RopeProject) -> set[str]:
        violations = u.Infra.detect_static_rules(
            m.Infra.DetectorContext(file_path=file_path, rope_project=rope_project),
            config.Infra.enforcement.rules,
        )
        return {v.kind for v in violations}

    def test_detects_typing_list_import(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Detect a deprecated ``typing.List`` member import."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\n"
            "from typing import List\n"
            "x: List[int] = []\n",
            encoding="utf-8",
        )
        tm.that(self._kinds(sample, rope_project), has="typing_list_import")

    def test_detects_typing_list_attr(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Detect a deprecated ``typing.List`` attribute reference."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\n"
            "import typing\n"
            "x: typing.List[int] = []\n",
            encoding="utf-8",
        )
        tm.that(self._kinds(sample, rope_project), has="typing_list_attr")

    def test_detects_direct_pydantic_import(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Detect a direct Pydantic import outside its owning project."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nfrom pydantic import BaseModel\n",
            encoding="utf-8",
        )
        tm.that(self._kinds(sample, rope_project), has="direct_pydantic_import")

    def test_detects_direct_structlog_import(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Detect a direct Structlog import outside its owning project."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\n"
            "import structlog\n"
            "logger = structlog.get_logger()\n",
            encoding="utf-8",
        )
        tm.that(self._kinds(sample, rope_project), has="direct_structlog_import")

    def test_detects_direct_oracledb_import(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Detect a direct Oracle DB import outside its owning project."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nimport oracledb\n", encoding="utf-8"
        )
        tm.that(self._kinds(sample, rope_project), has="direct_oracledb_import")

    def test_detects_direct_ldap3_import(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Detect a direct LDAP import outside its owning project."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nfrom ldap3 import Server\n",
            encoding="utf-8",
        )
        tm.that(self._kinds(sample, rope_project), has="direct_ldap3_import")

    def test_exempts_owned_library_in_owning_project(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Exempt a governed dependency inside its declared owning project."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nfrom pydantic import BaseModel\n",
            encoding="utf-8",
        )
        violations = u.Infra.detect_static_rules(
            m.Infra.DetectorContext(
                file_path=sample, rope_project=rope_project, project_name="flext-core"
            ),
            config.Infra.enforcement.rules,
        )
        tm.that(any(v.kind == "direct_pydantic_import" for v in violations), eq=False)

    def test_detects_owned_library_in_consumer_project(
        self, tmp_path: Path, rope_project: t.Infra.RopeProject
    ) -> None:
        """Reject a governed dependency inside a non-owning consumer project."""
        sample = tmp_path / "sample.py"
        sample.write_text(
            "from __future__ import annotations\nfrom pydantic import BaseModel\n",
            encoding="utf-8",
        )
        violations = u.Infra.detect_static_rules(
            m.Infra.DetectorContext(
                file_path=sample,
                rope_project=rope_project,
                project_name="flext-target-ldap",
            ),
            config.Infra.enforcement.rules,
        )
        tm.that(any(v.kind == "direct_pydantic_import" for v in violations), eq=True)
