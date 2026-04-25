"""Detect Protocol classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)

from flext_infra import c, m, u


class FlextInfraManualProtocolDetector:
    """Detect Protocol classes outside canonical protocol files via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.ManualProtocolViolation]:
        """Detect Protocol classes outside canonical locations."""
        if (
            ctx.file_path.name in c.Infra.MRO_PROTOCOLS_FILE_NAMES
            or c.Infra.MRO_PROTOCOLS_DIRECTORY in ctx.file_path.parts
        ):
            return []
        res = u.Infra.fetch_python_resource(
            ctx.rope_project, ctx.file_path, skip_protected=True
        )
        if res is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        return [
            m.Infra.ManualProtocolViolation(
                file=str(file_path), line=ci.line, name=ci.name
            )
            for ci in u.Infra.get_class_info(rope_project, res)
            if "Protocol" in ci.bases
        ]


__all__: list[str] = ["FlextInfraManualProtocolDetector"]
