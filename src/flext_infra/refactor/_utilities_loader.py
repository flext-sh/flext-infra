"""Detector scan result builder utilities for the refactor layer.

Centralizes the ``DetectorScanResultBuilder`` logic previously nested inside
``flext_infra.refactor._detectors.module_loader``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import JsonValue

from flext_infra import m


class _ViolationWithLine(Protocol):
    """Protocol for violations that have a line number."""

    def model_dump(self) -> dict[str, JsonValue]:
        """Dump violation data to a dictionary."""
        ...


_V = TypeVar("_V", bound=_ViolationWithLine)


class FlextInfraUtilitiesRefactorLoader:
    """Scan result builder utilities for detectors.

    Usage via namespace::

        from flext_infra import u

        result = u.Infra.build_scan_result(
            file_path=path,
            detector_name="MyDetector",
            rule_id="namespace.my_rule",
            violations=violations,
            message_builder=lambda v: str(v),
        )
    """

    @staticmethod
    def _coerce_violation_line(value: JsonValue | None) -> int:
        """Convert a JSON value to an integer line number.

        Args:
            value: The value to convert to a line number.

        Returns:
            Integer line number, or 0 if conversion fails.

        """
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 0
        return 0

    @staticmethod
    def build_scan_result(
        *,
        file_path: Path,
        detector_name: str,
        rule_id: str,
        violations: Sequence[_V],
        message_builder: Callable[[_V], str],
    ) -> m.Infra.ScanResult:
        """Build a standardized scan result from typed violations.

        Args:
            file_path: Path to the scanned file.
            detector_name: Name of the detector that found the violations.
            rule_id: Identifier for the violation rule.
            violations: Sequence of violations to include.
            message_builder: Function to convert violations to message strings.

        Returns:
            ScanResult with standardized violation format.

        """
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=FlextInfraUtilitiesRefactorLoader._coerce_violation_line(
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


__all__ = ["FlextInfraUtilitiesRefactorLoader"]
