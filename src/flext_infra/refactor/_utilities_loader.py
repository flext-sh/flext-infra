"""Detector scan result builder utilities for the refactor layer.

Centralizes the ``DetectorScanResultBuilder`` logic previously nested inside
``flext_infra.detectors.module_loader``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from pathlib import Path
from typing import TypeVar

from pydantic import JsonValue

from flext_infra import FlextInfraUtilitiesParsing, c, m, p

_V = TypeVar("_V", bound=p.Infra.ViolationWithLine)


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
        if isinstance(value, (int, float)):
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

    @staticmethod
    def load_python_module(
        file_path: Path,
        *,
        stage: str = "scan",
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> m.Infra.ParsedPythonModule | None:
        """Load and parse a Python module while recording parse failures."""
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except UnicodeDecodeError as exc:
            if parse_failures is not None:
                parse_failures.append(
                    m.Infra.ParseFailureViolation(
                        file=str(file_path),
                        stage=stage,
                        error_type=type(exc).__name__,
                        detail=str(exc),
                    ),
                )
            return None
        except OSError as exc:
            if parse_failures is not None:
                parse_failures.append(
                    m.Infra.ParseFailureViolation(
                        file=str(file_path),
                        stage=stage,
                        error_type=type(exc).__name__,
                        detail=str(exc),
                    ),
                )
            return None
        tree = FlextInfraUtilitiesParsing.parse_ast_from_source(source)
        if tree is None:
            if parse_failures is not None:
                parse_failures.append(
                    m.Infra.ParseFailureViolation(
                        file=str(file_path),
                        stage=stage,
                        error_type="SyntaxError",
                        detail="invalid python source",
                    ),
                )
            return None
        return m.Infra.ParsedPythonModule(source=source, tree=tree)


__all__ = ["FlextInfraUtilitiesRefactorLoader"]
