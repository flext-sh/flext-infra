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

from flext_infra import FlextInfraUtilitiesRope, c, m, p, u

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
                    line=u.to_int(violation.model_dump().get("line")),
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

        try:
            rope_proj = FlextInfraUtilitiesRope.init_rope_project(file_path.parent)
            try:
                resource = FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_proj,
                    file_path,
                )
                if resource is not None:
                    pycore = FlextInfraUtilitiesRope.get_pycore(rope_proj)
                    tree = pycore.resource_to_pyobject(resource)
                else:
                    tree = None
            finally:
                rope_proj.close()
        except Exception:
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
