"""Base utilities for flext-infra project.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TypeVar

from pydantic import JsonValue

from flext_infra import m, p, t

_V = TypeVar("_V", bound=p.Infra.ViolationWithLine)


class FlextInfraUtilitiesBase:
    """Base utilities for flext-infra project.

    Provides primitive helpers used across all infra utility subclasses.
    """

    @staticmethod
    def get_str_key(
        mapping: Mapping[str, t.Infra.InfraValue],
        key: str,
        *,
        default: str = "",
        lower: bool = False,
    ) -> str:
        """Extract and normalize a string key from a config mapping.

        Replaces the repeated ``str(mapping.get(key, "")).strip().lower()`` pattern.

        Args:
            mapping: Source mapping (e.g., rule config dict).
            key: Key to extract.
            default: Default value if key is missing.
            lower: If True, also lowercase the result.

        Returns:
            Stripped (and optionally lowercased) string value.

        """
        raw = str(mapping.get(key, default)).strip()
        return raw.lower() if lower else raw

    @staticmethod
    def _coerce_violation_line(value: JsonValue | None) -> int:
        """Convert a JSON scalar into a scan-result line number."""
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    @classmethod
    def build_scan_result(
        cls,
        *,
        file_path: Path,
        detector_name: str,
        rule_id: str,
        violations: Sequence[_V],
        message_builder: Callable[[_V], str],
    ) -> m.Infra.ScanResult:
        """Build a standardized scan result from typed violations."""
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=cls._coerce_violation_line(
                        violation.model_dump().get("line"),
                    ),
                    message=message_builder(violation),
                    severity="error",
                    rule_id=rule_id,
                )
                for violation in violations
            ],
            detector_name=detector_name,
        )
