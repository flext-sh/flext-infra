"""Detect Pydantic model classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Sequence,
)

from flext_infra import c, m, u


class FlextInfraClassPlacementDetector:
    """Detect Pydantic models outside canonical model files via rope."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> Sequence[m.Infra.ClassPlacementViolation]:
        """Detect misplaced Pydantic model classes."""
        if (
            ctx.file_path.name in c.Infra.PLACEMENT_CANONICAL_MODEL_FILES
            or "models" in ctx.file_path.parts
        ):
            return []
        res = u.Infra.fetch_python_resource(
            ctx.rope_project,
            ctx.file_path,
            skip_protected=True,
            skip_settings=True,
        )
        if res is None:
            return []
        file_path = ctx.file_path
        rope_project = ctx.rope_project
        violations: list[m.Infra.ClassPlacementViolation] = []
        for ci in u.Infra.get_class_info(rope_project, res):
            if ci.name.startswith("_"):
                continue
            base_class = next(
                (
                    base_name.rsplit(".", maxsplit=1)[-1]
                    for base_name in ci.bases
                    if base_name.rsplit(".", maxsplit=1)[-1]
                    in c.Infra.PLACEMENT_PYDANTIC_BASE_NAMES
                ),
                None,
            )
            if base_class is None:
                continue
            violations.append(
                m.Infra.ClassPlacementViolation(
                    file=str(file_path),
                    line=ci.line,
                    name=ci.name,
                    base_class=base_class,
                    suggestion="Move class to models.py/models.py or models/",
                ),
            )
        return violations


__all__: list[str] = ["FlextInfraClassPlacementDetector"]
