"""Base mixin for rope-powered namespace detectors.

Provides scan_file() template method + shared rope_project/parse_failures storage.
Subclasses declare _rule_id, _build_message, _collect_violations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel

from flext_infra import m, t, u


class FlextInfraScanFileMixin:
    """Base mixin: stores rope_project + parse_failures, provides scan_file().

    Subclasses MUST define ``_rule_id`` and ``detect_file`` classmethod.

    Boilerplate elimination hooks:

    * **_MESSAGE_TEMPLATE** — if set, ``_build_message`` formats the template with
      ``violation.model_dump()`` so subclasses can skip overriding it entirely.
    * **_collect_violations** — default delegates to ``cls.detect_file(file_path=...,
      rope_project=self._rope, parse_failures=self._pf)`` which covers the majority
      of detectors.  Override only when ``detect_file`` needs extra parameters.
    """

    _rule_id: ClassVar[str]
    _MESSAGE_TEMPLATE: ClassVar[str] = ""

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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_source_or_empty(
        rope_project: t.Infra.RopeProject, file_path: Path
    ) -> str | None:
        """Read source text via rope, returning *None* when the resource is missing."""
        res = u.Infra.get_resource_from_path(rope_project, file_path)
        if res is None:
            return None
        source: str = res.read()
        return source

    # ------------------------------------------------------------------
    # Template hooks
    # ------------------------------------------------------------------

    def _build_message(self, violation: BaseModel) -> str:
        """Format a single violation into a human-readable message.

        If ``_MESSAGE_TEMPLATE`` is set, uses ``str.format(**violation.model_dump())``.
        Subclasses with non-trivial formatting should override this method.
        """
        if self._MESSAGE_TEMPLATE:
            return self._MESSAGE_TEMPLATE.format(**violation.model_dump())
        return f"[{self._rule_id}] violation"

    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect violations for the given file.

        Default: delegates to ``cls.detect_file(file_path=..., rope_project=...,
        parse_failures=...)``.  Override when ``detect_file`` requires extra params.
        """
        return self.detect_file(  # type: ignore[attr-defined]  # duck-typed: subclasses define detect_file
            file_path=file_path,
            rope_project=self._rope,
            parse_failures=self._pf,
        )

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
