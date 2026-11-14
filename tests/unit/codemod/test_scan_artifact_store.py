"""Content-addressed native artifacts reach the scan report once per path.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra.codemod import FlextInfraModGateEngine
from tests import tm, u


class TestsFlextInfraScanArtifactStore:
    """Identical scanner bytes from two projects share one stored artifact."""

    @staticmethod
    def test_identical_project_outputs_report_one_artifact(tmp_path: Path) -> None:
        """Test identical project outputs report one artifact."""
        root = u.Tests.git_repository(tmp_path)
        published = []
        for project in ("alpha", "beta"):
            staged = tmp_path / f"{project}.jsonl"
            staged.write_bytes(b"")
            published.append(u.Infra.publish_mod_native_artifact(root, staged))
        tm.that(published[0].path, eq=published[1].path)
        report = FlextInfraModGateEngine.recounted(
            (), native_artifacts=tuple(published)
        )
        tm.that(report.native_artifacts, eq=(published[0],))
