"""Verify dependency provenance through the native installed environment.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from flext_infra.workspace import FlextInfraRuntimeDependencyCollector
from tests import c, m, tm, u


class TestsFlextInfraRuntimeDependencyCollector:
    """Installed vendor metadata must not compete with its owning distribution."""

    @staticmethod
    def test_collect_native_dependency_suppliers(tmp_path: Path) -> None:
        """The public collector accepts the current real wheel inventories."""
        root = tm.ok(
            u.Infra.git_repository_root(
                m.Infra.GitRepoRequest(repo_root=Path(__file__).parent),
            ),
        ).repository_root
        scan = tm.ok(
            u.Infra.capture_deptry_scan(
                root,
                Path(sys.executable).parent,
                config_path=root / c.PYPROJECT_FILENAME,
                json_output_path=tmp_path / "deptry.json",
            ),
        )
        tm.ok(
            FlextInfraRuntimeDependencyCollector(
                python=Path(sys.executable),
                development_only=(),
            )(root, scan),
        )
