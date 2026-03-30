"""Detect Protocol classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, override

from flext_infra import FlextInfraScanFileMixin, c, m, p, u
from flext_infra.detectors._base_detector import _DetectorContext


class FlextInfraManualProtocolDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect Protocol classes outside canonical protocol files via rope."""

    _rule_id: ClassVar[str] = "namespace.manual_protocol"
    _MESSAGE_TEMPLATE: ClassVar[str] = (
        "Protocol class '{name}' must be centralized ({suggestion})"
    )

    @classmethod
    @override
    def detect_file(
        cls,
        ctx: _DetectorContext,
    ) -> Sequence[m.Infra.ManualProtocolViolation]:
        """Detect Protocol classes outside canonical locations."""
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        if (
            file_path.name in c.Infra.MRO_PROTOCOLS_FILE_NAMES
            or c.Infra.MRO_PROTOCOLS_DIRECTORY in file_path.parts
            or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        return [
            m.Infra.ManualProtocolViolation(
                file=str(file_path), line=ci.line, name=ci.name
            )
            for ci in u.Infra.get_class_info(rope_project, res)
            if "Protocol" in ci.bases
        ]


__all__ = ["FlextInfraManualProtocolDetector"]
