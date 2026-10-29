"""Typed input fixtures for public pytest diagnostic contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from flext_cli import m, t


class TestsFlextInfraModelsBase:
    """Test-owned input records composed into the generated model facade."""

    class AstGrepFixtureSnapshots(m.Value):
        """Native snapshot identity and its complete per-source metadata."""

        id: str = m.Field(description="Native rule identity")
        snapshots: Mapping[str, t.JsonMapping] = m.Field(
            description="Source cases and their native snapshot metadata",
        )

    class PytestDiagOptions(m.Value):
        """Immutable output destinations and native report-event inputs."""

        failed: Path | None = m.Field(default=None, description="Failed cases output")
        errors: Path | None = m.Field(default=None, description="Error traces output")
        warnings: Path | None = m.Field(default=None, description="Warnings output")
        slowest: Path | None = m.Field(default=None, description="Slowest cases output")
        skips: Path | None = m.Field(default=None, description="Skipped cases output")
        events: str = m.Field(
            default=(
                '{"$report_type":"SessionStart"}\n'
                '{"$report_type":"SessionFinish","exitstatus":0}\n'
            ),
            description="Native pytest report-log event stream",
        )
        identities: str = m.Field(
            default="",
            description="Native warning identities sidecar",
        )


__all__: list[str] = ["TestsFlextInfraModelsBase"]
