"""Base mixin for rope-powered namespace detectors.

Provides scan_file() template method + shared rope_project/parse_failures storage.
Subclasses declare _rule_id, _build_message, _collect_violations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from flext_infra import m, t, u


class FlextInfraScanFileMixin:
    """Base mixin: stores rope_project + parse_failures, provides scan_file()."""

    _rule_id: ClassVar[str]

    def __init__(
        self,
        *,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize with mandatory rope project and optional parse failure tracker."""
        super().__init__()
        self._rope = rope_project
        self._pf = parse_failures

    @abstractmethod
    def _build_message(self, violation: BaseModel) -> str:
        """Format a single violation into a human-readable message."""

    @abstractmethod
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect violations for the given file."""

    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return a standardized ScanResult."""
        violations = self._collect_violations(file_path)
        return u.Infra.build_scan_result(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id=self._rule_id,
            violations=violations,
            message_builder=self._build_message,
        )


__all__ = ["FlextInfraScanFileMixin"]
