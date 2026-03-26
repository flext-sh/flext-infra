"""Detect Pydantic model classes outside canonical locations via rope.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import FlextInfraScanFileMixin, c, m, p, t, u

PYDANTIC_BASE_NAMES: frozenset[str] = frozenset({
    "BaseModel",
    "FrozenModel",
    "ArbitraryTypesModel",
    "FrozenStrictModel",
    "FrozenValueModel",
    "TimestampedModel",
})
CANONICAL_MODEL_FILES: frozenset[str] = frozenset({"models.py", "_models.py"})


class FlextInfraClassPlacementDetector(FlextInfraScanFileMixin, p.Infra.Scanner):
    """Detect Pydantic models outside canonical model files via rope."""

    _rule_id: ClassVar[str] = "namespace.class_placement"

    @override
    def _build_message(self, violation: BaseModel) -> str:
        d = violation.model_dump()
        return f"Model class '{d['name']}' must be in canonical model files ({d['suggestion']})"

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        return self.detect_file(
            file_path=file_path, rope_project=self._rope, parse_failures=self._pf
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.ClassPlacementViolation]:
        """Detect misplaced Pydantic model classes."""
        del parse_failures
        if (
            file_path.name in CANONICAL_MODEL_FILES
            or "_models" in file_path.parts
            or file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES
            or file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES
        ):
            return []
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return []
        return [
            m.Infra.ClassPlacementViolation.create(
                file=str(file_path),
                line=ci.line,
                name=ci.name,
                base_class=next(b for b in ci.bases if b in PYDANTIC_BASE_NAMES),
                suggestion="Move class to models.py/_models.py or _models/",
            )
            for ci in u.Infra.get_class_info(rope_project, res)
            if not ci.name.startswith("_")
            and any(b in PYDANTIC_BASE_NAMES for b in ci.bases)
        ]


__all__ = ["FlextInfraClassPlacementDetector"]
