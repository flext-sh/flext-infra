"""Utilities for loading and parsing Python modules in detectors.

This module provides tools for reading Python source files, parsing them into ASTs,
and building standardized scan results from violation data.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import JsonValue

from flext_infra import c, m, u


class FlextInfraRefactorDetectorModuleLoader:
    """Loader for parsing Python modules and handling parse failures."""

    @staticmethod
    def load_python_module(
        file_path: Path,
        *,
        stage: str,
        parse_failures: list[m.Infra.ParseFailureViolation] | None,
    ) -> m.Infra.ParsedPythonModule | None:
        """Load and parse a Python module from a file.

        Args:
            file_path: Path to the Python file to load.
            stage: Processing stage name for error tracking.
            parse_failures: Optional list to accumulate parse failure violations.

        Returns:
            ParsedPythonModule with source and AST, or None if parsing failed.

        """
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except UnicodeDecodeError as exc:
            FlextInfraRefactorDetectorModuleLoader._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        except OSError as exc:
            FlextInfraRefactorDetectorModuleLoader._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        tree = u.Infra.parse_ast_from_source(source)
        if tree is None:
            FlextInfraRefactorDetectorModuleLoader._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type="SyntaxError",
                detail="invalid python source",
            )
            return None
        return m.Infra.ParsedPythonModule(source=source, tree=tree)

    @staticmethod
    def _append_parse_failure(
        *,
        parse_failures: list[m.Infra.ParseFailureViolation] | None,
        file_path: Path,
        stage: str,
        error_type: str,
        detail: str,
    ) -> None:
        """Record a parse failure violation.

        Args:
            parse_failures: Optional list to accumulate violations.
            file_path: Path to the file that failed to parse.
            stage: Processing stage where the failure occurred.
            error_type: Type of error encountered.
            detail: Detailed error message.

        """
        if parse_failures is None:
            return
        parse_failures.append(
            m.Infra.ParseFailureViolation.create(
                file=str(file_path),
                stage=stage,
                error_type=error_type,
                detail=detail,
            ),
        )


class ViolationWithLine(Protocol):
    """Protocol for violations that have a line number."""

    def model_dump(self) -> dict[str, JsonValue]:
        """Dump violation data to a dictionary."""
        ...


_V = TypeVar("_V", bound=ViolationWithLine)


class DetectorScanResultBuilder:
    """Builder for constructing standardized detector scan results."""

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
    def build(
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
                    line=DetectorScanResultBuilder._coerce_violation_line(
                        violation.model_dump().get("line")
                    ),
                    message=message_builder(violation),
                    severity="error",
                    rule_id=rule_id,
                )
                for violation in violations
            ],
            detector_name=detector_name,
        )


__all__ = ["DetectorScanResultBuilder", "FlextInfraRefactorDetectorModuleLoader"]
