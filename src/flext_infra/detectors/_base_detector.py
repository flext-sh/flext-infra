"""Base mixin providing the scan_file() template method for namespace detectors.

All concrete detectors share the same scan_file() body: collect violations via
scan_file_impl, then format them with build_scan_result. This mixin captures that
shared logic via a template method pattern so subclasses only need to declare:

- ``_rule_id: ClassVar[str]`` — the rule identifier string
- ``_build_message(violation) -> str`` — formats one violation into a message
- ``_collect_violations(file_path) -> Sequence[...]`` — calls scan_file_impl
  with the correct signature (and any extra instance args like project_name)

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import m, u


class FlextInfraScanFileMixin:
    """Mixin that provides the concrete scan_file() via template method pattern.

    Subclasses must:
    1. Declare ``_rule_id: ClassVar[str]`` — the rule ID for ScanViolation
    2. Implement ``_build_message(violation) -> str`` — formats the message
    3. Implement ``_collect_violations(file_path) -> Sequence[BaseModel]`` —
       collects violations by calling scan_file_impl with the correct arguments

    Subclasses manage their own ``__init__`` and ``_parse_failures`` attribute
    with the precise concrete type required by their scan_file_impl signature.
    The mixin does not store parse_failures to avoid type widening.

    The mixin's scan_file() calls _collect_violations and _build_message,
    then delegates formatting to u.Infra.build_scan_result.
    """

    _rule_id: ClassVar[str]

    @abstractmethod
    def _build_message(self, violation: BaseModel) -> str:
        """Format a single violation into a human-readable message.

        Args:
            violation: The Pydantic violation model to format.

        Returns:
            Human-readable message string describing the violation.

        """

    @abstractmethod
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect violations for the given file.

        Implementations call scan_file_impl with the appropriate arguments,
        including any extra instance-level parameters (e.g. project_name).

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of Pydantic violation models found in the file.

        """

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return a standardized ScanResult.

        Uses _collect_violations() and _build_message() as template hooks,
        then delegates formatting to u.Infra.build_scan_result.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            ScanResult containing detected violations.

        """
        violations = self._collect_violations(file_path)
        return u.Infra.build_scan_result(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id=self._rule_id,
            violations=violations,
            message_builder=self._build_message,
        )


__all__ = ["FlextInfraScanFileMixin"]
